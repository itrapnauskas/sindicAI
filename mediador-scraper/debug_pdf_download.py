#!/usr/bin/env python3
"""
Debug: Descobrir URL real de download dos PDFs
Vai navegar, buscar um instrumento e clicar em Download para ver a URL
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
import time

def debug_pdf_url():
    print("🔍 DEBUG - DESCOBRIR URL DO PDF")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Voltando para headless
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True  # Ignorar erros de certificado SSL
        )
        page = context.new_page()

        # Listener para capturar todas as requisições
        pdf_requests = []

        def handle_request(request):
            if 'download' in request.url.lower() or 'pdf' in request.url.lower() or '.pdf' in request.url:
                print(f"\n🔗 REQUEST CAPTURADO:")
                print(f"   URL: {request.url}")
                print(f"   Method: {request.method}")
                print(f"   Headers: {request.headers}")
                pdf_requests.append(request.url)

        page.on("request", handle_request)

        try:
            print("\n🌐 Navegando para Mediador...")
            page.goto("https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
                     wait_until="load", timeout=180000)
            page.wait_for_timeout(3000)
            print("✅ Página carregada")

            # Preencher formulário (usando clicks reais para JavaScript executar)
            print("\n📝 Preenchendo formulário (AC, ACT, 2025)...")

            # Selecionar UF de Registro
            page.select_option("#cboUFRegistro", "AC")
            print("✅ UF selecionada: AC")

            # Selecionar tipo de instrumento
            page.select_option("#cboTPRequerimento", index=1)  # ACT
            print("✅ Tipo selecionado: Acordo Coletivo (index 1)")

            # Status de Vigência
            page.select_option("#cboSTVigencia", "2")  # Todos
            print("✅ Status de Vigência: Todos")

            # CLICAR nos checkboxes para ativar JavaScript do site
            print("\n📅 Ativando campos de data...")

            # Período de Registro
            page.click("#chkPeriodoRegistro")
            page.wait_for_timeout(500)  # Aguardar JavaScript ativar campos
            page.fill("#txtDTInicioRegistro", "01/01/2025")
            page.fill("#txtDTFimRegistro", "31/12/2025")
            print("✅ Período de Registro: 01/01/2025 até 31/12/2025")

            # Período de Vigência
            page.click("#chkVigencia")
            page.wait_for_timeout(500)  # Aguardar JavaScript ativar campos
            page.fill("#txtDTInicioVigencia", "01/01/2025")
            page.fill("#txtDTFimVigencia", "31/12/2025")
            print("✅ Período de Vigência: 01/01/2025 até 31/12/2025")

            print("✅ Formulário preenchido")

            # Pesquisar
            print("\n🔍 Pesquisando...")
            page.click("#btnPesquisar")
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(2000)
            print("✅ Resultados carregados")

            # Procurar PRIMEIRO link de download na página
            print("\n🎯 Procurando primeiro link de Download...")

            # PRIMEIRO: Salvar HTML para debug
            html = page.content()
            html_path = Path(__file__).parent / "debug_download_page.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"💾 HTML salvo em: {html_path}")

            # Contar quantos links com texto "Download" existem
            download_links = page.locator("a:has-text('Download')").all()
            print(f"📊 Links com 'Download': {len(download_links)}")

            # Tentar também por onclick
            onclick_links = page.locator("a[onclick*='fDownload']").all()
            print(f"📊 Links com onclick='fDownload': {len(onclick_links)}")

            if not download_links and not onclick_links:
                print("❌ Nenhum link de Download encontrado!")
                print(f"📋 Verifique o HTML em: {html_path}")
                return

            # Usar onclick_links se download_links estiver vazio
            links_to_use = download_links if download_links else onclick_links

            print(f"✅ Usando {len(links_to_use)} links encontrados")

            # Pegar o primeiro
            first_link = links_to_use[0]
            onclick_attr = first_link.get_attribute("onclick")
            print(f"\n📋 Atributo onclick do primeiro link:")
            print(f"   {onclick_attr}")

            # Extrair parâmetros
            import re
            match = re.search(r"fDownload\('([^']+)','([^']+)'\)", onclick_attr)
            if match:
                solicitacao = match.group(1)
                cnpj_hash = match.group(2)
                print(f"\n📦 Parâmetros extraídos:")
                print(f"   Solicitação: {solicitacao}")
                print(f"   CNPJ/Hash: {cnpj_hash}")

            # Agora CLICAR no link e capturar o que acontece
            print("\n🖱️  CLICANDO NO LINK DE DOWNLOAD...")
            print("   (aguarde, vamos capturar a URL real...)")

            # Esperar por navegação ou popup
            with page.expect_download(timeout=30000) as download_info:
                first_link.click()
                download = download_info.value

                print(f"\n✅ DOWNLOAD INICIADO!")
                print(f"   URL: {download.url}")
                print(f"   Suggested filename: {download.suggested_filename}")

                # Salvar o PDF para testar
                pdf_path = Path(__file__).parent / "test_download.pdf"
                download.save_as(str(pdf_path))
                print(f"   💾 Salvo em: {pdf_path}")
                print(f"   📊 Tamanho: {pdf_path.stat().st_size / 1024:.2f} KB")

            print("\n" + "="*60)
            print("✅ DEBUG CONCLUÍDO!")
            print("="*60)

            if pdf_requests:
                print("\n📋 TODAS as URLs de PDF capturadas:")
                for url in pdf_requests:
                    print(f"   {url}")

        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

if __name__ == "__main__":
    debug_pdf_url()
