#!/usr/bin/env python3
"""
Corrige os PDFs usando a página de Resumo do Sistema Mediador

Estratégia:
1. Lê todos os metadata.json existentes
2. Para cada um, acessa: https://www3.mte.gov.br/sistemas/mediador/Resumo/ResumoVisualiza?nrSolicitacao=MR...
3. Extrai o link do PDF (imagemAnexo) do HTML
4. Baixa o PDF real
5. Substitui o arquivo instrumento.pdf
"""

import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import time
import hashlib

def sha256(data: bytes) -> str:
    """Calcula SHA256"""
    return hashlib.sha256(data).hexdigest()

def extrair_link_pdf(html: str) -> str | None:
    """Extrai link do PDF da página de resumo"""
    soup = BeautifulSoup(html, 'html.parser')

    # Procurar por link que contém 'imagemAnexo'
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if 'imagemAnexo' in href and '.pdf' in href.lower():
            # Se for relativo, completar
            if href.startswith('http'):
                return href
            else:
                return f"https://www3.mte.gov.br{href}"

    return None

def baixar_pdf_real(num_solicitacao: str, timeout: int = 30) -> tuple[bytes | None, str | None]:
    """
    Baixa PDF real acessando página de resumo

    Returns:
        (pdf_bytes, pdf_hash) ou (None, None) se falhar
    """
    try:
        # URL da página de resumo
        url_resumo = f"https://www3.mte.gov.br/sistemas/mediador/Resumo/ResumoVisualiza?nrSolicitacao={num_solicitacao}"

        # Acessar página de resumo
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        resp = session.get(url_resumo, timeout=timeout)
        resp.raise_for_status()

        # Extrair link do PDF
        link_pdf = extrair_link_pdf(resp.text)

        if not link_pdf:
            print(f"    ⚠️  Link do PDF não encontrado no resumo")
            return None, None

        print(f"    🔗 PDF: {link_pdf}")

        # Baixar PDF
        resp_pdf = session.get(link_pdf, timeout=timeout)
        resp_pdf.raise_for_status()

        # Verificar se é realmente PDF
        pdf_bytes = resp_pdf.content
        if not pdf_bytes.startswith(b'%PDF'):
            print(f"    ⚠️  Arquivo baixado não é PDF válido!")
            return None, None

        pdf_hash = sha256(pdf_bytes)

        return pdf_bytes, pdf_hash

    except requests.Timeout:
        print(f"    ⏰ Timeout ao acessar resumo/PDF")
        return None, None
    except requests.RequestException as e:
        print(f"    ❌ Erro HTTP: {e}")
        return None, None
    except Exception as e:
        print(f"    ❌ Erro: {e}")
        return None, None

def main():
    print("🔧 CORRIGINDO PDFs USANDO PÁGINA DE RESUMO")
    print("=" * 70)

    # Encontrar todos os metadata.json
    data_root = Path("data/raw/mediador")
    metadatas = list(data_root.glob("**/metadata.json"))

    print(f"\n📊 Total de instrumentos: {len(metadatas)}")

    if not metadatas:
        print("❌ Nenhum metadata.json encontrado!")
        return

    # Estatísticas
    stats = {
        'total': len(metadatas),
        'sucesso': 0,
        'falha': 0,
        'sem_solicitacao': 0,
        'ja_correto': 0
    }

    for i, meta_path in enumerate(metadatas, 1):
        # Ler metadata
        with open(meta_path) as f:
            meta = json.load(f)

        id_mediador = meta.get('id_mediador', 'DESCONHECIDO')
        num_solicitacao = meta.get('num_solicitacao', '')

        print(f"\n[{i}/{len(metadatas)}] {id_mediador}")

        if not num_solicitacao:
            print(f"    ⚠️  Sem num_solicitacao no metadata")
            stats['sem_solicitacao'] += 1
            continue

        # Verificar se PDF já existe e é válido
        pdf_path = meta_path.parent / "instrumento.pdf"
        if pdf_path.exists():
            with open(pdf_path, 'rb') as f:
                first_bytes = f.read(10)
            if first_bytes.startswith(b'%PDF'):
                print(f"    ✅ PDF já correto, pulando...")
                stats['ja_correto'] += 1
                continue

        # Baixar PDF real
        pdf_bytes, pdf_hash = baixar_pdf_real(num_solicitacao)

        if pdf_bytes:
            # Salvar PDF
            pdf_path.write_bytes(pdf_bytes)

            # Salvar hash
            hash_path = meta_path.parent / "instrumento.sha256"
            hash_path.write_text(pdf_hash)

            print(f"    ✅ PDF baixado e salvo ({len(pdf_bytes) / 1024:.1f} KB)")
            stats['sucesso'] += 1
        else:
            print(f"    ❌ Falha ao baixar PDF")
            stats['falha'] += 1

        # Rate limiting: 1 req/s
        time.sleep(1)

    # Relatório final
    print("\n" + "=" * 70)
    print("📊 RELATÓRIO FINAL")
    print("=" * 70)
    print(f"Total de instrumentos: {stats['total']}")
    print(f"✅ PDFs baixados com sucesso: {stats['sucesso']}")
    print(f"✅ PDFs já corretos (pulados): {stats['ja_correto']}")
    print(f"⚠️  Sem num_solicitacao: {stats['sem_solicitacao']}")
    print(f"❌ Falhas: {stats['falha']}")
    print("\n✅ PROCESSO CONCLUÍDO!")

if __name__ == "__main__":
    main()
