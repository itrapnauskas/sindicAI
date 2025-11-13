# Mediador Scraper

Módulo de scraping do Sistema Mediador (MTE) para o projeto **sindicAI**.

## Objetivo

Coletar **100% da base de convenções coletivas, acordos coletivos e aditivos** do Sistema Mediador do Ministério do Trabalho e Emprego.

## Cobertura

- ✅ **27 UFs** (todas as unidades federativas do Brasil)
- ✅ **3 tipos**: CCT (Convenção Coletiva), ACT (Acordo Coletivo), Aditivos
- ✅ **Histórico completo** desde 2010 (configurável para 2000+)

## Instalação

```bash
# 1. Instalar dependências Python
pip install -r requirements.txt

# 2. Instalar browser Chromium para Playwright
playwright install chromium

# 3. Configurar ambiente (opcional)
cp .env.example .env
```

## Uso

### Teste em uma UF específica

```bash
python -m scripts.run_single_uf --uf SC --tipo 1 --max-paginas 2
```

### Coleta completa (TODAS as UFs)

⚠️ **ATENÇÃO**: Isso vai baixar ~800k PDFs (~300 GB). Certifique-se de ter espaço em disco!

```bash
# Usar tmux para sessão persistente
tmux new -s nuclear

# Executar scraper
python -m mediador.scraper_nuclear

# Detach: Ctrl+B, depois D
# Reattach: tmux attach -t nuclear
```

## Estrutura de Dados

Cada instrumento é salvo em:
```
data/raw/mediador/{UF}/{ANO}/{TIPO}/{ID_MEDIADOR}/
├── metadata.json      # Metadados estruturados
├── instrumento.html   # HTML original da página
├── instrumento.pdf    # PDF do instrumento
└── instrumento.sha256 # Hash SHA-256 do PDF
```

## Progresso

Logs em tempo real mostram:
```
[15:42:10] 🚀 SP-CCT iniciado
[15:42:15] ✅ SP-CCT página 1 -> 20 docs
[15:42:22] ✅ SP-CCT página 2 -> 20 docs
```

## Troubleshooting

Ver seção de troubleshooting no [CLAUDE.md](../CLAUDE.md) principal.

## Próximos Passos

1. Validação de integridade (checksums)
2. Dashboard de progresso
3. Pipeline Bronze → Silver (estruturação dos dados)

---

Para mais detalhes sobre o projeto completo, veja [CLAUDE.md](../CLAUDE.md).
