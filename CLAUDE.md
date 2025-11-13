# CLAUDE.md - sindicAI

> **Documentação completa do projeto para AI assistants**
> Última atualização: 2025-11-13

---

## 🎯 VISÃO GERAL DO PROJETO

**sindicAI** é um projeto ambicioso para construir a **primeira base de dados nacional completa** com TODAS as convenções coletivas, acordos coletivos de trabalho (ACT) e termos aditivos do Brasil.

### Objetivo Final

Criar uma plataforma que permita:
- 📥 **Coleta automática** de convenções de TODOS os sindicatos do Brasil
- 💾 **Armazenamento dual**: dados originais (PDFs, HTMLs) + dados estruturados
- 🔍 **Extração inteligente** de cláusulas, pisos salariais, benefícios
- 🤖 **Automatização** do processo de implantação de folha de pagamento
- 🌐 **API nacional** para consulta por CNPJ, CBO, UF, etc.

### Alcance

- ✅ **27 UFs** (todas as unidades federativas)
- ✅ **Todos os sindicatos** cadastrados no Brasil
- ✅ **Todos os tipos**: CCT (Convenção Coletiva), ACT (Acordo Coletivo), Aditivos
- ✅ **Histórico completo** desde 2000 (ou mais antigo se disponível)

---

## 🏗️ ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE COLETA                         │
├─────────────────────────────────────────────────────────────┤
│  1. Sistema Mediador (MTE) ← FASE ATUAL (MVP/Protótipo)   │
│  2. Portais dos Sindicatos (scraping individual)           │
│  3. APIs públicas (quando disponíveis)                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                 CAMADA DE ARMAZENAMENTO RAW                 │
├─────────────────────────────────────────────────────────────┤
│  data/raw/mediador/{UF}/{ANO}/{TIPO}/{ID_MEDIADOR}/       │
│    ├── metadata.json     (metadados estruturados)          │
│    ├── instrumento.html  (HTML original)                   │
│    ├── instrumento.pdf   (PDF original)                    │
│    └── instrumento.sha256 (hash para integridade)          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE PROCESSAMENTO (TODO)                 │
├─────────────────────────────────────────────────────────────┤
│  • OCR em PDFs (quando necessário)                         │
│  • Extração de texto estruturado                           │
│  • Parsing de cláusulas específicas                        │
│  • Identificação de: pisos, benefícios, jornadas, etc.    │
│  • Delta Lake: Bronze → Silver → Gold                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE BUSCA E ANÁLISE (TODO)               │
├─────────────────────────────────────────────────────────────┤
│  • Embeddings vetoriais (busca semântica)                  │
│  • Elasticsearch/OpenSearch (busca textual)                │
│  • Query: "pisos salariais > R$2.000 em 2025"             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE API (TODO)                     │
├─────────────────────────────────────────────────────────────┤
│  GET /api/v1/piso/{cnpj}/{cbo}                             │
│  GET /api/v1/convencoes?uf=SP&setor=comercio               │
│  GET /api/v1/clausulas?termo=vale+transporte               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📍 FASE ATUAL: MVP/PROTÓTIPO - MEDIADOR

### O que é o Sistema Mediador?

Portal oficial do Ministério do Trabalho e Emprego (MTE):
- **URL**: https://www3.mte.gov.br/sistemas/mediador/ConsultarInstColetivo
- **Conteúdo**: Base de dados pública de TODOS os instrumentos coletivos registrados
- **Formato**: Interface web com filtros + tabela de resultados + links para PDFs

### Estratégia "Full Burst"

**Objetivo**: Baixar 100% da base do Mediador em modo "2 pés no peito"

**Abordagem**:
1. Loop cartesiano: 27 UFs × 3 tipos × N páginas
2. Paralelismo controlado: 8 workers simultâneos
3. Rate limiting ético: 8 req/s agregado (1 req/s por worker)
4. Retry automático: 3 tentativas com backoff exponencial
5. Checksum SHA-256 para garantir integridade

**Estimativa de volume**:
- ~800.000 PDFs
- ~300 GB de dados brutos
- Tempo estimado: 24-48h de scraping contínuo

### Parâmetros da Consulta

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| `uf` | AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO | 27 UFs |
| `tpInstrumento` | 1=CCT, 2=ACT, 3=Aditivo | Tipo de instrumento |
| `dtRegistroIni` | 01/01/2010 (ou 2000) | Início do período |
| `dtRegistroFim` | Data atual | Fim do período |
| `pagina` | 1...N | Paginação (cada página ~20 linhas) |

---

## 📁 ESTRUTURA DO REPOSITÓRIO

```
sindicAI/
├── README.md                      # Documentação principal do projeto
├── CLAUDE.md                      # Este arquivo (para AI assistants)
│
├── mediador-scraper/              # 🎯 MÓDULO ATUAL - Scraper do Mediador
│   ├── README.md                  # Docs específicas do scraper
│   ├── requirements.txt           # Dependências Python
│   ├── .env.example               # Exemplo de configuração
│   │
│   ├── mediador/                  # Pacote Python principal
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações e constantes
│   │   ├── scraper.py             # Lógica de scraping (Playwright)
│   │   ├── scraper_nuclear.py     # Versão "full burst" multi-thread
│   │   ├── parser.py              # Parsing de HTML/tabelas
│   │   └── storage.py             # Funções para salvar em disco
│   │
│   ├── scripts/                   # Scripts utilitários
│   │   ├── run_single_uf.py       # Teste em uma UF específica
│   │   ├── run_full_burst.py      # Execução completa (todas UFs)
│   │   └── check_integrity.py     # Validação de checksums
│   │
│   └── tests/                     # Testes unitários
│       ├── test_parser.py
│       └── test_storage.py
│
├── data/                          # 💾 DADOS BRUTOS (gitignored)
│   └── raw/
│       └── mediador/
│           └── {UF}/              # Ex: SP, RJ, MG...
│               └── {ANO}/         # Ex: 2024, 2023...
│                   └── {TIPO}/    # CCT, ACT, ADITIVO
│                       └── {ID_MEDIADOR}/
│                           ├── metadata.json
│                           ├── instrumento.html
│                           ├── instrumento.pdf
│                           └── instrumento.sha256
│
├── pipeline/                      # 🔄 PIPELINE DE ETL (TODO - futuro)
│   ├── bronze/                    # Dados brutos → Delta Lake Bronze
│   ├── silver/                    # Limpeza e estruturação
│   └── gold/                      # Agregações e features
│
├── api/                           # 🌐 API REST (TODO - futuro)
│   ├── app/
│   ├── models/
│   └── routes/
│
└── docs/                          # 📚 Documentação adicional
    ├── arquitetura.md
    ├── scraping-guidelines.md
    └── api-spec.yaml
```

---

## 🛠️ STACK TECNOLÓGICO

### Fase Atual (Scraping)

- **Python 3.10+**
- **Playwright** - Automação de browser (headless Chrome)
- **BeautifulSoup4 + lxml** - Parsing de HTML
- **Requests** - HTTP client (para downloads diretos)
- **ThreadPoolExecutor** - Paralelismo controlado

### Futuro (Pipeline e API)

- **Delta Lake / Parquet** - Armazenamento estruturado
- **DuckDB** - Query engine analítico
- **OpenSearch / Elasticsearch** - Busca textual
- **Qdrant / Weaviate** - Vector database (embeddings)
- **FastAPI** - Framework da API REST
- **Docker + Kubernetes** - Deployment

---

## 🚀 COMO RODAR O SCRAPER (MVP ATUAL)

### ⚠️ Requisitos de Ambiente

**IMPORTANTE**: O scraper precisa de **acesso irrestrito à internet**:

- ✅ Acesso a `https://www3.mte.gov.br/sistemas/mediador/*`
- ✅ Acesso a Azure CDN para baixar Chromium
- ✅ 500 GB de espaço em disco (para coleta completa)
- ✅ 4+ GB de RAM, 8 GB recomendado

**Ambientes que NÃO funcionam**:
- ❌ Redes corporativas com firewall restritivo
- ❌ Sandboxes sem acesso externo
- ❌ Ambientes com whitelist de domínios

👉 **Ver detalhes completos**: [mediador-scraper/ENVIRONMENT.md](mediador-scraper/ENVIRONMENT.md)

### Setup Inicial

```bash
# 1. Clonar repositório
git clone <repo-url>
cd sindicAI/mediador-scraper

# 2. Instalar dependências
pip install -r requirements.txt
python -m playwright install chromium --with-deps

# 3. Configurar ambiente (opcional)
cp .env.example .env
# Editar .env se necessário (ex: DATA_ROOT=/mnt/storage/mediador)

# 4. Testar com uma UF (usando Playwright)
python test_acre_playwright.py

# 5. Executar coleta completa (CUIDADO: 300GB!)
tmux new -s mediador
python -m mediador.scraper_playwright
```

### Monitoramento

Logs aparecem em tempo real:
```
[15:42:10] 🚀 SP-CCT iniciado
[15:42:15] ✅ SP-CCT página 1 -> 20 docs
[15:42:22] ✅ SP-CCT página 2 -> 20 docs
...
```

### Parada e Retomada

O scraper é **idempotente**:
- Se interrompido (Ctrl+C), pode retomar de onde parou
- Arquivos já baixados são sobrescritos (mesmo hash)
- Nenhum dado duplicado

---

## 📋 CONVENÇÕES DE DESENVOLVIMENTO

### Estrutura de Dados

#### metadata.json (exemplo)
```json
{
  "id_mediador": "SC123456/2024",
  "uf": "SC",
  "tipo": "CCT",
  "tipo_simplificado": "CCT",
  "ano": "2024",
  "data_registro": "15/03/2024",
  "data_assinatura": "10/03/2024",
  "vigencia_inicio": "01/01/2024",
  "vigencia_fim": "31/12/2024",
  "partes": "SINDICATO DOS COMERCIÁRIOS DE FLORIANÓPOLIS E EMPRESA XYZ LTDA",
  "link_pdf": "https://www3.mte.gov.br/sistemas/mediador/download/12345",
  "fonte": "MEDIADOR",
  "coletado_em": "2025-11-13T15:42:10.123456"
}
```

### Nomenclatura

- **UFs**: SEMPRE em maiúsculas (SP, RJ, MG)
- **Tipos**:
  - Código numérico na consulta: `1`, `2`, `3`
  - Nome legível: `CCT`, `ACT`, `ADITIVO`
- **Datas**: formato `DD/MM/YYYY` (conforme retorna o Mediador)
- **IDs**: formato original do Mediador (ex: `SC123456/2024`)
  - Substituir `/` por `_` em nomes de diretório

### Tratamento de Erros

1. **HTTP 429 (rate limit)**: backoff exponencial 2s, 4s, 8s
2. **HTTP 5xx**: retry até 3 vezes
3. **Timeout**: definir timeout de 120s para PDFs grandes
4. **PDF não disponível**: salvar mesmo assim o metadata.json + HTML
5. **Logging**: SEMPRE logar erro completo + UF + tipo + página

### Git Workflow

- Branch principal: `main`
- Branch de desenvolvimento: `develop`
- Features: `feature/nome-descritivo`
- Commits: mensagens claras e descritivas
  - ✅ "Add nuclear scraper with multi-threading"
  - ❌ "update stuff"

---

## 🎯 PRÓXIMOS PASSOS (ROADMAP)

### ✅ Fase 1: Scraping Mediador (ATUAL)
- [x] Protótipo single-threaded
- [x] Versão "nuclear" multi-thread
- [ ] Cobertura completa de 27 UFs
- [ ] Validação de integridade (checksums)
- [ ] Dashboard de progresso (opcional)

### 🔄 Fase 2: Pipeline Bronze → Silver
- [ ] Ingestão de PDFs no Delta Lake (formato Bronze)
- [ ] OCR em PDFs de imagem (se necessário)
- [ ] Extração de texto estruturado
- [ ] Parsing de cláusulas específicas:
  - Piso salarial
  - Vale-transporte
  - Vale-refeição
  - Jornada de trabalho
  - Adicionais (periculosidade, insalubridade, noturno)
- [ ] Schema Silver validado e normalizado

### 🔍 Fase 3: Busca e Análise
- [ ] Embeddings vetoriais (OpenAI, Cohere ou open-source)
- [ ] Vector database (Qdrant, Weaviate ou ChromaDB)
- [ ] Busca semântica: "quais convenções têm piso > R$2.000?"
- [ ] Elasticsearch para busca textual tradicional
- [ ] Dashboard analítico (Streamlit ou Grafana)

### 🌐 Fase 4: API Nacional
- [ ] API REST com FastAPI
- [ ] Endpoints principais:
  - `GET /api/v1/piso/{cnpj}/{cbo}`
  - `GET /api/v1/convencoes?uf=SP&setor=comercio`
  - `GET /api/v1/clausulas?termo=vale+transporte`
- [ ] Autenticação e rate limiting
- [ ] Documentação OpenAPI/Swagger
- [ ] Deploy em produção (Kubernetes)

### 🚀 Fase 5: Scraping de Portais Individuais
- [ ] Mapear top 100 sindicatos mais relevantes
- [ ] Scrapers customizados por sindicato
- [ ] Detecção automática de atualizações (delta)
- [ ] Orquestração com Airflow/Prefect

### 🤖 Fase 6: Automação de Folha
- [ ] Integração com sistemas de folha de pagamento
- [ ] API para calcular piso por CNPJ + CBO + data
- [ ] Alertas de novas convenções/aditivos
- [ ] Compliance check automático

---

## ⚠️ CONSIDERAÇÕES LEGAIS E ÉTICAS

### Dados Públicos

- ✅ Todos os dados do Sistema Mediador são **públicos e gratuitos**
- ✅ Acesso via portal oficial do governo brasileiro
- ✅ Nenhuma autenticação ou paywall

### Rate Limiting Ético

- ✅ 8 req/s agregado (muito abaixo do limite técnico)
- ✅ Respeito a robots.txt (se existir)
- ✅ User-Agent identificado: `sis-sindical/1.0`
- ✅ Retry com backoff exponencial (não bombardear servidor)

### Uso dos Dados

- ✅ Finalidade: **acesso público organizado** a informações trabalhistas
- ✅ Não viola direitos autorais (dados factuais e oficiais)
- ✅ Contribui para **transparência** e **democratização** da informação

---

## 🆘 TROUBLESHOOTING

### Erro: "SSL Certificate Verification Failed"
```python
# Adicionar no session do requests:
session.get(url, verify=False)
```

### Erro: "Playwright browser not installed"
```bash
playwright install chromium
```

### Erro: "403 Forbidden" ao acessar Mediador

**Causa**: Proteção anti-bot, firewall corporativo, ou ambiente sandbox.

**Solução**:
1. Usar Playwright (browser real) ao invés de requests
2. Rodar em ambiente com acesso livre à internet (VPS, máquina local)
3. Verificar se site está online: `curl https://www3.mte.gov.br`

### Erro: "Failed to download Chromium"

**Causa**: Firewall bloqueando Azure CDN.

**Solução**:
1. Liberar domínios `*.azureedge.net`
2. Rodar em ambiente sem restrições
3. Ver: [ENVIRONMENT.md](mediador-scraper/ENVIRONMENT.md)

### Scraper muito lento
1. Aumentar `MAX_WORKERS` (cuidado com rate limiting)
2. Verificar largura de banda da rede
3. Usar disco SSD para armazenamento

### Disco cheio
- ~300 GB necessários para base completa
- Alternativa: rodar por UF e subir incrementalmente para S3

### PDFs corrompidos
- Validar com SHA-256 stored vs recalculado
- Script: `python -m scripts.check_integrity`

---

## 📞 CONTATO E CONTRIBUIÇÕES

Este é um projeto open-source (ou será).

Para contribuir:
1. Fork o repositório
2. Crie uma branch feature
3. Faça commit das mudanças
4. Abra um Pull Request

---

## 🏆 CRÉDITOS

Desenvolvido com ❤️ para democratizar acesso a informações trabalhistas no Brasil.

**Tecnologias principais**:
- Python & Playwright
- BeautifulSoup & lxml
- Sistema Mediador (MTE)

---

**Última atualização**: 2025-11-13
**Versão do documento**: 1.0.0
**Status do projeto**: 🟡 MVP em desenvolvimento ativo
