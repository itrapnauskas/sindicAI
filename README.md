# sindicAI

**A primeira base de dados nacional completa com TODAS as convenções coletivas do Brasil.**

## 🎯 Visão Geral

O **sindicAI** é um projeto ambicioso para criar uma plataforma que:

- 📥 Coleta automaticamente convenções de TODOS os sindicatos do Brasil
- 💾 Armazena dados originais (PDFs, HTMLs) + dados estruturados
- 🔍 Extrai cláusulas, pisos salariais, benefícios de forma inteligente
- 🤖 Automatiza implantação de folha de pagamento
- 🌐 Fornece API nacional para consulta por CNPJ, CBO, UF

## 📊 Escopo

- ✅ **27 UFs** (todas as unidades federativas)
- ✅ **Todos os sindicatos** cadastrados
- ✅ **Todos os tipos**: CCT, ACT, Aditivos
- ✅ **~800.000 instrumentos** coletivos
- ✅ **Histórico completo** desde 2000+

## 🚀 Status Atual: MVP - Scraping Mediador

Estamos na **Fase 1**: coleta massiva do Sistema Mediador (MTE).

### Quick Start

```bash
# 1. Instalar dependências
cd mediador-scraper
pip install -r requirements.txt
playwright install chromium

# 2. Testar com uma UF
python -m scripts.run_single_uf --uf SC --tipo 1

# 3. Coleta completa (CUIDADO: ~300 GB!)
python -m mediador.scraper_nuclear
```

## 📁 Estrutura do Projeto

```
sindicAI/
├── CLAUDE.md              # Documentação completa para AI assistants
├── README.md              # Este arquivo
├── mediador-scraper/      # Scraper do Sistema Mediador (ATUAL)
├── pipeline/              # Pipeline ETL (TODO)
├── api/                   # API REST (TODO)
└── data/                  # Dados brutos (gitignored)
```

## 📚 Documentação

- **[CLAUDE.md](CLAUDE.md)** - Documentação técnica completa para desenvolvedores e AI assistants
- **[mediador-scraper/README.md](mediador-scraper/README.md)** - Docs específicas do scraper

## 🗺️ Roadmap

- [x] **Fase 1**: Scraping Mediador (MVP atual)
- [ ] **Fase 2**: Pipeline Bronze → Silver (estruturação)
- [ ] **Fase 3**: Busca semântica + análise
- [ ] **Fase 4**: API nacional
- [ ] **Fase 5**: Scraping de portais individuais
- [ ] **Fase 6**: Automação de folha

## 🤝 Contribuindo

Este projeto está em desenvolvimento ativo. Contribuições são bem-vindas!

1. Fork o repositório
2. Crie uma branch feature
3. Commit suas mudanças
4. Abra um Pull Request

## ⚖️ Legal

Todos os dados coletados são públicos e gratuitos, disponibilizados oficialmente pelo Ministério do Trabalho e Emprego.

## 📞 Contato

Para dúvidas, sugestões ou colaborações, abra uma issue.

---

**Desenvolvido com ❤️ para democratizar acesso a informações trabalhistas no Brasil.**
