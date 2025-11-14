#!/usr/bin/env python3
"""
Scraper com Playwright - Versão que coleta ANO POR ANO

IMPORTANTE: O site limita pesquisas a 2 anos!
Por isso fazemos um loop por ano (01/01/YYYY até 31/12/YYYY)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mediador.scraper_playwright import worker_playwright, TIPOS, ensure_dir, DATA_ROOT, human_time
from mediador.config import ANO_INICIO, ANO_FIM

def main():
    UF = "AC"
    print(f"[{human_time()}] 🔥 TESTE ACRE (AC) - ANO POR ANO")
    print(f"[{human_time()}] 📊 Período: {ANO_INICIO} até {ANO_FIM}")
    print(f"[{human_time()}] 💾 Destino: {DATA_ROOT}/AC")
    print()

    ensure_dir(DATA_ROOT)

    # Testar com ACT (index 1)
    tipo_codigo = "2"  # ACT
    tipo_nome = TIPOS[tipo_codigo]

    print(f"[{human_time()}] {'='*60}")
    print(f"[{human_time()}] Testando: AC - {tipo_nome}")
    print(f"[{human_time()}] {'='*60}")

    try:
        worker_playwright(UF, tipo_codigo)
    except Exception as e:
        print(f"[{human_time()}] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    print()
    print(f"[{human_time()}] ✅ TESTE FINALIZADO!")
    print(f"[{human_time()}] 📁 Verifique: {DATA_ROOT}/AC")

if __name__ == "__main__":
    main()
