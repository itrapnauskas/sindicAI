#!/usr/bin/env python3
"""
Script de inspeção do site Mediador
Descobre os seletores CSS corretos dos campos do formulário
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json

def inspect_mediador():
    """Inspeciona o site do Mediador e extrai informações dos campos"""

    print("🔍 INSPECIONANDO SITE DO MEDIADOR")
    print("="*60)

    with sync_playwright() as p:
        # Lançar browser em modo visível
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            print("\n📡 Navegando para o site...")
            page.goto("https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
                     wait_until="networkidle",
                     timeout=60000)

            print("✅ Página carregada!")
            print("\n⏳ Aguardando 3 segundos para JavaScript carregar...")
            page.wait_for_timeout(3000)

            # Tirar screenshot
            screenshot_path = Path(__file__).parent / "mediador_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot salvo em: {screenshot_path}")

            # Pegar HTML completo
            html = page.content()
            soup = BeautifulSoup(html, "lxml")

            print("\n" + "="*60)
            print("🔍 ANALISANDO CAMPOS DO FORMULÁRIO")
            print("="*60)

            # Encontrar todos os selects
            print("\n📋 SELECTS (dropdowns):")
            selects = soup.find_all("select")
            for i, select in enumerate(selects):
                name = select.get("name", "N/A")
                id_attr = select.get("id", "N/A")
                classes = " ".join(select.get("class", []))
                print(f"\n  [{i+1}] <select>")
                print(f"      name: {name}")
                print(f"      id: {id_attr}")
                print(f"      class: {classes}")

                # Ver algumas opções
                options = select.find_all("option")[:5]
                print(f"      opções: {[opt.get_text(strip=True) for opt in options]}")

            # Encontrar todos os inputs
            print("\n\n📝 INPUTS:")
            inputs = soup.find_all("input")
            for i, inp in enumerate(inputs):
                inp_type = inp.get("type", "text")
                name = inp.get("name", "N/A")
                id_attr = inp.get("id", "N/A")
                placeholder = inp.get("placeholder", "")
                classes = " ".join(inp.get("class", []))

                print(f"\n  [{i+1}] <input type='{inp_type}'>")
                print(f"      name: {name}")
                print(f"      id: {id_attr}")
                print(f"      class: {classes}")
                if placeholder:
                    print(f"      placeholder: {placeholder}")

            # Encontrar botões
            print("\n\n🔘 BOTÕES:")
            buttons = soup.find_all(["button", "input"])
            for i, btn in enumerate(buttons):
                if btn.name == "input" and btn.get("type") not in ["submit", "button"]:
                    continue

                text = btn.get_text(strip=True) or btn.get("value", "")
                name = btn.get("name", "N/A")
                id_attr = btn.get("id", "N/A")
                classes = " ".join(btn.get("class", []))

                print(f"\n  [{i+1}] <{btn.name}>")
                print(f"      texto: {text}")
                print(f"      name: {name}")
                print(f"      id: {id_attr}")
                print(f"      class: {classes}")

            # Salvar HTML completo para análise
            html_path = Path(__file__).parent / "mediador_page.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"\n\n💾 HTML completo salvo em: {html_path}")

            # Tentar identificar campos específicos
            print("\n" + "="*60)
            print("🎯 IDENTIFICAÇÃO DE CAMPOS ESPECÍFICOS")
            print("="*60)

            selectors = {}

            # Procurar select de UF
            for select in selects:
                text_content = str(select).lower()
                if "uf" in text_content or any(uf in text_content.upper() for uf in ["AC", "AL", "AM", "SP", "RJ"]):
                    selectors["uf"] = {
                        "name": select.get("name"),
                        "id": select.get("id"),
                        "sugestão": f"select[name='{select.get('name')}']" if select.get("name") else f"select[id='{select.get('id')}']"
                    }
                    print(f"\n✅ UF encontrado:")
                    print(f"   Seletor sugerido: {selectors['uf']['sugestão']}")
                    break

            # Procurar select de tipo
            for select in selects:
                text_content = str(select).lower()
                if "tipo" in text_content or "instrumento" in text_content:
                    selectors["tipo"] = {
                        "name": select.get("name"),
                        "id": select.get("id"),
                        "sugestão": f"select[name='{select.get('name')}']" if select.get("name") else f"select[id='{select.get('id')}']"
                    }
                    print(f"\n✅ Tipo de Instrumento encontrado:")
                    print(f"   Seletor sugerido: {selectors['tipo']['sugestão']}")
                    break

            # Procurar inputs de data
            date_inputs = [inp for inp in inputs if inp.get("type") in ["text", "date"] or "data" in str(inp).lower()]
            if len(date_inputs) >= 2:
                selectors["data_inicio"] = {
                    "name": date_inputs[0].get("name"),
                    "id": date_inputs[0].get("id"),
                    "sugestão": f"input[name='{date_inputs[0].get('name')}']" if date_inputs[0].get("name") else f"input[id='{date_inputs[0].get('id')}']"
                }
                selectors["data_fim"] = {
                    "name": date_inputs[1].get("name"),
                    "id": date_inputs[1].get("id"),
                    "sugestão": f"input[name='{date_inputs[1].get('name')}']" if date_inputs[1].get("name") else f"input[id='{date_inputs[1].get('id')}']"
                }
                print(f"\n✅ Data Início encontrado:")
                print(f"   Seletor sugerido: {selectors['data_inicio']['sugestão']}")
                print(f"\n✅ Data Fim encontrado:")
                print(f"   Seletor sugerido: {selectors['data_fim']['sugestão']}")

            # Procurar botão pesquisar
            for btn in buttons:
                text = (btn.get_text(strip=True) or btn.get("value", "")).lower()
                if "pesquis" in text:
                    selectors["botao_pesquisar"] = {
                        "name": btn.get("name"),
                        "id": btn.get("id"),
                        "text": btn.get_text(strip=True) or btn.get("value"),
                        "sugestão": f"button:has-text('{btn.get_text(strip=True)}')" if btn.name == "button" else f"input[value='{btn.get('value')}']"
                    }
                    print(f"\n✅ Botão Pesquisar encontrado:")
                    print(f"   Seletor sugerido: {selectors['botao_pesquisar']['sugestão']}")
                    break

            # Salvar seletores em JSON
            selectors_path = Path(__file__).parent / "selectors.json"
            selectors_path.write_text(json.dumps(selectors, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\n\n💾 Seletores salvos em: {selectors_path}")

            print("\n" + "="*60)
            print("✅ INSPEÇÃO CONCLUÍDA!")
            print("="*60)
            print("\n📋 Próximos passos:")
            print("  1. Verifique mediador_screenshot.png")
            print("  2. Revise mediador_page.html se necessário")
            print("  3. Use os seletores sugeridos em selectors.json")
            print("\n⏸️  Pressione Enter para fechar o browser...")
            input()

        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            print("\n⏸️  Pressione Enter para fechar...")
            input()

        finally:
            browser.close()

if __name__ == "__main__":
    inspect_mediador()
