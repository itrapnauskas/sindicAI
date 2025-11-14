#!/usr/bin/env python3
"""
Analisa os HTMLs já salvos para encontrar o link do PDF
"""

from pathlib import Path
from bs4 import BeautifulSoup
import re

print("🔍 ANALISANDO HTMLs JÁ SALVOS")
print("=" * 70)

# Pegar primeiro HTML salvo
data_root = Path("data/raw/mediador")
htmls = list(data_root.glob("**/instrumento.html"))

print(f"\n📊 Total de HTMLs: {len(htmls)}")

if not htmls:
    print("❌ Nenhum HTML encontrado!")
    exit(1)

# Analisar primeiro HTML
html_path = htmls[0]
print(f"\n📄 Analisando: {html_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

print(f"📏 Tamanho: {len(html):,} bytes")

# Procurar por padrões
patterns = [
    r'imagemAnexo',
    r'\.pdf',
    r'MR\d+',
    r'http[s]?://[^\s"\'<>]+\.pdf',
    r'fDownload',
    r'download',
]

print("\n🔍 BUSCANDO PADRÕES:")
for pattern in patterns:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"\n✅ Padrão '{pattern}' encontrado:")
        for match in matches[:5]:  # Primeiras 5 ocorrências
            print(f"   - {match}")
    else:
        print(f"\n❌ Padrão '{pattern}' NÃO encontrado")

# Procurar links <a>
print("\n\n🔗 ANALISANDO LINKS <a>:")
soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=True)

print(f"Total de links: {len(links)}")

for i, link in enumerate(links[:10]):  # Primeiros 10
    print(f"\n[{i+1}] href: {link.get('href', '')[:100]}")
    if link.get('onclick'):
        print(f"    onclick: {link.get('onclick')}")
    print(f"    texto: {link.get_text(strip=True)[:50]}")

# Procurar por tags específicas
print("\n\n📋 TODAS AS TAGS COM 'pdf' (case insensitive):")
for tag in soup.find_all():
    tag_str = str(tag)
    if 'pdf' in tag_str.lower():
        print(f"\n{tag.name}: {tag_str[:200]}...")
        break  # Só primeira

print("\n\n💡 SALVANDO HTML COMPLETO PARA INSPEÇÃO MANUAL:")
output = Path("primeiro_html_analise.html")
output.write_text(html, encoding='utf-8')
print(f"✅ Salvo em: {output}")
print("\n📝 Abra esse arquivo no navegador ou VS Code e procure por:")
print("   - 'imagemAnexo'")
print("   - 'download'")
print("   - '.pdf'")
print("   - O num_solicitacao do metadata (ex: MR031724)")
