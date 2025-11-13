# Requisitos de Ambiente - Mediador Scraper

## ⚠️ Importante: Restrições de Rede

O scraper do **sindicAI** precisa de **acesso irrestrito à internet** para funcionar corretamente.

### Requ isitos de Rede

#### ✅ Acessos Necessários

1. **Site do Mediador (MTE)**
   - URL: `https://www3.mte.gov.br/sistemas/mediador/*`
   - Porta: 443 (HTTPS)
   - Protocolo: HTTP/2

2. **Download do Playwright Chromium**
   - URLs:
     - `https://playwright.azureedge.net/`
     - `https://playwright-akamai.azureedge.net/`
     - `https://playwright-verizon.azureedge.net/`
   - Tamanho: ~300 MB (download único)

#### ❌ Ambientes que NÃO funcionam

- Redes corporativas com proxy/firewall restritivo
- Ambientes sandbox (como alguns ambientes Cloud IDE)
- VPNs que bloqueiam Azure CDN
- Ambientes com whitelist de domínios

---

## 🖥️ Ambientes Recomendados

### Opção 1: Máquina Local (Recomendado)

**Ubuntu/Debian**:
```bash
# 1. Instalar Python 3.10+
sudo apt update
sudo apt install python3 python3-pip

# 2. Clonar repositório
git clone <repo-url>
cd sindicAI/mediador-scraper

# 3. Instalar dependências
pip3 install -r requirements.txt
python3 -m playwright install chromium

# 4. Rodar teste
python3 test_acre_playwright.py
```

**macOS**:
```bash
# 1. Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python
brew install python@3.11

# 3. Clone e setup (igual Ubuntu)
git clone <repo-url>
cd sindicAI/mediador-scraper
pip3 install -r requirements.txt
python3 -m playwright install chromium

# 4. Rodar
python3 test_acre_playwright.py
```

**Windows**:
```powershell
# 1. Instalar Python 3.10+ de python.org

# 2. Clone e setup
git clone <repo-url>
cd sindicAI\mediador-scraper
pip install -r requirements.txt
python -m playwright install chromium

# 3. Rodar
python test_acre_playwright.py
```

---

### Opção 2: VPS/Cloud (Produção)

Recomendado para coleta completa (300 GB):

**AWS EC2**:
```bash
# Instância recomendada: t3.xlarge (4 vCPU, 16 GB RAM)
# Storage: 500 GB EBS (gp3)
# Sistema: Ubuntu 22.04 LTS

# Setup
sudo apt update && sudo apt install -y python3 python3-pip git tmux
git clone <repo-url>
cd sindicAI/mediador-scraper
pip3 install -r requirements.txt
python3 -m playwright install chromium --with-deps

# Rodar em background
tmux new -s mediador
python3 mediador/scraper_playwright.py
# Ctrl+B, D para detach
```

**Digital Ocean / Linode / Vultr**:
- Similar ao AWS
- Droplet/VM: 4 GB RAM mínimo, 8 GB recomendado
- Storage: 500 GB

**Google Cloud Compute Engine**:
- e2-standard-4 (4 vCPU, 16 GB)
- Debian 11 ou Ubuntu 22.04

---

### Opção 3: Docker (Portável)

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install chromium --with-deps

COPY . .

CMD ["python", "test_acre_playwright.py"]
```

```bash
# Build e run
docker build -t sindic-ai-scraper .
docker run -v $(pwd)/data:/app/data sindic-ai-scraper
```

---

## 🔧 Troubleshooting

### Erro: "403 Forbidden" ao acessar Mediador

**Causa**: Rede bloqueada, IP brasileiro necessário, ou site fora do ar.

**Solução**:
1. Verificar se site está no ar: `curl -I https://www3.mte.gov.br`
2. Testar de outra rede (celular, VPN)
3. Usar VPS brasileiro (AWS São Paulo, etc.)

### Erro: "Failed to download Chromium"

**Causa**: Firewall bloqueando Azure CDN.

**Solução**:
1. Liberar domínios:
   - `*.azureedge.net`
   - `playwright.azureedge.net`
2. Ou baixar manualmente:
   ```bash
   wget https://playwright.azureedge.net/builds/chromium/1140/chromium-linux.zip
   unzip chromium-linux.zip -d ~/.cache/ms-playwright/chromium-1140/
   ```

### Erro: "Connection timeout"

**Causa**: Rede lenta ou instável.

**Solução**:
1. Aumentar timeout em `config.py`:
   ```python
   TIMEOUT = 300  # 5 minutos
   ```
2. Reduzir workers:
   ```python
   MAX_WORKERS = 2
   ```

### Disco cheio

**Causa**: ~300 GB necessários para base completa.

**Solução**:
1. Monitorar espaço: `df -h`
2. Coletar por UF e mover para S3:
   ```bash
   aws s3 sync data/raw/mediador/ s3://bucket/mediador/
   rm -rf data/raw/mediador/SC/  # Limpar após sync
   ```

---

## 📊 Recursos Necessários

| Componente | Mínimo | Recomendado | Produção |
|------------|--------|-------------|----------|
| **CPU** | 2 cores | 4 cores | 8 cores |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Disco** | 50 GB | 100 GB | 500 GB |
| **Rede** | 10 Mbps | 50 Mbps | 100 Mbps |
| **SO** | Linux/macOS/Windows | Ubuntu 22.04 | Ubuntu 22.04 LTS |

---

## ✅ Checklist Pré-Execução

Antes de rodar o scraper massivo, verifique:

- [ ] Python 3.10+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Playwright Chromium baixado (`python -m playwright install chromium`)
- [ ] Acesso ao site do Mediador (`curl https://www3.mte.gov.br/sistemas/mediador/`)
- [ ] Espaço em disco suficiente (500 GB livres)
- [ ] Conexão estável (teste com speedtest)
- [ ] tmux instalado (para sessão persistente)

---

## 🚀 Próximos Passos

Após validar o ambiente:

1. **Teste pequeno**: `python test_acre_playwright.py` (1 UF)
2. **Validar dados**: verificar `data/raw/mediador/AC/`
3. **Coleta completa**: `python mediador/scraper_playwright.py` (27 UFs)
4. **Monitorar**: logs em tempo real
5. **Backup**: sync periódico para S3/cloud

---

**Última atualização**: 2025-11-13
