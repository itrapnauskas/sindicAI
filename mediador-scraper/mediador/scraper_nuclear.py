#!/usr/bin/env python3
"""
Scraper Nuclear - Coleta MASSIVA do Sistema Mediador

Estratégia "Full Burst":
- Loop cartesiano: 27 UFs × 3 tipos × N páginas
- Paralelismo controlado: 8 workers simultâneos
- Rate limiting ético: 8 req/s agregado
- Retry automático com backoff exponencial
- Checksum SHA-256 para integridade

Estimativa: ~800k PDFs, ~300 GB, 24-48h de execução
"""

import os
import json
import hashlib
import time
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from bs4 import BeautifulSoup

from .config import (
    UFS, TIPOS, BASE_URL, DATA_ROOT, MAX_WORKERS,
    RATE_LIMIT, DATA_INICIO, MAX_RETRIES, RETRY_BACKOFF,
    TIMEOUT, USER_AGENT
)

# Desabilitar warnings de SSL (o servidor do MTE pode ter cert problemático)
urllib3.disable_warnings()

# Session global para reusar conexões
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def human_time() -> str:
    """Retorna timestamp legível HH:MM:SS"""
    return dt.datetime.now().strftime("%H:%M:%S")


def sha256(data: bytes) -> str:
    """Calcula hash SHA-256 de bytes"""
    return hashlib.sha256(data).hexdigest()


def ensure_dir(path: Path) -> None:
    """Cria diretório se não existir"""
    path.mkdir(parents=True, exist_ok=True)


def scrape_lista(uf: str, tipo: str, pagina: int) -> str:
    """
    Faz request para página de listagem do Mediador.

    Args:
        uf: Sigla da UF (ex: "SP")
        tipo: Código do tipo ("1", "2", "3")
        pagina: Número da página (1-indexed)

    Returns:
        HTML da página de resultados
    """
    params = {
        "uf": uf,
        "tpInstrumento": tipo,
        "pagina": pagina,
        "dtRegistroIni": DATA_INICIO,
        "dtRegistroFim": dt.date.today().strftime("%d/%m/%Y")
    }

    t0 = time.time()

    # Retry com backoff exponencial
    for tentativa in range(MAX_RETRIES):
        try:
            r = session.get(BASE_URL, params=params, verify=False, timeout=TIMEOUT)
            r.raise_for_status()

            # Rate limiting: garantir pelo menos RATE_LIMIT segundos entre requests
            elapsed = time.time() - t0
            sleep_time = max(0, RATE_LIMIT - elapsed)
            time.sleep(sleep_time)

            return r.text

        except Exception as e:
            if tentativa < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF[tentativa]
                print(f"[{human_time()}] ⚠️  Erro em {uf}-{tipo} pág {pagina}: {e}. Retry em {wait}s...")
                time.sleep(wait)
            else:
                raise


def parse_lista(html: str, tipo_codigo: str) -> list[dict]:
    """
    Parseia HTML da página de listagem e extrai instrumentos.

    Args:
        html: HTML da página
        tipo_codigo: Código do tipo ("1", "2", "3")

    Returns:
        Lista de dicts com metadados de cada instrumento
    """
    soup = BeautifulSoup(html, "lxml")

    # Encontrar tabela de resultados (ajustar seletor se necessário)
    table = soup.find("table", {"class": "table-striped"})
    if not table:
        # Tentar seletor alternativo
        table = soup.find("table")

    if not table:
        return []

    rows = table.find_all("tr")[1:]  # Pular header
    instrumentos = []

    for tr in rows:
        cols = tr.find_all("td")
        if len(cols) < 7:
            continue

        # Extrair link (primeira coluna geralmente tem um <a>)
        a_tag = cols[0].find("a")
        link_pdf = a_tag.get("href") if a_tag else None

        # Construir dict com metadados
        instrumento = {
            "id_mediador": cols[0].get_text(strip=True),
            "tipo": TIPOS.get(tipo_codigo, "DESCONHECIDO"),
            "data_registro": cols[2].get_text(strip=True) if len(cols) > 2 else "",
            "data_assinatura": cols[3].get_text(strip=True) if len(cols) > 3 else "",
            "vigencia_inicio": cols[4].get_text(strip=True) if len(cols) > 4 else "",
            "vigencia_fim": cols[5].get_text(strip=True) if len(cols) > 5 else "",
            "partes": cols[6].get_text(strip=True) if len(cols) > 6 else "",
            "link_pdf": link_pdf
        }

        instrumentos.append(instrumento)

    return instrumentos


def baixa_pdf(url: str) -> tuple[bytes | None, str | None]:
    """
    Baixa PDF do instrumento.

    Args:
        url: URL do PDF

    Returns:
        Tupla (conteudo_bytes, hash_sha256) ou (None, None) em caso de erro
    """
    if not url:
        return None, None

    try:
        # Se URL for relativa, completar com domínio
        if url.startswith("/"):
            url = "https://www3.mte.gov.br" + url

        r = session.get(url, verify=False, timeout=TIMEOUT)
        r.raise_for_status()

        conteudo = r.content
        hash_value = sha256(conteudo)

        return conteudo, hash_value

    except Exception as e:
        print(f"[{human_time()}] ⚠️  Erro ao baixar PDF {url}: {e}")
        return None, None


def salva_instrumento(uf: str, meta: dict, html_bin: bytes, pdf_bin: bytes | None, pdf_hash: str | None) -> None:
    """
    Salva instrumento em disco com estrutura organizada.

    Estrutura:
        data/raw/mediador/{UF}/{ANO}/{TIPO}/{ID_MEDIADOR}/
          ├── metadata.json
          ├── instrumento.html
          ├── instrumento.pdf
          └── instrumento.sha256
    """
    ano = meta.get("ano", "0000")
    tipo = meta.get("tipo", "DESCONHECIDO")
    id_mediador = meta["id_mediador"].replace("/", "_")  # Substituir / em nome de diretório

    pasta = DATA_ROOT / uf / ano / tipo / id_mediador
    ensure_dir(pasta)

    # Salvar metadata.json
    (pasta / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Salvar HTML
    (pasta / "instrumento.html").write_bytes(html_bin)

    # Salvar PDF e hash (se disponível)
    if pdf_bin:
        (pasta / "instrumento.pdf").write_bytes(pdf_bin)
        if pdf_hash:
            (pasta / "instrumento.sha256").write_text(pdf_hash)


def worker(uf: str, tipo_codigo: str) -> None:
    """
    Worker que processa uma combinação UF + tipo.

    Para cada combinação:
    1. Percorre todas as páginas de resultados
    2. Para cada instrumento: baixa HTML + PDF
    3. Salva em disco com estrutura organizada

    Args:
        uf: Sigla da UF
        tipo_codigo: Código do tipo ("1", "2", "3")
    """
    tipo_nome = TIPOS[tipo_codigo]
    print(f"[{human_time()}] 🚀 {uf}-{tipo_nome} iniciado")

    pagina = 1
    total_instrumentos = 0

    while True:
        try:
            # Buscar página de listagem
            html = scrape_lista(uf, tipo_codigo, pagina)
            instrumentos = parse_lista(html, tipo_codigo)

            # Se não encontrou resultados, fim da paginação
            if not instrumentos:
                print(f"[{human_time()}] 🏁 {uf}-{tipo_nome} finalizado ({total_instrumentos} instrumentos)")
                break

            # Processar cada instrumento
            for item in instrumentos:
                # Enriquecer metadados
                meta = {
                    **item,
                    "uf": uf,
                    "ano": item["data_registro"][-4:] if item["data_registro"] else "0000",
                    "fonte": "MEDIADOR",
                    "coletado_em": dt.datetime.now().isoformat()
                }

                # Baixar PDF
                pdf_bytes, pdf_hash = baixa_pdf(item["link_pdf"])

                # Salvar tudo
                salva_instrumento(uf, meta, html.encode("utf-8"), pdf_bytes, pdf_hash)

                total_instrumentos += 1

            print(f"[{human_time()}] ✅ {uf}-{tipo_nome} página {pagina} -> {len(instrumentos)} docs (total: {total_instrumentos})")
            pagina += 1

        except Exception as e:
            print(f"[{human_time()}] ❌ {uf}-{tipo_nome} página {pagina} -> ERRO: {e}")
            # Continuar para próxima página mesmo com erro
            pagina += 1
            time.sleep(5)


def main():
    """
    Função principal: executa coleta massiva com paralelismo controlado.
    """
    print(f"[{human_time()}] 🔥 INICIANDO COLETA NUCLEAR")
    print(f"[{human_time()}] 📊 Configuração:")
    print(f"           - {len(UFS)} UFs × {len(TIPOS)} tipos = {len(UFS) * len(TIPOS)} combinações")
    print(f"           - {MAX_WORKERS} workers paralelos")
    print(f"           - Rate limit: {RATE_LIMIT}s por request")
    print(f"           - Dados salvos em: {DATA_ROOT}")
    print()

    # Criar diretório raiz
    ensure_dir(DATA_ROOT)

    # Executar workers em paralelo
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submeter todas as combinações UF × tipo
        futuros = [
            executor.submit(worker, uf, tipo_codigo)
            for uf in UFS
            for tipo_codigo in TIPOS.keys()
        ]

        # Aguardar conclusão
        for futuro in as_completed(futuros):
            try:
                futuro.result()
            except Exception as e:
                print(f"[{human_time()}] 💥 Worker crashou: {e}")

    print()
    print(f"[{human_time()}] 🎉 COLETA NUCLEAR FINALIZADA!")
    print(f"[{human_time()}] 📁 Dados salvos em: {DATA_ROOT}")


if __name__ == "__main__":
    main()
