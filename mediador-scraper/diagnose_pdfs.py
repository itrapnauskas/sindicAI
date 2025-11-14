#!/usr/bin/env python3
"""
Diagnosticar os PDFs baixados - descobrir o que realmente está nos arquivos
"""

from pathlib import Path
import json

print("🔍 DIAGNÓSTICO DE PDFs")
print("=" * 70)

# Encontrar todos os PDFs
data_root = Path("data/raw/mediador")
pdfs = list(data_root.glob("**/instrumento.pdf"))

print(f"\n📊 Total de PDFs encontrados: {len(pdfs)}")

if not pdfs:
    print("❌ Nenhum PDF encontrado!")
    exit(1)

# Analisar primeiros 5 PDFs
for i, pdf_path in enumerate(pdfs[:5], 1):
    print(f"\n{'='*70}")
    print(f"PDF {i}: {pdf_path}")
    print('='*70)

    # Tamanho
    size_bytes = pdf_path.stat().st_size
    print(f"📏 Tamanho: {size_bytes:,} bytes ({size_bytes / 1024:.1f} KB)")

    # Ler primeiros 100 bytes
    with open(pdf_path, "rb") as f:
        first_bytes = f.read(100)

    print(f"\n📋 Primeiros 20 bytes (hex):")
    print("   ", first_bytes[:20].hex())

    print(f"\n📋 Primeiros 100 bytes (texto):")
    try:
        print("   ", first_bytes.decode("utf-8", errors="replace")[:100])
    except:
        print("    (não é texto UTF-8)")

    # Verificar assinatura de arquivo
    if first_bytes.startswith(b"%PDF"):
        print("\n✅ ASSINATURA: É um PDF válido! (%PDF)")
    elif first_bytes.startswith(b"<!DOCTYPE") or first_bytes.startswith(b"<html"):
        print("\n❌ ASSINATURA: É HTML, não PDF!")
    elif first_bytes.startswith(b"{"):
        print("\n❌ ASSINATURA: É JSON, não PDF!")
    elif first_bytes.startswith(b"<?xml"):
        print("\n❌ ASSINATURA: É XML, não PDF!")
    else:
        print(f"\n⚠️  ASSINATURA DESCONHECIDA: {first_bytes[:10]}")

    # Ler metadata associado
    metadata_path = pdf_path.parent / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
        print(f"\n📄 Metadados:")
        print(f"   ID: {meta.get('id_mediador', 'N/A')}")
        print(f"   Tipo: {meta.get('tipo', 'N/A')}")
        print(f"   Download IDs: {meta.get('download_ids', {})}")

print("\n" + "="*70)
print("✅ DIAGNÓSTICO CONCLUÍDO")
print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Se ver '%PDF' -> PDFs estão corretos")
print("   2. Se ver HTML/JSON -> download está capturando página de erro")
print("   3. Se assinatura desconhecida -> envie os primeiros bytes")
