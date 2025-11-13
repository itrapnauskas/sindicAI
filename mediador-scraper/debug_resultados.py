#!/usr/bin/env python3
"""
Debug: Inspeciona a página de RESULTADOS após pesquisar
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def debug_resultados():
    print("🔍 DEBUG - PÁGINA DE RESULTADOS")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            print("\n🌐 Navegando...")
            page.goto("https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
                     wait_until="load", timeout=180000)
            page.wait_for_timeout(3000)
            print("✅ Página carregada")

            # Preencher formulário
            print("\n📝 Preenchendo formulário:")
            page.select_option("#cboUFRegistro", "AC")
            print("  ✅ UF: AC")

            page.select_option("#cboTPRequerimento", index=1)  # ACT
            print("  ✅ Tipo: Acordo Coletivo (index 1)")

            page.check("#chkPeriodoRegistro")
            page.wait_for_timeout(500)
            page.fill("#txtDTInicioRegistro", "01/01/2020")
            page.fill("#txtDTFimRegistro", "13/11/2025")
            print("  ✅ Datas: 01/01/2020 até 13/11/2025")

            # Pesquisar
            print("\n🔍 Pesquisando...")
            page.click("#btnPesquisar")
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(3000)
            print("✅ Pesquisa concluída")

            # Screenshot
            screenshot_path = Path(__file__).parent / "resultados_screenshot.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n📸 Screenshot salvo: {screenshot_path}")

            # Salvar HTML
            html = page.content()
            html_path = Path(__file__).parent / "resultados_page.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"💾 HTML salvo: {html_path}")

            # Analisar tabelas
            soup = BeautifulSoup(html, "lxml")
            print("\n" + "="*60)
            print("📊 ANÁLISE DE TABELAS")
            print("="*60)

            tables = soup.find_all("table")
            print(f"\n🔢 Total de tabelas encontradas: {len(tables)}")

            for i, table in enumerate(tables):
                print(f"\n[Tabela {i+1}]")
                print(f"  ID: {table.get('id', 'N/A')}")
                print(f"  Class: {' '.join(table.get('class', []))}")

                rows = table.find_all("tr")
                print(f"  Linhas: {len(rows)}")

                if rows:
                    # Mostrar primeira linha (header)
                    first_row = rows[0]
                    headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]
                    print(f"  Cabeçalho: {headers[:5]}")  # Primeiras 5 colunas

                    # Mostrar segunda linha (primeiro registro)
                    if len(rows) > 1:
                        second_row = rows[1]
                        cells = [td.get_text(strip=True) for td in second_row.find_all("td")]
                        print(f"  Primeira linha de dados: {cells[:5]}")

            # Procurar mensagens
            print("\n" + "="*60)
            print("💬 MENSAGENS NA PÁGINA")
            print("="*60)

            # Procurar div de mensagem de "nenhum resultado"
            no_result = soup.find_all(string=lambda text: text and ("nenhum" in text.lower() or "não encontr" in text.lower()))
            if no_result:
                print("\n⚠️  Mensagens de 'sem resultados':")
                for msg in no_result[:3]:
                    print(f"  - {msg.strip()}")
            else:
                print("\n✅ Nenhuma mensagem de 'sem resultados' encontrada")

            # Procurar paginação
            pagination = soup.find_all("a", string=lambda text: text and any(x in text.lower() for x in ["próxima", "anterior", "primeira", "última"]))
            if pagination:
                print("\n📄 Links de paginação encontrados:")
                for link in pagination:
                    print(f"  - {link.get_text(strip=True)}: {link.get('href', 'N/A')}")

            print("\n" + "="*60)
            print("✅ DEBUG CONCLUÍDO")
            print("="*60)
            print("\nArquivos salvos:")
            print(f"  - {screenshot_path}")
            print(f"  - {html_path}")
            print("\n⏸️  Pressione Enter para fechar o browser...")
            input()

        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            input()

        finally:
            browser.close()

if __name__ == "__main__":
    debug_resultados()
