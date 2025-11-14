#!/usr/bin/env python3
"""
Interceptar a função fDownload() usando Playwright
Salvando o HTML que você coletou e injetando JavaScript para capturar a chamada
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

# Salvar o HTML em arquivo temporário
html_path = Path(__file__).parent / "temp_result_page.html"

# Ler o HTML dos samples (se existir)
sample_html = Path(__file__).parent / "samples/html_examples/instrumento.html"

if sample_html.exists():
    print(f"✅ Usando HTML de: {sample_html}")
    html_content = sample_html.read_text(encoding="utf-8")
else:
    print("❌ Arquivo HTML não encontrado!")
    print("Por favor, certifique-se de que samples/html_examples/instrumento.html existe")
    exit(1)

print("\n🔍 INTERCEPTANDO FUNÇÃO fDownload()")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Variável para capturar chamadas
    captured_calls = []

    # Injetar código JavaScript ANTES de carregar a página
    page.add_init_script("""
        window.fDownloadCalls = [];
        window.fDownload = function(solicitacao, cnpj) {
            console.log('fDownload chamado!', solicitacao, cnpj);
            window.fDownloadCalls.push({
                solicitacao: solicitacao,
                cnpj: cnpj,
                timestamp: new Date().toISOString()
            });

            // Tentar construir URLs possíveis
            const possibleUrls = [
                `/sistemas/mediador/Download/${solicitacao}/${cnpj}`,
                `/sistemas/mediador/download/${solicitacao}/${cnpj}`,
                `/sistemas/mediador/DownloadInstrumento?solicitacao=${solicitacao}&cnpj=${cnpj}`,
                `/sistemas/mediador/api/download?id=${solicitacao}&cnpj=${cnpj}`,
            ];

            console.log('URLs possíveis:', possibleUrls);
            window.possibleUrls = possibleUrls;
        };
    """)

    # Listener para console.log
    page.on("console", lambda msg: print(f"   [CONSOLE] {msg.text}"))

    # Listener para requisições
    page.on("request", lambda req: print(f"   [REQUEST] {req.method} {req.url}") if 'download' in req.url.lower() else None)

    # Carregar HTML
    print("\n📄 Carregando HTML...")
    page.set_content(html_content)

    print("✅ HTML carregado")

    # Procurar links de download
    download_links = page.locator("a[onclick*='fDownload']").all()
    print(f"\n📊 Encontrados {len(download_links)} links de download")

    if download_links:
        # Pegar primeiro link
        first_link = download_links[0]
        onclick_attr = first_link.get_attribute("onclick")
        print(f"\n📋 Primeiro link onclick: {onclick_attr}")

        # Clicar no link
        print("\n🖱️  Clicando no link...")
        first_link.click()
        page.wait_for_timeout(1000)

        # Pegar os dados capturados
        calls = page.evaluate("window.fDownloadCalls")
        urls = page.evaluate("window.possibleUrls || []")

        print(f"\n✅ Chamadas capturadas: {len(calls)}")

        if calls:
            for call in calls:
                print(f"\n📦 Chamada capturada:")
                print(f"   Solicitação: {call['solicitacao']}")
                print(f"   CNPJ: {call['cnpj']}")
                print(f"   Timestamp: {call['timestamp']}")

        if urls:
            print(f"\n🔗 URLs possíveis construídas:")
            for url in urls:
                full_url = f"https://www3.mte.gov.br{url}"
                print(f"   {full_url}")

            # Salvar URLs em arquivo
            urls_file = Path(__file__).parent / "possible_pdf_urls.txt"
            with open(urls_file, "w") as f:
                for url in urls:
                    f.write(f"https://www3.mte.gov.br{url}\n")
            print(f"\n💾 URLs salvas em: {urls_file}")

    browser.close()

print("\n" + "="*60)
print("✅ ANÁLISE CONCLUÍDA!")
