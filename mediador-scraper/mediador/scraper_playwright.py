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
    MAX_WORKERS, RATE_LIMIT, ANO_INICIO, ANO_FIM,
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


def parse_lista(html: str, tipo_codigo: str, debug_save=False) -> list[dict]:
    """
    Parseia HTML da página de listagem e extrai instrumentos.

    ESTRUTURA DO SITE:
    <div id="grdInstrumentos">
      <table class="Dados Tb01">
        <tr indice="MR063207/2023">
          <td><div><table class="TbForm">
            <!-- Dados aninhados aqui -->
          </table></div></td>
        </tr>
      </table>
    </div>
    """
    import re
    soup = BeautifulSoup(html, "lxml")

    # Encontrar a div com id="grdInstrumentos"
    grid_div = soup.find("div", {"id": "grdInstrumentos"})
    if not grid_div:
        print(f"[DEBUG] ⚠️  Div grdInstrumentos não encontrada!")
        return []

    # Encontrar a tabela principal class="Dados Tb01"
    main_table = grid_div.find("table", {"class": "Dados Tb01"})
    if not main_table:
        print(f"[DEBUG] ⚠️  Tabela 'Dados Tb01' não encontrada!")
        return []

    # Cada TR com atributo "indice" é um instrumento
    instrument_rows = main_table.find_all("tr", {"indice": True})
    print(f"[DEBUG] 📊 Encontrados {len(instrument_rows)} instrumentos na página")

    instrumentos = []

    for i, tr in enumerate(instrument_rows):
        try:
            # Atributo indice contém o número da solicitação (MR...)
            num_solicitacao = tr.get("indice", "")

            # Dentro do TR, buscar a tabela aninhada TbForm que contém os dados
            nested_table = tr.find("table", {"class": "TbForm"})
            if not nested_table:
                continue

            # Extrair dados das linhas da tabela aninhada
            data = {}
            for row in nested_table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                label = cells[0].get_text(strip=True)

                if "Nº do Registro" in label:
                    # Registro está em tabela aninhada dentro: <table><tr><td>AC000001/2024</td>...
                    inner_table = cells[1].find("table")
                    if inner_table:
                        inner_cells = inner_table.find("tr").find_all("td")
                        data["registro"] = inner_cells[0].get_text(strip=True) if inner_cells else ""
                        data["solicitacao"] = inner_cells[2].get_text(strip=True) if len(inner_cells) > 2 else num_solicitacao

                elif "Tipo do Instrumento" in label:
                    # Tipo e Vigência em tabela aninhada
                    inner_table = cells[1].find("table")
                    if inner_table:
                        inner_cells = inner_table.find("tr").find_all("td")
                        data["tipo"] = inner_cells[0].get_text(strip=True) if inner_cells else ""
                        # Vigência: "01/09/2023 - 31/08/2025"
                        vigencia_text = inner_cells[2].get_text(strip=True) if len(inner_cells) > 2 else ""
                        # Remover "*VIGÊNCIA EXPIRADA" se existir
                        vigencia_text = re.sub(r'\*VIGÊNCIA.*', '', vigencia_text).strip()
                        if " - " in vigencia_text:
                            parts = vigencia_text.split(" - ")
                            data["vigencia_inicio"] = parts[0].strip()
                            data["vigencia_fim"] = parts[1].strip()
                        else:
                            data["vigencia_inicio"] = vigencia_text
                            data["vigencia_fim"] = ""

                elif "Partes" in label:
                    # Partes são separadas por <br>
                    partes_html = cells[1]
                    # Pegar todo o texto e separar por quebras
                    partes_text = partes_html.get_text(separator="|", strip=True)
                    data["partes"] = partes_text.replace("|", " / ")

                # Procurar link de download: onclick="fDownload('MR063207/2023','76535764032770')"
                download_link = row.find("a", {"onclick": lambda x: x and "fDownload" in x})
                if download_link:
                    onclick = download_link.get("onclick", "")
                    # Extrair os parâmetros: fDownload('MR063207/2023','76535764032770')
                    match = re.search(r"fDownload\('([^']+)','([^']+)'\)", onclick)
                    if match:
                        solicitacao_id = match.group(1)
                        cnpj_hash = match.group(2)
                        # Construir URL de download (preciso descobrir o padrão correto)
                        # Por enquanto guardar os IDs
                        data["download_solicitacao"] = solicitacao_id
                        data["download_cnpj_hash"] = cnpj_hash

            # Montar instrumento
            instrumento = {
                "id_mediador": data.get("registro", ""),
                "num_solicitacao": data.get("solicitacao", num_solicitacao),
                "tipo": data.get("tipo", TIPOS.get(tipo_codigo, "DESCONHECIDO")),
                "tipo_simplificado": TIPOS.get(tipo_codigo, "DESCONHECIDO"),
                "data_registro": "",  # Não vi data de registro explícita
                "data_assinatura": "",  # Não vi data de assinatura explícita
                "vigencia_inicio": data.get("vigencia_inicio", ""),
                "vigencia_fim": data.get("vigencia_fim", ""),
                "partes": data.get("partes", ""),
                "link_pdf": None,  # Será construído depois com os IDs de download
                "download_ids": {
                    "solicitacao": data.get("download_solicitacao", ""),
                    "cnpj_hash": data.get("download_cnpj_hash", "")
                }
            }

            if instrumento["id_mediador"]:  # Só adicionar se tiver registro
                instrumentos.append(instrumento)

                # DEBUG: Mostrar primeiros 2
                if i < 2:
                    print(f"[DEBUG] Instrumento {i+1}: {instrumento['id_mediador']} | {instrumento['tipo']} | {instrumento['vigencia_inicio']}")

        except Exception as e:
            print(f"[DEBUG] ⚠️  Erro ao processar instrumento {i+1}: {e}")
            continue

    print(f"[DEBUG] ✅ Total de instrumentos extraídos: {len(instrumentos)}")
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

    IMPORTANTE: Site limita pesquisas a 2 anos!
    Fazemos loop ANO POR ANO para respeitar esse limite.
    """
    tipo_nome = TIPOS[tipo_codigo]
    print(f"[{human_time()}] 🚀 {uf}-{tipo_nome} iniciado")
    print(f"[{human_time()}] 📅 Período: {ANO_INICIO} até {ANO_FIM}")

    total_geral = 0

    # Loop ANO POR ANO para respeitar limite de 2 anos do site
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n[{human_time()}] {'='*60}")
        print(f"[{human_time()}] 📆 Coletando ano {ano} - {uf}-{tipo_nome}")
        print(f"[{human_time()}] {'='*60}")

        with sync_playwright() as p:
            # Lançar browser
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            try:
                # Navegar para página de consulta (site pode estar lento)
                print(f"[{human_time()}] 🌐 Navegando para {BASE_URL}...")
                page.goto(BASE_URL, wait_until="load", timeout=180000)  # 3 minutos
                print(f"[{human_time()}] ✅ Página carregada, aguardando estabilização...")
                page.wait_for_timeout(3000)  # Aguardar JS carregar

                # Preencher formulário com seletores corretos do site Mediador
                # Descobertos via inspect_site.py

                # Mapear tipo_codigo para INDEX no select (mais confiável que label)
                # Índices descobertos via inspect_site.py:
                # 0 = "Todos os Tipos"
                # 1 = "Acordo Coletivo" (ACT)
                # 2 = "Acordo Coletivo Específico - PPE"
                # 3 = "Acordo Coletivo Específico - Domingos"
                # 4 = "Convenção Coletiva" (CCT)
                tipo_index_map = {
                    "1": 4,  # CCT
                    "2": 1,  # ACT
                    "3": 0   # Todos (para pegar aditivos)
                }
                tipo_index = tipo_index_map.get(tipo_codigo, 0)
                tipo_nomes = {
                    "1": "Convenção Coletiva (CCT)",
                    "2": "Acordo Coletivo (ACT)",
                    "3": "Todos os Tipos (Aditivos)"
                }

                try:
                    # Selecionar UF de Registro (id correto: cboUFRegistro)
                    page.select_option("#cboUFRegistro", uf)
                    print(f"[{human_time()}] ✅ UF selecionada: {uf}")
                except Exception as e:
                    print(f"[{human_time()}] ⚠️  Erro ao selecionar UF: {e}")

                try:
                    # Selecionar tipo de instrumento por ÍNDICE (mais confiável)
                    page.select_option("#cboTPRequerimento", index=tipo_index)
                    print(f"[{human_time()}] ✅ Tipo selecionado: {tipo_nomes.get(tipo_codigo, 'Desconhecido')} (index {tipo_index})")
                except Exception as e:
                    print(f"[{human_time()}] ⚠️  Erro ao selecionar tipo: {e}")

                try:
                    # Calcular datas PARA O ANO ATUAL DO LOOP
                    # Site limita a 2 anos, então fazemos 01/01/YYYY até 31/12/YYYY (1 ano por vez)
                    data_inicio = f"01/01/{ano}"
                    data_fim = f"31/12/{ano}"

                    # Marcar checkbox de Período de Registro
                    page.check("#chkPeriodoRegistro")
                    page.wait_for_timeout(300)

                    # Preencher Período de Registro
                    page.fill("#txtDTInicioRegistro", data_inicio)
                    page.fill("#txtDTFimRegistro", data_fim)
                    print(f"[{human_time()}] ✅ Período de Registro: {data_inicio} até {data_fim}")

                    # CAMPO CRÍTICO: Status de Vigência (select obrigatório!)
                    # Opções: "" (vazio/erro), "2" (Todos), "1" (Vigentes), "0" (Não Vigentes)
                    page.select_option("#cboSTVigencia", "2")  # "Todos"
                    print(f"[{human_time()}] ✅ Status de Vigência: Todos")

                    # TAMBÉM marcar e preencher Vigência (site exige!)
                    page.check("#chkVigencia")
                    page.wait_for_timeout(300)

                    # Preencher Período de Vigência
                    page.fill("#txtDTInicioVigencia", data_inicio)
                    page.fill("#txtDTFimVigencia", data_fim)
                    print(f"[{human_time()}] ✅ Período de Vigência: {data_inicio} até {data_fim}")

                except Exception as e:
                    print(f"[{human_time()}] ⚠️  Erro ao preencher datas: {e}")

                # Clicar em pesquisar
                try:
                    page.click("#btnPesquisar")
                    print(f"[{human_time()}] ✅ Botão Pesquisar clicado")
                    page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
                    time.sleep(2)
                except Exception as e:
                    print(f"[{human_time()}] ⚠️  Erro ao clicar em pesquisar: {e}")
                    browser.close()
                    continue  # Próximo ano

                pagina = 1
                total_instrumentos_ano = 0

                while True:
                    # Capturar HTML da página atual
                    html = page.content()
                    current_url = page.url
                    print(f"[DEBUG] 📍 URL atual: {current_url}")

                    # Ativar debug na primeira página para salvar HTML se não encontrar resultados
                    instrumentos = parse_lista(html, tipo_codigo, debug_save=(pagina == 1 and ano == ANO_INICIO))

                    if not instrumentos:
                        if pagina == 1:
                            print(f"[{human_time()}] ℹ️  Nenhum resultado para {uf}-{tipo_nome} em {ano}")
                            # Salvar HTML apenas no primeiro ano para debug
                            if ano == ANO_INICIO:
                                debug_file = DATA_ROOT.parent / f"debug_{uf}_{tipo_nome}_{ano}_empty.html"
                                ensure_dir(DATA_ROOT.parent)
                                debug_file.write_text(html, encoding="utf-8")
                                print(f"[{human_time()}] 💾 HTML de resultado vazio salvo em: {debug_file}")
                        break

                    # Processar cada instrumento
                    for idx_item, item in enumerate(instrumentos):
                        meta = {
                            **item,
                            "uf": uf,
                            "ano": item["data_registro"][-4:] if item["data_registro"] else str(ano),
                            "fonte": "MEDIADOR",
                            "coletado_em": dt.datetime.now().isoformat()
                        }

                        # Baixar PDF clicando no botão de Download
                        pdf_bytes, pdf_hash = None, None

                        # Verificar se temos os IDs de download
                        download_ids = item.get("download_ids", {})
                        solicitacao_id = download_ids.get("solicitacao", "")
                        cnpj_hash = download_ids.get("cnpj_hash", "")

                        if solicitacao_id and cnpj_hash:
                            try:
                                # Procurar o botão de download específico para este instrumento
                                # onclick="fDownload('MR063207/2023','76535764032770')"
                                # IMPORTANTE: Garantir que é o botão fDownload, não o Visualizar!
                                onclick_pattern = f"fDownload('{solicitacao_id}','{cnpj_hash}')"
                                download_button = page.locator(f"a[onclick*=\"fDownload\"][onclick*=\"{solicitacao_id}\"]").first

                                if download_button.count() > 0:
                                    # Clicar e capturar o download
                                    with page.expect_download(timeout=30000) as download_info:
                                        download_button.click()
                                        download = download_info.value

                                    # Ler bytes do PDF
                                    temp_path = download.path()
                                    pdf_bytes = Path(temp_path).read_bytes()
                                    pdf_hash = sha256(pdf_bytes)
                                    print(f"[{human_time()}] ✅ PDF baixado: {item['id_mediador']} ({len(pdf_bytes) / 1024:.1f} KB)")
                                else:
                                    print(f"[{human_time()}] ⚠️  Botão de Download não encontrado para {item['id_mediador']}")

                            except Exception as e:
                                print(f"[{human_time()}] ⚠️  Erro ao baixar PDF {item['id_mediador']}: {e}")

                        # Salvar tudo
                        salva_instrumento(uf, meta, html.encode("utf-8"), pdf_bytes, pdf_hash)
                        total_instrumentos_ano += 1
                        total_geral += 1

                    print(f"[{human_time()}] ✅ {uf}-{tipo_nome}-{ano} página {pagina} -> {len(instrumentos)} docs (ano: {total_instrumentos_ano}, total: {total_geral})")

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

                print(f"[{human_time()}] ✅ Ano {ano} concluído: {total_instrumentos_ano} instrumentos")

            except Exception as e:
                print(f"[{human_time()}] ❌ {uf}-{tipo_nome}-{ano} ERRO FATAL: {e}")

            finally:
                browser.close()

        # Pequeno delay entre anos para não sobrecarregar o site
        time.sleep(2)

    print(f"\n[{human_time()}] 🏁 {uf}-{tipo_nome} FINALIZADO - Total: {total_geral} instrumentos coletados")


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
