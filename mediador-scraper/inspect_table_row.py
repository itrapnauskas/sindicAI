#!/usr/bin/env python3
"""
Captura o HTML de uma linha específica da tabela de resultados
para descobrir onde está o link/timestamp do PDF
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("🔍 INSPECIONANDO LINHA DA TABELA DE RESULTADOS")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_timeout(120000)

    print("📡 Acessando Sistema Mediador...")
    page.goto('https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo',
              wait_until='domcontentloaded',
              timeout=120000)

    print("⏳ Esperando formulário...")
    page.wait_for_selector('#uf', state='visible', timeout=120000)
    page.wait_for_timeout(2000)

    print("📝 Preenchendo: AC, ACT, 2025...")
    page.select_option('#uf', 'AC')
    page.select_option('#tpInstrumento', '2')
    page.fill('#dtRegistroIni', '01/01/2025')
    page.fill('#dtRegistroFim', '31/12/2025')

    print("🔎 Consultando...")
    page.click('button:has-text("Consultar")')
    page.wait_for_timeout(5000)  # Espera resultados

    print("📊 Capturando HTML da tabela...")

    # Pegar HTML completo da página de resultados
    html = page.content()

    # Salvar HTML completo
    with open('tabela_resultados.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Salvou: tabela_resultados.html ({len(html):,} bytes)")

    # Analisar com BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Procurar primeira linha com dados (tr que tem MR)
    rows = soup.find_all('tr')

    print(f"\n📋 Total de <tr> encontrados: {len(rows)}")

    for i, row in enumerate(rows[:10]):  # Primeiras 10 linhas
        row_html = str(row)
        if 'MR' in row_html and ('2025' in row_html or '2024' in row_html or '2023' in row_html):
            print(f"\n{'='*70}")
            print(f"LINHA {i} (contém MR + ano):")
            print('='*70)
            print(row.prettify())
            print("\n🔍 Atributos da linha:")
            for attr, value in row.attrs.items():
                print(f"   {attr} = {value}")

            print("\n🔗 Links (<a>) na linha:")
            for link in row.find_all('a'):
                print(f"\n   Tag: {link.name}")
                print(f"   Atributos: {link.attrs}")
                print(f"   Texto: {link.get_text(strip=True)[:50]}")

                # Se tiver onclick, mostrar
                if link.get('onclick'):
                    print(f"   onclick: {link['onclick']}")

                # Se tiver href, mostrar
                if link.get('href'):
                    print(f"   href: {link['href']}")

            # Parar após primeira linha válida
            break

    browser.close()

print("\n💡 PRÓXIMO PASSO:")
print("   1. Abra tabela_resultados.html no VS Code")
print("   2. Procure por 'imagemAnexo' ou '.pdf'")
print("   3. Ou procure pelo num_solicitacao: MR031724")
print("   4. Veja se o link completo do PDF está em algum lugar!")
