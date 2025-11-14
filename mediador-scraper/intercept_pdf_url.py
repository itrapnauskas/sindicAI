#!/usr/bin/env python3
"""
Intercepta a URL do PDF quando clicar no botão fDownload
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

print("🔍 INTERCEPTANDO URL DO PDF")
print("=" * 70)

# Lista para capturar URLs
captured_urls = []
captured_downloads = []

def handle_request(request):
    """Captura todas as requisições"""
    url = request.url
    if 'imagemAnexo' in url or '.pdf' in url.lower() or 'download' in url.lower():
        print(f"\n🌐 REQUEST: {url}")
        captured_urls.append(url)

def handle_response(response):
    """Captura todas as respostas"""
    url = response.url
    if 'imagemAnexo' in url or '.pdf' in url.lower():
        print(f"\n✅ RESPONSE: {url}")
        print(f"   Status: {response.status}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        captured_urls.append(url)

with sync_playwright() as p:
    # Usar headless=False para ver o que acontece
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    page.set_default_timeout(120000)

    # Registrar handlers
    page.on("request", handle_request)
    page.on("response", handle_response)

    print("\n📡 Acessando Sistema Mediador...")
    page.goto('https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo',
              wait_until='domcontentloaded',
              timeout=120000)

    print("⏳ Esperando formulário (10s)...")
    page.wait_for_timeout(10000)

    # Procurar por select com opção AC (mais robusto que #uf)
    print("🔍 Procurando campo de UF...")
    uf_select = page.locator('select:has(option[value="AC"])').first

    if uf_select.count() == 0:
        print("\n❌ Campo UF não encontrado! Site pode estar fora do ar.")
        print("💾 Salvando HTML para debug...")
        html = page.content()
        Path("error_page.html").write_text(html, encoding='utf-8')
        print("   Salvo em: error_page.html")
        browser.close()
        exit(1)

    # Pegar IDs reais dos campos
    uf_id = uf_select.get_attribute('id')
    uf_name = uf_select.get_attribute('name')
    print(f"✅ Campo UF encontrado: id='{uf_id}' name='{uf_name}'")

    # Procurar campo de tipo
    tipo_select = page.locator('select:has(option[value="2"])').first
    tipo_id = tipo_select.get_attribute('id') if tipo_select.count() > 0 else 'tpInstrumento'

    print("\n📝 Preenchendo: AC, ACT, 2025...")
    page.select_option(f'#{uf_id}', 'AC')
    page.select_option(f'#{tipo_id}', '2')
    page.fill('#dtRegistroIni', '01/01/2025')
    page.fill('#dtRegistroFim', '31/12/2025')

    print("🔎 Consultando...")
    page.click('button:has-text("Consultar")')
    page.wait_for_timeout(5000)

    print("\n📊 Procurando primeiro botão de Download...")

    # Procurar botão de download específico para MR031724
    download_button = page.locator("a[onclick*='MR031724/2025'][onclick*='73471989007955']").first

    if download_button.count() == 0:
        print("❌ Botão de download não encontrado!")
        browser.close()
        exit(1)

    print("✅ Botão encontrado!")
    print("\n🖱️  Clicando no botão fDownload...")

    try:
        # Tentar capturar download
        with page.expect_download(timeout=30000) as download_info:
            download_button.click()
            download = download_info.value

        # URL do download
        pdf_url = download.url
        print(f"\n🎯 URL DO PDF CAPTURADA:")
        print(f"   {pdf_url}")

        # Salvar para conferir
        download.save_as("teste_download.pdf")
        print(f"\n✅ PDF salvo em: teste_download.pdf")

    except Exception as e:
        print(f"\n⚠️  Erro ao capturar download: {e}")
        print("\n📋 URLs capturadas nos listeners:")
        for url in captured_urls:
            print(f"   {url}")

    print("\n⏳ Aguardando 5s para ver se há mais requests...")
    page.wait_for_timeout(5000)

    browser.close()

print("\n" + "=" * 70)
print("✅ PROCESSO CONCLUÍDO")

if captured_urls:
    print("\n🔗 URLs CAPTURADAS:")
    for url in set(captured_urls):  # Remover duplicatas
        print(f"   {url}")
