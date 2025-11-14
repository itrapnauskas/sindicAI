#!/usr/bin/env python3
"""
Baixa PDFs acessando página de Resumo (método do dev!)
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
from urllib.parse import quote

print("📥 BAIXANDO PDFs VIA PÁGINA DE RESUMO")
print("=" * 70)

BASE_URL = "https://www3.mte.gov.br/sistemas/mediador"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def obter_link_pdf(num_solicitacao: str, debug=False) -> str | None:
    """
    Acessa página de resumo e extrai link do PDF

    Testa múltiplas variações de URL até encontrar a correta
    """
    # Testar diferentes formatos de URL
    urls_to_try = [
        # Formato 1: Com encoding
        f"{BASE_URL}/Resumo/ResumoVisualiza?nrSolicitacao={quote(num_solicitacao, safe='')}",
        # Formato 2: Sem encoding (como dev faz)
        f"{BASE_URL}/Resumo/ResumoVisualiza?nrSolicitacao={num_solicitacao}",
        # Formato 3: Path param ao invés de query
        f"{BASE_URL}/Resumo/ResumoVisualiza/{num_solicitacao}",
        # Formato 4: Outro endpoint possível
        f"{BASE_URL}/ResumoVisualiza?nrSolicitacao={num_solicitacao}",
    ]

    print(f"\n🔍 Acessando resumo: {num_solicitacao}")

    session = requests.Session()
    session.headers.update(HEADERS)

    for i, url_resumo in enumerate(urls_to_try, 1):
        try:
            print(f"   Tentativa {i}/{len(urls_to_try)}: {url_resumo}")
            r = session.get(url_resumo, timeout=30)
            print(f"   Status: {r.status_code}")

            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')

                # Procurar link com texto "Anexo (PDF)" ou contendo "imagemAnexo"
                # Método 1: Por texto
                link = soup.find('a', href=True, string=lambda s: s and 'PDF' in s.upper())

                if not link:
                    # Método 2: Por href contendo imagemAnexo
                    link = soup.find('a', href=lambda h: h and 'imagemAnexo' in h)

                if link:
                    href = link['href']
                    # Se for relativo, completar
                    if href.startswith('http'):
                        pdf_url = href
                    else:
                        pdf_url = f"https://www3.mte.gov.br{href}"

                    print(f"   ✅ PDF encontrado: {pdf_url}")
                    return pdf_url
                else:
                    print(f"   ⚠️  Link do PDF não encontrado no HTML")
                    # Salvar HTML para debug apenas no primeiro 200
                    debug_file = Path(f"debug_resumo_{num_solicitacao.replace('/', '_')}.html")
                    debug_file.write_text(r.text, encoding='utf-8')
                    print(f"   💾 HTML salvo em: {debug_file}")
                    # Continuar tentando outras URLs
            else:
                # Não é 200, tentar próxima URL
                continue

        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
            continue

    # Nenhuma URL funcionou
    print(f"   ❌ Nenhuma URL de resumo funcionou")
    return None

# Ler metadados existentes
data_root = Path("data/raw/mediador")
metadatas = list(data_root.glob("**/metadata.json"))

print(f"\n📊 Total de metadados: {len(metadatas)}")

if not metadatas:
    print("❌ Nenhum metadata encontrado!")
    exit(1)

# Testar com primeiros 3 metadados
stats = {'sucesso': 0, 'falha': 0, 'sem_solicitacao': 0}

for i, meta_path in enumerate(metadatas[:3], 1):
    with open(meta_path) as f:
        meta = json.load(f)

    id_mediador = meta.get('id_mediador', 'DESCONHECIDO')
    num_solicitacao = meta.get('num_solicitacao', '')

    print(f"\n{'='*70}")
    print(f"[{i}/3] {id_mediador}")

    if not num_solicitacao:
        print("   ⚠️  Sem num_solicitacao")
        stats['sem_solicitacao'] += 1
        continue

    # Obter link do PDF
    pdf_url = obter_link_pdf(num_solicitacao)

    if pdf_url:
        # Baixar PDF
        try:
            print(f"\n   📥 Baixando PDF...")
            r = requests.get(pdf_url, headers=HEADERS, timeout=30)

            if r.status_code == 200:
                pdf_bytes = r.content

                # Verificar se é PDF
                if pdf_bytes.startswith(b'%PDF'):
                    # Salvar
                    pdf_path = meta_path.parent / "instrumento.pdf"
                    pdf_path.write_bytes(pdf_bytes)
                    print(f"   ✅ PDF salvo ({len(pdf_bytes) / 1024:.1f} KB): {pdf_path}")
                    stats['sucesso'] += 1
                else:
                    print(f"   ⚠️  Arquivo baixado não é PDF válido!")
                    stats['falha'] += 1
            else:
                print(f"   ❌ Erro ao baixar: {r.status_code}")
                stats['falha'] += 1

        except Exception as e:
            print(f"   ❌ Erro ao baixar PDF: {e}")
            stats['falha'] += 1
    else:
        stats['falha'] += 1

    # Rate limiting
    time.sleep(1)

print("\n" + "=" * 70)
print("📊 ESTATÍSTICAS:")
print(f"   ✅ Sucesso: {stats['sucesso']}")
print(f"   ❌ Falha: {stats['falha']}")
print(f"   ⚠️  Sem solicitação: {stats['sem_solicitacao']}")
print("\n✅ TESTE CONCLUÍDO!")
print("\nSe funcionou, podemos processar todos os 61 metadados!")
