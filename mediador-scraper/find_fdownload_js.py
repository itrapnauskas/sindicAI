#!/usr/bin/env python3
"""
Descobrir onde a função fDownload() está definida
Analisando scripts JS carregados pela página
"""

import requests
from bs4 import BeautifulSoup
import re

print("🔍 PROCURANDO DEFINIÇÃO DA FUNÇÃO fDownload()")
print("="*60)

# Buscar página principal
url = "https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo"
print(f"\n📥 Baixando: {url}")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

try:
    # Ignorar SSL errors
    response = session.get(url, verify=False, timeout=30)
    print(f"✅ Status: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Procurar todos os <script src="...">
    scripts = soup.find_all("script", src=True)
    print(f"\n📋 {len(scripts)} scripts externos encontrados:")

    js_urls = []
    for script in scripts:
        src = script.get("src")
        # Construir URL completa
        if src.startswith("/"):
            full_url = f"https://www3.mte.gov.br{src}"
        elif src.startswith("http"):
            full_url = src
        else:
            full_url = f"https://www3.mte.gov.br/sistemas/mediador/{src}"

        print(f"  - {src}")
        js_urls.append((src, full_url))

    # Baixar cada script e procurar fDownload
    print(f"\n🔎 Procurando fDownload nos scripts...")

    for name, url in js_urls:
        try:
            js_response = session.get(url, verify=False, timeout=10)
            if js_response.status_code == 200:
                content = js_response.text

                # Procurar função fDownload
                if "fDownload" in content:
                    print(f"\n✅ ENCONTRADO em: {name}")
                    print(f"   URL: {url}")

                    # Extrair a definição da função
                    match = re.search(r"function\s+fDownload\s*\([^)]*\)\s*\{[^}]*\}", content, re.DOTALL)
                    if match:
                        func_code = match.group(0)
                        print(f"\n📜 Definição da função:")
                        print("-" * 60)
                        print(func_code[:500])  # Primeiros 500 chars
                        if len(func_code) > 500:
                            print("...")
                        print("-" * 60)

                    # Salvar script completo para análise
                    with open("fDownload_script.js", "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"\n💾 Script completo salvo em: fDownload_script.js")
                    break
        except Exception as e:
            print(f"  ⚠️  Erro ao baixar {name}: {e}")

    # Procurar também scripts inline
    print(f"\n🔎 Procurando em scripts inline...")
    inline_scripts = soup.find_all("script", src=False)
    print(f"📋 {len(inline_scripts)} scripts inline encontrados")

    for idx, script in enumerate(inline_scripts):
        content = script.string or ""
        if "fDownload" in content and "function" in content:
            print(f"\n✅ ENCONTRADO em script inline #{idx}")

            # Extrair a definição
            match = re.search(r"function\s+fDownload\s*\([^)]*\)\s*\{[^}]*\}", content, re.DOTALL)
            if match:
                func_code = match.group(0)
                print(f"\n📜 Definição da função:")
                print("-" * 60)
                print(func_code)
                print("-" * 60)

            # Salvar script inline
            with open(f"inline_script_{idx}.js", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"💾 Script salvo em: inline_script_{idx}.js")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ Busca concluída!")
