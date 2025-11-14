#!/usr/bin/env python3
"""
Debug: Tira screenshot DO FORMULÁRIO PREENCHIDO antes de pesquisar
Para verificar se os campos de Vigência realmente estão preenchidos
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
import time

def debug_form():
    print("🔍 DEBUG - SCREENSHOT DO FORMULÁRIO PREENCHIDO")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver
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

            # Período de Registro
            page.check("#chkPeriodoRegistro")
            page.wait_for_timeout(500)
            page.fill("#txtDTInicioRegistro", "01/01/2024")
            page.fill("#txtDTFimRegistro", "31/12/2024")
            print("  ✅ Período de Registro: 01/01/2024 até 31/12/2024")

            # Período de Vigência
            page.check("#chkVigencia")
            page.wait_for_timeout(500)
            page.fill("#txtDTInicioVigencia", "01/01/2024")
            page.fill("#txtDTFimVigencia", "31/12/2024")
            print("  ✅ Período de Vigência: 01/01/2024 até 31/12/2024")

            # AGUARDAR 2 segundos para campos estabilizarem
            print("\n⏳ Aguardando 2 segundos para campos estabilizarem...")
            page.wait_for_timeout(2000)

            # Tirar screenshot ANTES de pesquisar
            screenshot_path = Path(__file__).parent / "debug_form_filled.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n📸 Screenshot ANTES de pesquisar salvo: {screenshot_path}")

            # Verificar valores dos campos via JavaScript
            print("\n🔍 Verificando valores dos campos via JavaScript:")

            check_vigencia = page.evaluate("document.querySelector('#chkVigencia').checked")
            print(f"  chkVigencia checked: {check_vigencia}")

            val_inicio = page.evaluate("document.querySelector('#txtDTInicioVigencia').value")
            print(f"  txtDTInicioVigencia value: '{val_inicio}'")

            val_fim = page.evaluate("document.querySelector('#txtDTFimVigencia').value")
            print(f"  txtDTFimVigencia value: '{val_fim}'")

            check_registro = page.evaluate("document.querySelector('#chkPeriodoRegistro').checked")
            print(f"  chkPeriodoRegistro checked: {check_registro}")

            val_reg_inicio = page.evaluate("document.querySelector('#txtDTInicioRegistro').value")
            print(f"  txtDTInicioRegistro value: '{val_reg_inicio}'")

            val_reg_fim = page.evaluate("document.querySelector('#txtDTFimRegistro').value")
            print(f"  txtDTFimRegistro value: '{val_reg_fim}'")

            # Agora pesquisar
            print("\n🔍 Clicando em Pesquisar...")
            page.click("#btnPesquisar")
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(2000)

            # Screenshot APÓS pesquisar
            screenshot_path2 = Path(__file__).parent / "debug_form_result.png"
            page.screenshot(path=str(screenshot_path2), full_page=True)
            print(f"📸 Screenshot APÓS pesquisar salvo: {screenshot_path2}")

            # Salvar HTML resultado
            html = page.content()
            html_path = Path(__file__).parent / "debug_form_result.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"💾 HTML resultado salvo: {html_path}")

            print("\n" + "="*60)
            print("✅ DEBUG CONCLUÍDO")
            print("="*60)
            print("\nArquivos salvos:")
            print(f"  - {screenshot_path} (formulário preenchido)")
            print(f"  - {screenshot_path2} (resultado da busca)")
            print(f"  - {html_path} (HTML do resultado)")

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
    debug_form()
