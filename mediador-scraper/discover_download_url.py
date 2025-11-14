#!/usr/bin/env python3
"""
DESCOBRIR URL DE DOWNLOAD REAL
Navegando, pesquisando e clicando em Download para capturar a URL
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import re

print("🔍 DESCOBRINDO URL REAL DE DOWNLOAD DE PDF")
print("="*70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    page = context.new_page()

    # Capturar todas as requisições
    all_requests = []
    download_urls = []

    def handle_request(request):
        all_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers)
        })
        # Capturar especificamente downloads
        if any(keyword in request.url.lower() for keyword in ['download', 'pdf', '.pdf', 'arquivo']):
            print(f"\n🎯 CAPTURADO: {request.method} {request.url}")
            download_urls.append(request.url)

    page.on("request", handle_request)

    try:
        print("\n🌐 Navegando para Mediador...")
        page.goto("https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
                 wait_until="load", timeout=180000)
        page.wait_for_timeout(3000)
        print("✅ Página carregada")

        # Preencher formulário
        print("\n📝 Preenchendo formulário (AC, Todos, 2025)...")

        page.select_option("#cboUFRegistro", "AC")
        page.select_option("#cboSTVigencia", "2")  # Todos

        # Período de Vigência (APENAS vigência, não registro)
        page.click("#chkVigencia")
        page.wait_for_timeout(500)
        page.fill("#txtDTInicioVigencia", "01/01/2025")
        page.fill("#txtDTFimVigencia", "31/12/2025")

        print("✅ Formulário preenchido")

        # Pesquisar
        print("\n🔍 Pesquisando...")
        page.click("#btnPesquisar")
        page.wait_for_load_state("networkidle", timeout=120000)
        page.wait_for_timeout(3000)
        print("✅ Resultados carregados")

        # Salvar HTML da página de resultados
        html = page.content()
        html_path = Path(__file__).parent / "result_page_with_downloads.html"
        html_path.write_text(html, encoding="utf-8")
        print(f"💾 HTML salvo em: {html_path}")

        # Procurar links de download
        download_links = page.locator("a[onclick*='fDownload']").all()
        print(f"\n📊 Links de download encontrados: {len(download_links)}")

        if download_links:
            first_link = download_links[0]
            onclick = first_link.get_attribute("onclick")
            print(f"\n📋 Primeiro onclick: {onclick}")

            # Extrair parâmetros
            match = re.search(r"fDownload\('([^']+)','([^']+)'\)", onclick)
            if match:
                solicitacao = match.group(1)
                cnpj = match.group(2)
                print(f"\n📦 Parâmetros extraídos:")
                print(f"   Solicitação: {solicitacao}")
                print(f"   CNPJ: {cnpj}")

                # Tentar clicar e capturar download
                print(f"\n🖱️  Clicando no primeiro link de Download...")
                print("   (aguarde, vamos capturar a requisição...)")

                # Clicar
                first_link.click()
                page.wait_for_timeout(5000)  # Aguardar requisições

                if download_urls:
                    print(f"\n✅ URLs DE DOWNLOAD CAPTURADAS:")
                    for url in download_urls:
                        print(f"   {url}")

                    # Salvar em arquivo
                    urls_file = Path(__file__).parent / "captured_download_urls.txt"
                    with open(urls_file, "w") as f:
                        for url in download_urls:
                            f.write(f"{url}\n")
                    print(f"\n💾 URLs salvas em: {urls_file}")
                else:
                    print("\n⚠️  Nenhuma requisição de download capturada")
                    print("   Tentando construir URLs manualmente...")

                    possible_urls = [
                        f"https://www3.mte.gov.br/sistemas/mediador/Download/{solicitacao}/{cnpj}",
                        f"https://www3.mte.gov.br/sistemas/mediador/download/{solicitacao}/{cnpj}",
                        f"https://www3.mte.gov.br/sistemas/mediador/DownloadInstrumento?solicitacao={solicitacao}&cnpj={cnpj}",
                        f"https://www3.mte.gov.br/sistemas/mediador/Download?id={solicitacao}&cnpj={cnpj}",
                    ]

                    print("\n🔗 URLs possíveis (baseado no padrão):")
                    for url in possible_urls:
                        print(f"   {url}")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        browser.close()

print("\n" + "="*70)
print("✅ DESCOBERTA CONCLUÍDA!")
