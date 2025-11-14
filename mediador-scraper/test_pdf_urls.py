#!/usr/bin/env python3
"""
Testar diferentes padrões de URL para download de PDFs
Usando os IDs que extraímos do HTML
"""

import requests
from pathlib import Path

# Parâmetros extraídos do HTML
solicitacao = "MR035988/2025"
cnpj = "02742202000134"

# Possíveis padrões de URL
url_patterns = [
    f"https://www3.mte.gov.br/sistemas/mediador/download/{solicitacao}/{cnpj}",
    f"https://www3.mte.gov.br/sistemas/mediador/Download/{solicitacao}/{cnpj}",
    f"https://www3.mte.gov.br/sistemas/mediador/pdf/{solicitacao}/{cnpj}",
    f"https://www3.mte.gov.br/sistemas/mediador/arquivo/{solicitacao}/{cnpj}",
    f"https://www3.mte.gov.br/sistemas/mediador/Download?id={solicitacao}&cnpj={cnpj}",
    f"https://www3.mte.gov.br/sistemas/mediador/download?solicitacao={solicitacao}&cnpj={cnpj}",
]

print(f"🔍 Testando URLs para: {solicitacao} / {cnpj}")
print("="*70)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

for i, url in enumerate(url_patterns, 1):
    print(f"\n[{i}] Testando: {url}")
    try:
        response = session.head(url, timeout=10, allow_redirects=True)
        print(f"    Status: {response.status_code}")

        if response.status_code == 200:
            print(f"    ✅ FUNCIONA!")
            print(f"    Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"    Content-Length: {response.headers.get('Content-Length', 'N/A')} bytes")

            # Tentar baixar
            print(f"    📥 Baixando...")
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                pdf_path = Path(__file__).parent / "test_downloaded.pdf"
                pdf_path.write_bytes(response.content)
                print(f"    💾 Salvo em: {pdf_path}")
                print(f"    📊 Tamanho: {len(response.content) / 1024:.2f} KB")
                print(f"\n🎉 PADRÃO DE URL ENCONTRADO: {url}")
                break
        elif response.status_code == 404:
            print(f"    ❌ Não encontrado (404)")
        elif response.status_code == 403:
            print(f"    🚫 Proibido (403)")
        else:
            print(f"    ⚠️  Código inesperado")

    except requests.Timeout:
        print(f"    ⏱️  Timeout")
    except requests.RequestException as e:
        print(f"    ❌ Erro: {e}")

print("\n" + "="*70)
print("✅ Teste concluído!")
