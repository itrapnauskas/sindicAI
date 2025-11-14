#!/usr/bin/env python3
"""
Testar padrões de URL de download baseado no HTML coletado
Usando os IDs extraídos: solicitacao + cnpj_hash
"""

import requests
from pathlib import Path
import urllib3

# Desabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# IDs extraídos do HTML que o usuário enviou
test_cases = [
    {"solicitacao": "MR025608/2025", "cnpj": "02866338000156"},  # Último do HTML
    {"solicitacao": "MR029108/2024", "cnpj": "04582300000187"},  # Primeiro do HTML
    {"solicitacao": "MR017870/2025", "cnpj": "34709501000163"},  # Segundo do HTML
]

print("🔍 TESTANDO PADRÕES DE URL DE DOWNLOAD")
print("="*70)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo",
    "Accept": "application/pdf,*/*",
})

for idx, test in enumerate(test_cases, 1):
    sol = test["solicitacao"]
    cnpj = test["cnpj"]

    print(f"\n{'='*70}")
    print(f"TESTE {idx}: {sol} / {cnpj}")
    print('='*70)

    # Padrões de URL para testar
    url_patterns = [
        # Padrão 1: Query string
        f"https://www3.mte.gov.br/sistemas/mediador/Download?solicitacao={sol}&cnpj={cnpj}",

        # Padrão 2: DownloadInstrumento
        f"https://www3.mte.gov.br/sistemas/mediador/DownloadInstrumento?solicitacao={sol}&cnpj={cnpj}",

        # Padrão 3: Path-based
        f"https://www3.mte.gov.br/sistemas/mediador/Download/{sol}/{cnpj}",

        # Padrão 4: Lowercase download
        f"https://www3.mte.gov.br/sistemas/mediador/download?solicitacao={sol}&cnpj={cnpj}",

        # Padrão 5: Com ID
        f"https://www3.mte.gov.br/sistemas/mediador/Download?id={sol}&cnpj={cnpj}",

        # Padrão 6: Download/arquivo
        f"https://www3.mte.gov.br/sistemas/mediador/Download/arquivo?solicitacao={sol}&cnpj={cnpj}",

        # Padrão 7: API style
        f"https://www3.mte.gov.br/sistemas/mediador/api/Download?solicitacao={sol}&cnpj={cnpj}",
    ]

    for i, url in enumerate(url_patterns, 1):
        print(f"\n[{i}] Testando: {url}")
        try:
            response = session.get(url, timeout=15, allow_redirects=True, verify=False)
            status = response.status_code
            content_type = response.headers.get('Content-Type', 'N/A')
            content_length = response.headers.get('Content-Length', 'N/A')

            print(f"    Status: {status}")
            print(f"    Content-Type: {content_type}")
            print(f"    Content-Length: {content_length}")

            if status == 200:
                # Verificar se é realmente PDF
                is_pdf = content_type == 'application/pdf' or response.content[:4] == b'%PDF'

                if is_pdf:
                    print(f"    ✅ ✅ ✅ FUNCIONA! É UM PDF! ✅ ✅ ✅")

                    # Salvar PDF
                    pdf_path = Path(__file__).parent / f"test_download_{idx}.pdf"
                    pdf_path.write_bytes(response.content)
                    size_kb = len(response.content) / 1024
                    print(f"    💾 Salvo em: {pdf_path}")
                    print(f"    📊 Tamanho: {size_kb:.2f} KB")

                    print(f"\n🎉 🎉 🎉 PADRÃO DE URL ENCONTRADO! 🎉 🎉 🎉")
                    print(f"\n📋 URL PATTERN:")
                    print(f"    {url}")

                    # Salvar padrão em arquivo
                    pattern_file = Path(__file__).parent / "FOUND_PDF_URL_PATTERN.txt"
                    with open(pattern_file, "w") as f:
                        f.write(f"PADRÃO ENCONTRADO:\n")
                        f.write(f"{url}\n\n")
                        f.write(f"Template:\n")
                        f.write(url.replace(sol, "{solicitacao}").replace(cnpj, "{cnpj}") + "\n")
                    print(f"    💾 Padrão salvo em: {pattern_file}")

                    # Não precisa testar mais
                    exit(0)
                else:
                    print(f"    ⚠️  Status 200 mas não é PDF (content-type ou header)")
                    # Salvar primeiros bytes para debug
                    print(f"    Primeiros 50 bytes: {response.content[:50]}")

            elif status == 404:
                print(f"    ❌ Não encontrado (404)")
            elif status == 403:
                print(f"    🚫 Proibido (403)")
            elif status == 302 or status == 301:
                print(f"    🔀 Redirect para: {response.headers.get('Location', 'N/A')}")
            else:
                print(f"    ⚠️  Código inesperado: {status}")

        except requests.Timeout:
            print(f"    ⏱️  Timeout")
        except requests.ConnectionError as e:
            print(f"    ❌ Erro de conexão: {e}")
        except Exception as e:
            print(f"    ❌ Erro: {e}")

print("\n" + "="*70)
print("❌ Nenhum padrão funcionou")
print("="*70)
