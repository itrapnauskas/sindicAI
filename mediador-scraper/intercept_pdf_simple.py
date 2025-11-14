#!/usr/bin/env python3
"""
Script SIMPLIFICADO para interceptar URL do PDF
Usa os mesmos seletores do scraper_playwright.py que FUNCIONA!
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

print("🔍 INTERCEPTANDO URL DO PDF (VERSÃO SIMPLES)")
print("=" * 70)

captured_urls = []

def handle_request(request):
    url = request.url
    if 'imagemAnexo' in url or ('.pdf' in url.lower() and 'mediador' in url):
        print(f"\n🌐 REQUEST PDF: {url}")
        captured_urls.append(('REQUEST', url))

def handle_response(response):
    url = response.url
    if 'imagemAnexo' in url or ('.pdf' in url.lower() and 'mediador' in url):
        print(f"\n✅ RESPONSE PDF: {url}")
        print(f"   Status: {response.status}")
        captured_urls.append(('RESPONSE', url))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()

    # Handlers
    page.on("request", handle_request)
    page.on("response", handle_response)

    print("\n📡 Acessando Sistema Mediador...")
    page.goto('https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo',
              timeout=120000)

    print("⏳ Aguardando 5s para carregar...")
    page.wait_for_timeout(5000)

    try:
        # SELETORES CORRETOS (mesmos do scraper original)
        print("\n📝 Preenchendo formulário...")

        # UF
        page.select_option("#cboUFRegistro", "AC")
        print("✅ UF: AC")

        # Tipo (index=1 para ACT)
        page.select_option("#cboTPRequerimento", index=1)
        print("✅ Tipo: ACT (index=1)")

        # Habilitar filtro de data
        page.check("#chkPeriodoRegistro")
        page.wait_for_timeout(500)

        # Datas
        page.fill("#txtDTInicioRegistro", "01/01/2025")
        page.fill("#txtDTFimRegistro", "31/12/2025")
        print("✅ Período: 01/01/2025 - 31/12/2025")

        # Status de Vigência (OBRIGATÓRIO!)
        page.select_option("#cboSTVigencia", "2")  # 2 = Todos
        print("✅ Status Vigência: Todos")

        # Pesquisar
        print("\n🔎 Clicando em Pesquisar...")
        page.click("#btnPesquisar")
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        print("\n📊 Resultados carregados!")
        print("🔍 Procurando botão de Download...")

        # Procurar primeiro botão fDownload
        download_button = page.locator("a[onclick*='fDownload']").first

        if download_button.count() == 0:
            print("❌ Nenhum botão de download encontrado!")
        else:
            print("✅ Botão encontrado!")
            onclick = download_button.get_attribute('onclick')
            print(f"   onclick: {onclick}")

            print("\n🖱️  Clicando no botão...")

            try:
                # Capturar download
                with page.expect_download(timeout=30000) as download_info:
                    download_button.click()
                    download = download_info.value

                pdf_url = download.url
                print(f"\n🎯 URL DO PDF CAPTURADA:")
                print(f"   {pdf_url}")

                # Salvar
                download.save_as("teste_pdf.pdf")
                print(f"\n✅ PDF salvo: teste_pdf.pdf")

            except Exception as e:
                print(f"\n⚠️  Erro ao capturar download: {e}")

        print("\n⏳ Aguardando 5s para ver mais requests...")
        page.wait_for_timeout(5000)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        browser.close()

print("\n" + "=" * 70)
if captured_urls:
    print("\n🔗 URLs CAPTURADAS:")
    for tipo, url in captured_urls:
        print(f"   [{tipo}] {url}")
else:
    print("\n⚠️  Nenhuma URL capturada")

print("\n✅ PROCESSO CONCLUÍDO")
