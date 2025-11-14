#!/usr/bin/env python3
"""
Debug: salva screenshot e HTML da página para ver o estado real
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

print("🔍 DEBUG: ESTADO DA PÁGINA")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(120000)

    print("\n📡 Acessando Sistema Mediador...")
    page.goto('https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo',
              wait_until='domcontentloaded',
              timeout=120000)

    print("⏳ Esperando 10 segundos para página carregar completamente...")
    page.wait_for_timeout(10000)

    # Salvar screenshot
    screenshot_path = Path("debug_screenshot.png")
    page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"📸 Screenshot salvo: {screenshot_path}")

    # Salvar HTML
    html = page.content()
    html_path = Path("debug_page.html")
    html_path.write_text(html, encoding='utf-8')
    print(f"💾 HTML salvo: {html_path} ({len(html):,} bytes)")

    # Procurar por selects e inputs
    print("\n🔍 Procurando por <select>:")
    selects = page.locator('select').all()
    print(f"   Total encontrados: {len(selects)}")
    for i, select in enumerate(selects[:10]):
        select_id = select.get_attribute('id')
        select_name = select.get_attribute('name')
        print(f"   [{i+1}] id='{select_id}' name='{select_name}'")

    print("\n🔍 Procurando por <input>:")
    inputs = page.locator('input').all()
    print(f"   Total encontrados: {len(inputs)}")
    for i, inp in enumerate(inputs[:10]):
        inp_id = inp.get_attribute('id')
        inp_name = inp.get_attribute('name')
        inp_type = inp.get_attribute('type')
        print(f"   [{i+1}] id='{inp_id}' name='{inp_name}' type='{inp_type}'")

    # Procurar especificamente por 'uf'
    print("\n🔍 Procurando elementos com 'uf':")
    uf_elements = page.get_by_text('uf', exact=False).all()
    print(f"   Total encontrados: {len(uf_elements)}")

    # Procurar por qualquer select que contenha opções de UF
    print("\n🔍 Procurando select com opção 'AC':")
    selects_with_ac = page.locator('select:has(option[value="AC"])').all()
    print(f"   Total encontrados: {len(selects_with_ac)}")
    for i, select in enumerate(selects_with_ac):
        select_id = select.get_attribute('id')
        select_name = select.get_attribute('name')
        print(f"   [{i+1}] id='{select_id}' name='{select_name}'")

    # Procurar por iframes
    print("\n🔍 Procurando <iframe>:")
    iframes = page.locator('iframe').all()
    print(f"   Total encontrados: {len(iframes)}")
    for i, iframe in enumerate(iframes):
        iframe_src = iframe.get_attribute('src')
        iframe_id = iframe.get_attribute('id')
        print(f"   [{i+1}] id='{iframe_id}' src='{iframe_src}'")

    print("\n⏳ Mantendo navegador aberto por 30s para inspeção manual...")
    print("    Pressione Ctrl+C para fechar antes")
    try:
        page.wait_for_timeout(30000)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")

    browser.close()

print("\n✅ DEBUG CONCLUÍDO")
print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Abra debug_screenshot.png para ver estado visual")
print("   2. Abra debug_page.html no VS Code")
print("   3. Procure por 'uf' ou 'UF' no HTML")
print("   4. Veja os IDs/names dos selects encontrados acima")
