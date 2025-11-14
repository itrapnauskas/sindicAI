#!/usr/bin/env python3
"""
Scraper modificado que CLICA nos botões de Download usando Playwright
Ao invés de tentar construir URLs, clicamos nos botões e capturamos os PDFs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from mediador.config import DATA_ROOT
from mediador.scraper_playwright import salva_instrumento, sha256, ensure_dir, human_time
import datetime as dt
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup

HEADLESS = True
TIMEOUT = 120
RATE_LIMIT = 1  # segundos entre requests

def worker_with_click_download(uf, tipo_codigo):
    """
    Coleta instrumentos E PDFs clicando nos botões de Download
    """

    # Mapear tipo_codigo para nome
    tipo_map = {
        "1": ("CCT", "Convenção Coletiva", 4),
        "2": ("ACT", "Acordo Coletivo", 1),
        "3": ("ADITIVO", "Termo Aditivo", [5, 6, 7, 8]),
    }

    tipo_nome, tipo_label, tipo_index = tipo_map[tipo_codigo]

    # Ano atual (apenas 2025 para teste)
    ano = 2025
    data_inicio = f"01/01/{ano}"
    data_fim = f"31/12/{ano}"

    print(f"\n[{human_time()}] 🚀 INICIANDO: {uf}-{tipo_nome}-{ano}")
    print(f"[{human_time()}] {'='*60}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        page = context.new_page()

        try:
            # Navegar
            print(f"[{human_time()}] 🌐 Navegando para Mediador...")
            page.goto("https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
                     wait_until="load", timeout=180000)
            page.wait_for_timeout(3000)

            # Preencher formulário
            print(f"[{human_time()}] 📝 Preenchendo formulário...")
            page.select_option("#cboUFRegistro", uf)
            page.select_option("#cboSTVigencia", "2")  # Todos

            # Selecionar tipo
            if isinstance(tipo_index, list):
                # Múltiplos índices (Aditivos)
                page.select_option("#cboTPRequerimento", index=tipo_index[0])
            else:
                page.select_option("#cboTPRequerimento", index=tipo_index)

            # Período de Vigência
            page.click("#chkVigencia")
            page.wait_for_timeout(500)
            page.fill("#txtDTInicioVigencia", data_inicio)
            page.fill("#txtDTFimVigencia", data_fim)

            print(f"[{human_time()}] ✅ Formulário preenchido")

            # Pesquisar
            page.click("#btnPesquisar")
            print(f"[{human_time()}] ✅ Botão Pesquisar clicado")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
            time.sleep(2)

            pagina = 1
            total_instrumentos = 0
            total_pdfs = 0

            while True:
                print(f"\n[{human_time()}] 📄 Processando página {pagina}...")

                # Procurar todas as linhas da tabela de resultados
                # Cada linha tem atributo "indice" com o número da solicitação
                rows = page.locator("tr[indice]").all()
                print(f"[{human_time()}] 📊 Encontradas {len(rows)} linhas na página {pagina}")

                if not rows:
                    print(f"[{human_time()}] ℹ️  Nenhum resultado na página {pagina}")
                    break

                # Processar cada linha
                for idx, row in enumerate(rows, 1):
                    try:
                        # Extrair indice (número da solicitação)
                        indice = row.get_attribute("indice")
                        print(f"\n[{human_time()}] 🔹 [{idx}/{len(rows)}] Processando: {indice}")

                        # Extrair dados da linha usando Beautiful Soup
                        row_html = row.inner_html()

                        # Parse básico para extrair metadados
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(row_html, "html.parser")

                        # Extrair informações
                        meta = {"id_mediador": "N/A", "num_solicitacao": indice}

                        # Procurar campos específicos
                        tables = soup.find_all("table", class_="TbForm")
                        if tables:
                            for table in tables:
                                cells = table.find_all("td")
                                for i, cell in enumerate(cells):
                                    text = cell.get_text(strip=True)

                                    if "Nº do Registro" in text and i + 1 < len(cells):
                                        meta["id_mediador"] = cells[i + 1].get_text(strip=True).split()[0]
                                    elif "Tipo do Instrumento" in text and i + 1 < len(cells):
                                        meta["tipo"] = cells[i + 1].get_text(strip=True).split()[0]
                                    elif "Vigência" in text and i + 1 < len(cells):
                                        vig_text = cells[i + 1].get_text(strip=True)
                                        dates = re.findall(r'\d{2}/\d{2}/\d{4}', vig_text)
                                        if len(dates) >= 2:
                                            meta["vigencia_inicio"] = dates[0]
                                            meta["vigencia_fim"] = dates[1]
                                    elif "Partes" in text and i + 1 < len(cells):
                                        meta["partes"] = cells[i + 1].get_text(separator=" / ", strip=True)

                        meta.update({
                            "tipo_simplificado": tipo_nome,
                            "uf": uf,
                            "ano": str(ano),
                            "fonte": "MEDIADOR",
                            "coletado_em": dt.datetime.now().isoformat()
                        })

                        print(f"[{human_time()}]    ✅ Metadados extraídos: {meta.get('id_mediador', 'N/A')}")

                        # AGORA A PARTE IMPORTANTE: CLICAR NO BOTÃO DE DOWNLOAD
                        pdf_bytes = None
                        pdf_hash = None

                        # Procurar botão de Download DENTRO desta linha (row)
                        download_button = row.locator("a[onclick*='fDownload']").first

                        if download_button.count() > 0:
                            print(f"[{human_time()}]    🎯 Botão de Download encontrado, clicando...")

                            try:
                                # Usar expect_download para capturar o arquivo baixado
                                with page.expect_download(timeout=30000) as download_info:
                                    download_button.click()
                                    download = download_info.value

                                print(f"[{human_time()}]    ✅ Download capturado: {download.suggested_filename}")

                                # Ler bytes do PDF
                                temp_path = download.path()
                                pdf_bytes = Path(temp_path).read_bytes()
                                pdf_hash = sha256(pdf_bytes)

                                print(f"[{human_time()}]    💾 PDF baixado: {len(pdf_bytes) / 1024:.2f} KB")
                                total_pdfs += 1

                            except Exception as e:
                                print(f"[{human_time()}]    ⚠️  Erro ao baixar PDF: {e}")
                        else:
                            print(f"[{human_time()}]    ⚠️  Botão de Download não encontrado")

                        # Salvar (HTML da linha + metadados + PDF)
                        salva_instrumento(uf, meta, row_html.encode("utf-8"), pdf_bytes, pdf_hash)
                        total_instrumentos += 1

                        print(f"[{human_time()}]    ✅ Salvo: {meta.get('id_mediador', 'N/A')}")

                        # Rate limiting
                        time.sleep(RATE_LIMIT)

                    except Exception as e:
                        print(f"[{human_time()}]    ❌ Erro ao processar linha {idx}: {e}")
                        continue

                print(f"\n[{human_time()}] ✅ Página {pagina} concluída: {len(rows)} instrumentos, {total_pdfs} PDFs")

                # Tentar ir para próxima página
                try:
                    next_button = page.locator("a:has-text('Próxima'), a:has-text('Próximo')").first
                    if next_button.count() > 0:
                        next_button.click()
                        page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
                        time.sleep(RATE_LIMIT)
                        pagina += 1
                    else:
                        break
                except Exception:
                    break

            print(f"\n[{human_time()}] 🏁 {uf}-{tipo_nome}-{ano} FINALIZADO")
            print(f"[{human_time()}] 📊 Total: {total_instrumentos} instrumentos, {total_pdfs} PDFs baixados")

        except Exception as e:
            print(f"\n[{human_time()}] ❌ ERRO FATAL: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()


if __name__ == "__main__":
    # Teste: Acre, Aditivos, 2025
    print(f"[{human_time()}] 🚀 TESTE: Scraper com Click Download")
    print(f"[{human_time()}] Coletando: AC - Aditivos - 2025")
    print(f"[{human_time()}] (Este teste vai BAIXAR os PDFs!)")
    print()

    worker_with_click_download("AC", "3")  # 3 = Aditivos

    print(f"\n[{human_time()}] ✅ TESTE CONCLUÍDO!")
