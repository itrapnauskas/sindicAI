#!/usr/bin/env python3
"""
Captura a página completa de resultados para investigar botões de download
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

print("🔍 CAPTURANDO PÁGINA DE RESULTADOS COMPLETA")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Timeout maior para site lento
    page.set_default_timeout(120000)  # 120 segundos

    print("📡 Acessando Sistema Mediador...")
    page.goto('https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo',
              wait_until='domcontentloaded',  # Não espera todos os recursos
              timeout=120000)
    page.wait_for_timeout(3000)

    print("📝 Preenchendo formulário (AC, ACT, 2025)...")
    page.select_option('#uf', 'AC')
    page.select_option('#tpInstrumento', '2')
    page.fill('#dtRegistroIni', '01/01/2025')
    page.fill('#dtRegistroFim', '31/12/2025')

    print("🔎 Consultando...")
    page.click('button:has-text("Consultar")')
    page.wait_for_timeout(3000)

    print("💾 Salvando HTML completo...")
    html = page.content()

    output_file = Path(__file__).parent / 'pagina_resultados_completa.html'
    output_file.write_text(html, encoding='utf-8')

    print(f"✅ Salvou: {output_file}")
    print(f"📏 Tamanho: {len(html):,} bytes")

    # Contar links de download
    download_links = page.locator('a[onclick*="fDownload"]').count()
    print(f"🔗 Links com fDownload encontrados: {download_links}")

    # Contar outros tipos de links
    all_links = page.locator('a').count()
    print(f"🔗 Total de links na página: {all_links}")

    browser.close()

print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Abra pagina_resultados_completa.html no VS Code")
print("   2. Procure por 'Download' (Ctrl+F)")
print("   3. Veja TODOS os botões e links disponíveis")
print("   4. Identifique qual é o link CORRETO para PDF")
