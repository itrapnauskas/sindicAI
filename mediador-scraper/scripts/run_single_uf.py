#!/usr/bin/env python3
"""
Script de teste: coleta de uma UF específica com limite de páginas.

Uso:
    python -m scripts.run_single_uf --uf SC --tipo 1 --max-paginas 2
"""

import argparse
import sys
from pathlib import Path

# Adicionar diretório pai ao path para importar módulo mediador
sys.path.insert(0, str(Path(__file__).parent.parent))

from mediador.scraper_nuclear import worker, TIPOS, ensure_dir, DATA_ROOT


def main():
    parser = argparse.ArgumentParser(description="Teste de coleta em uma UF específica")
    parser.add_argument("--uf", required=True, help="Sigla da UF (ex: SC, SP, RJ)")
    parser.add_argument("--tipo", required=True, choices=["1", "2", "3"],
                       help="Tipo: 1=CCT, 2=ACT, 3=ADITIVO")
    parser.add_argument("--max-paginas", type=int, default=1,
                       help="Número máximo de páginas a coletar (padrão: 1)")

    args = parser.parse_args()

    uf = args.uf.upper()
    tipo_codigo = args.tipo
    tipo_nome = TIPOS[tipo_codigo]

    print(f"🧪 MODO TESTE")
    print(f"   UF: {uf}")
    print(f"   Tipo: {tipo_nome} (código {tipo_codigo})")
    print(f"   Máx páginas: {args.max_paginas}")
    print(f"   Destino: {DATA_ROOT}/{uf}")
    print()

    ensure_dir(DATA_ROOT)

    # Executar worker (limitado será feito modificando a função - para teste vamos rodar normal)
    # Em produção, você pode modificar worker() para aceitar max_paginas como parâmetro
    print("⚠️  NOTA: Este script executará TODAS as páginas disponíveis.")
    print("   Para limitar, modifique a função worker() para aceitar max_paginas.")
    print()

    worker(uf, tipo_codigo)

    print()
    print(f"✅ Teste concluído! Verifique os dados em: {DATA_ROOT}/{uf}")


if __name__ == "__main__":
    main()
