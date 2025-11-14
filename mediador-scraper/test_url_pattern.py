#!/usr/bin/env python3
"""
Testa se conseguimos adivinhar URLs de PDF baseado no padrão descoberto
"""

import requests
import json
from pathlib import Path

print("🧪 TESTANDO PADRÃO DE URLs DE PDF")
print("=" * 70)

# Padrão descoberto pelo dev:
# https://www3.mte.gov.br/sistemas/mediador/imagemAnexo/MR005307_20252025_01_31T17_48_02.pdf

# URLs conhecidas (do CSV do dev)
known_urls = [
    "https://www3.mte.gov.br/sistemas/mediador/imagemAnexo/MR005307_20252025_01_31T17_48_02.pdf",
    "https://www3.mte.gov.br/sistemas/mediador/imagemAnexo/MR005708_20252025_01_31T17_48_02.pdf",
    "https://www3.mte.gov.br/sistemas/mediador/imagemAnexo/MR037839_20252025_06_30T12_52_30.pdf",
]

# Pegar metadados que temos
data_root = Path("data/raw/mediador")
metadatas = list(data_root.glob("**/metadata.json"))

print(f"\n📊 Total de metadados: {len(metadatas)}")

if not metadatas:
    print("❌ Nenhum metadata encontrado!")
    exit(1)

# Testar primeiro metadata
meta_path = metadatas[0]
with open(meta_path) as f:
    meta = json.load(f)

num_solicitacao = meta.get('num_solicitacao', '')
ano = meta.get('ano', '')
id_mediador = meta.get('id_mediador', '')

print(f"\n📄 Testando: {id_mediador}")
print(f"   num_solicitacao: {num_solicitacao}")
print(f"   ano: {ano}")

# Tentar diferentes padrões de timestamp
# Observação: maioria usa 01_31T17_48_02, alguns usam 06_30T12_52_30
timestamps_comuns = [
    f"{ano}{ano}_01_31T17_48_02",  # Mais comum
    f"{ano}{ano}_06_30T12_52_30",  # Alternativo
    f"{ano}{ano}_12_31T23_59_59",  # Fim de ano
    f"{ano}{ano}_01_01T00_00_00",  # Início de ano
]

# Remover / do num_solicitacao
num_clean = num_solicitacao.replace('/', '')

print(f"\n🔍 Tentando {len(timestamps_comuns)} timestamps diferentes...")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

for i, timestamp in enumerate(timestamps_comuns, 1):
    url = f"https://www3.mte.gov.br/sistemas/mediador/imagemAnexo/{num_clean}_{timestamp}.pdf"

    print(f"\n[{i}/{len(timestamps_comuns)}] Testando:")
    print(f"   {url}")

    try:
        resp = session.head(url, timeout=10, allow_redirects=True)
        print(f"   Status: {resp.status_code}")

        if resp.status_code == 200:
            print(f"   ✅ ENCONTRADO!")
            print(f"   Content-Type: {resp.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {resp.headers.get('content-length', 'N/A')} bytes")

            # Baixar PDF
            resp_full = session.get(url, timeout=30)
            if resp_full.content.startswith(b'%PDF'):
                Path("teste_url_pattern.pdf").write_bytes(resp_full.content)
                print(f"   ✅ PDF VÁLIDO salvo em: teste_url_pattern.pdf")
                break
            else:
                print(f"   ⚠️  Não é PDF válido!")
        else:
            print(f"   ❌ Não encontrado")

    except requests.Timeout:
        print(f"   ⏰ Timeout")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

print("\n" + "=" * 70)
print("💡 CONCLUSÃO:")
print("   Se encontrou PDF: podemos usar força bruta com timestamps comuns")
print("   Se NÃO encontrou: precisamos do método do dev para descobrir timestamp exato")
print("\n👉 PERGUNTE AO SEU DEV: Como ele descobriu os timestamps?")
