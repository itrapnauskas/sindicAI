#!/usr/bin/env python3
"""
Teste rápido: coletar dados do ACRE (AC) - TODAS as páginas, TODOS os tipos
"""

import sys
from pathlib import Path

# Adicionar módulo ao path
sys.path.insert(0, str(Path(__file__).parent))

from mediador.scraper_nuclear import worker, TIPOS, ensure_dir, DATA_ROOT, human_time

def main():
    print(f"[{human_time()}] 🔥 INICIANDO COLETA - ACRE (AC)")
    print(f"[{human_time()}] 📊 Vamos baixar:")
    print(f"           - CCT (Convenções Coletivas)")
    print(f"           - ACT (Acordos Coletivos)")
    print(f"           - ADITIVOS (Termos Aditivos)")
    print(f"[{human_time()}] 💾 Destino: {DATA_ROOT}/AC")
    print()

    ensure_dir(DATA_ROOT)

    # Rodar para cada tipo
    for tipo_codigo, tipo_nome in TIPOS.items():
        print(f"[{human_time()}] {'='*60}")
        print(f"[{human_time()}] Iniciando coleta: AC - {tipo_nome}")
        print(f"[{human_time()}] {'='*60}")
        try:
            worker("AC", tipo_codigo)
        except Exception as e:
            print(f"[{human_time()}] ❌ Erro ao coletar AC-{tipo_nome}: {e}")
        print()

    print(f"[{human_time()}] ✅ COLETA DO ACRE FINALIZADA!")
    print(f"[{human_time()}] 📁 Verifique os dados em: {DATA_ROOT}/AC")

if __name__ == "__main__":
    main()
