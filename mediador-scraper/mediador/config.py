"""
Configurações do Mediador Scraper
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env se existir
load_dotenv()

# URL base do Sistema Mediador
BASE_URL = "https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo"

# Diretório raiz para salvar dados brutos
DATA_ROOT = Path(os.getenv("DATA_ROOT", "./data/raw/mediador")).resolve()

# Todas as 27 UFs do Brasil
UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]

# Tipos de instrumento coletivo
# Mapeamento: código numérico → sigla legível
TIPOS = {
    "1": "CCT",      # Convenção Coletiva de Trabalho
    "2": "ACT",      # Acordo Coletivo de Trabalho
    "3": "ADITIVO"   # Termo Aditivo
}

# Configurações de scraping
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "1.0"))  # segundos entre requests

# Período de coleta
DATA_INICIO = os.getenv("DATA_INICIO", "01/01/2010")
# DATA_FIM é sempre a data atual (calculada dinamicamente no scraper)

# Configurações de retry
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 4, 8]  # segundos de espera entre retries

# Configurações do browser
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
TIMEOUT = 120  # segundos (para PDFs grandes)

# User-Agent
USER_AGENT = "Mozilla/5.0 (Linux 3.10) sis-sindical/1.0"
