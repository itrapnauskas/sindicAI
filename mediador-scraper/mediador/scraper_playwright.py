#!/usr/bin/env python3
"""
Scraper com Playwright - Versão que usa browser real

O site do Mediador tem proteção anti-bot, então precisamos usar
um browser real (Chromium via Playwright) ao invés de requests direto.
"""

import os
import json
import hashlib
import time
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

from .config import (
    UFS, TIPOS, BASE_URL, DATA_ROOT,
    MAX_WORKERS, RATE_LIMIT, DATA_INICIO,
    MAX_RETRIES, RETRY_BACKOFF, TIMEOUT, HEADLESS
)


def human_time() -> str:
    """Retorna timestamp legível HH:MM:SS"""
    return dt.datetime.now().strftime("%H:%M:%S")


def sha256(data: bytes) -> str:
    """Calcula hash SHA-256 de bytes"""
    return hashlib.sha256(data).hexdigest()


def ensure_dir(path: Path) -> None:
    """Cria diretório se não existir"""
    path.mkdir(parents=True, exist_ok=True)


def parse_lista(html: str, tipo_codigo: str) -> list[dict]:
    """
    Parseia HTML da página de listagem e extrai instrumentos.
    """
    soup = BeautifulSoup(html, "lxml")

    # Encontrar tabela de resultados - tentar vários seletores
    table = (
        soup.find("table", {"class": "table-striped"}) or
        soup.find("table", {"class": "table"}) or
        soup.find("table")
    )

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

        # Se link for relativo, completar
        if link_pdf and link_pdf.startswith("/"):
            link_pdf = "https://www3.mte.gov.br" + link_pdf

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


def salva_instrumento(uf: str, meta: dict, html_bin: bytes, pdf_bin: bytes | None, pdf_hash: str | None) -> None:
    """Salva instrumento em disco"""
    ano = meta.get("ano", "0000")
    tipo = meta.get("tipo", "DESCONHECIDO")
    id_mediador = meta["id_mediador"].replace("/", "_").replace("\\", "_")

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


def worker_playwright(uf: str, tipo_codigo: str) -> None:
    """
    Worker que usa Playwright para scraping.
    Abre um browser, navega no site, preenche formulário e coleta dados.
    """
    tipo_nome = TIPOS[tipo_codigo]
    print(f"[{human_time()}] 🚀 {uf}-{tipo_nome} iniciado")

    with sync_playwright() as p:
        # Lançar browser
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            # Navegar para página de consulta
            page.goto(BASE_URL, wait_until="networkidle", timeout=TIMEOUT * 1000)
            time.sleep(2)  # Aguardar JS carregar

            # Preencher formulário
            # NOTA: Seletores precisam ser ajustados conforme HTML real do site
            # Aqui estamos usando seletores genéricos que provavelmente precisarão de ajuste

            try:
                # Selecionar UF
                page.select_option("select[name*='uf'], select[id*='uf'], select[id*='UF']", uf)
            except Exception as e:
                print(f"[{human_time()}] ⚠️  Erro ao selecionar UF: {e}")

            try:
                # Selecionar tipo de instrumento
                page.select_option(
                    "select[name*='tipo'], select[name*='Tipo'], select[id*='tipo']",
                    tipo_codigo
                )
            except Exception as e:
                print(f"[{human_time()}] ⚠️  Erro ao selecionar tipo: {e}")

            try:
                # Preencher data inicial
                page.fill("input[name*='dataIni'], input[name*='dtIni'], input[id*='dataIni']", DATA_INICIO)
            except Exception as e:
                print(f"[{human_time()}] ⚠️  Erro ao preencher data inicial: {e}")

            try:
                # Preencher data final
                data_fim = dt.date.today().strftime("%d/%m/%Y")
                page.fill("input[name*='dataFim'], input[name*='dtFim'], input[id*='dataFim']", data_fim)
            except Exception as e:
                print(f"[{human_time()}] ⚠️  Erro ao preencher data final: {e}")

            # Clicar em pesquisar
            try:
                page.click("button:has-text('Pesquisar'), input[type='submit'][value*='Pesquis']")
                page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
                time.sleep(2)
            except Exception as e:
                print(f"[{human_time()}] ⚠️  Erro ao clicar em pesquisar: {e}")
                browser.close()
                return

            pagina = 1
            total_instrumentos = 0

            while True:
                # Capturar HTML da página atual
                html = page.content()
                instrumentos = parse_lista(html, tipo_codigo)

                if not instrumentos:
                    print(f"[{human_time()}] 🏁 {uf}-{tipo_nome} finalizado ({total_instrumentos} instrumentos)")
                    break

                # Processar cada instrumento
                for item in instrumentos:
                    meta = {
                        **item,
                        "uf": uf,
                        "ano": item["data_registro"][-4:] if item["data_registro"] else "0000",
                        "fonte": "MEDIADOR",
                        "coletado_em": dt.datetime.now().isoformat()
                    }

                    # Baixar PDF (se houver link)
                    pdf_bytes, pdf_hash = None, None
                    if item["link_pdf"]:
                        try:
                            # Usar browser para baixar (mais confiável contra anti-bot)
                            pdf_page = context.new_page()
                            response = pdf_page.goto(item["link_pdf"], timeout=TIMEOUT * 1000)
                            if response and response.status == 200:
                                pdf_bytes = response.body()
                                pdf_hash = sha256(pdf_bytes)
                            pdf_page.close()
                        except Exception as e:
                            print(f"[{human_time()}] ⚠️  Erro ao baixar PDF {item['id_mediador']}: {e}")

                    # Salvar tudo
                    salva_instrumento(uf, meta, html.encode("utf-8"), pdf_bytes, pdf_hash)
                    total_instrumentos += 1

                print(f"[{human_time()}] ✅ {uf}-{tipo_nome} página {pagina} -> {len(instrumentos)} docs (total: {total_instrumentos})")

                # Tentar ir para próxima página
                try:
                    # Procurar botão/link de próxima página
                    next_button = page.locator("a:has-text('Próxima'), a:has-text('Próximo'), button:has-text('Próxima')").first
                    if next_button.count() > 0:
                        next_button.click()
                        page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
                        time.sleep(RATE_LIMIT)  # Rate limiting
                        pagina += 1
                    else:
                        break
                except Exception:
                    break

        except Exception as e:
            print(f"[{human_time()}] ❌ {uf}-{tipo_nome} ERRO FATAL: {e}")

        finally:
            browser.close()


def main():
    """Função principal - coleta massiva com Playwright"""
    print(f"[{human_time()}] 🔥 INICIANDO COLETA COM PLAYWRIGHT")
    print(f"[{human_time()}] 📊 Configuração:")
    print(f"           - {len(UFS)} UFs × {len(TIPOS)} tipos = {len(UFS) * len(TIPOS)} combinações")
    print(f"           - Modo headless: {HEADLESS}")
    print(f"           - Dados salvos em: {DATA_ROOT}")
    print()

    ensure_dir(DATA_ROOT)

    # Por enquanto, rodar sequencial (Playwright é mais pesado que requests)
    # Em produção, você pode paralelizar com cuidado
    for uf in UFS:
        for tipo_codigo in TIPOS.keys():
            worker_playwright(uf, tipo_codigo)

    print()
    print(f"[{human_time()}] 🎉 COLETA FINALIZADA!")
    print(f"[{human_time()}] 📁 Dados salvos em: {DATA_ROOT}")


if __name__ == "__main__":
    main()
