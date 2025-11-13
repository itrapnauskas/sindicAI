#!/usr/bin/env python3
"""
Teste com Playwright: coletar dados do ACRE (AC)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mediador.scraper_playwright import worker_playwright, TIPOS, ensure_dir, DATA_ROOT, human_time

def main():
    print(f"[{human_time()}] 🔥 TESTE ACRE (AC) - COM PLAYWRIGHT")
    print(f"[{human_time()}] 📊 Vamos baixar:")
    print(f"           - CCT (Convenções Coletivas)")
    print(f"           - ACT (Acordos Coletivos)")
    print(f"           - ADITIVOS (Termos Aditivos)")
    print(f"[{human_time()}] 💾 Destino: {DATA_ROOT}/AC")
    print(f"[{human_time()}] 🌐 Usando browser real (Chromium)")
    print()

    ensure_dir(DATA_ROOT)

    # Rodar para cada tipo
    for tipo_codigo, tipo_nome in TIPOS.items():
        print(f"[{human_time()}] {'='*60}")
        print(f"[{human_time()}] Iniciando: AC - {tipo_nome}")
        print(f"[{human_time()}] {'='*60}")
        try:
            worker_playwright("AC", tipo_codigo)
        except Exception as e:
            print(f"[{human_time()}] ❌ Erro ao coletar AC-{tipo_nome}: {e}")
            import traceback
            traceback.print_exc()
        print()

    print(f"[{human_time()}] ✅ TESTE DO ACRE FINALIZADO!")
    print(f"[{human_time()}] 📁 Verifique os dados em: {DATA_ROOT}/AC")

if __name__ == "__main__":
    main()
