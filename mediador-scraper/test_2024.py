#!/usr/bin/env python3
"""
Teste rápido: buscar ACT do Acre em 2024
Para validar se o scraper está funcionando com ano que tem dados
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from mediador.scraper_playwright import worker_playwright
from mediador.config import human_time
import os

# Forçar ano 2024 para teste
os.environ["ANO_INICIO"] = "2024"

print(f"[{human_time()}] 🔥 TESTE RÁPIDO: AC-ACT 2024")
print(f"[{human_time()}] Este ano DEVE ter dados!\n")

try:
    worker_playwright("AC", "2")  # AC = Acre, 2 = ACT
    print(f"\n[{human_time()}] ✅ Teste concluído!")
except Exception as e:
    print(f"\n[{human_time()}] ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
