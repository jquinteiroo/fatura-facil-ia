# Fatura Fácil

> Entenda sua fatura de cartão sem cadastro, sem conectar sua conta bancária e sem depender de API de IA.

O **Fatura Fácil** é uma aplicação web open source para transformar faturas PDF ou CSV em uma visão simples dos gastos. A versão 2 está sendo reconstruída com um motor determinístico: extração, categorização, cálculos, perguntas e comparação de faturas funcionam sem Gemini, OpenAI, Claude ou outro LLM.

## O que a V2 já faz

- leitura local de PDF e CSV;
- parsers modulares para Nubank, Banco Inter, Mercado Pago e Sicredi;
- fallback genérico para outros layouts;
- categorização automática por regras;
- dashboard com total, categorias, média e principais despesas;
- destaques calculados sem IA;
- perguntas objetivas sobre a fatura;
- revisão manual de descrição, categoria e valor;
- remoção de lançamentos incorretos;
- exportação da fatura revisada para CSV;
- comparação entre duas faturas;
- modo de privacidade visual;
- limite de upload e validação básica do arquivo;
- testes automatizados com GitHub Actions.

## Privacidade

O Fatura Fácil **não envia o conteúdo da fatura para modelos de IA**.

O arquivo é recebido pelo servidor Flask para extração e processamento durante a requisição. A aplicação não possui banco de dados para armazenar faturas. Antes de disponibilizar uma instância pública, revise a política de privacidade e a infraestrutura de hospedagem escolhida.

## Bancos

Existem parsers dedicados para:

- Nubank
- Banco Inter
- Mercado Pago
- Sicredi

> Os parsers ainda estão em validação. Layouts de faturas mudam e podem variar entre produtos do mesmo banco. Sempre confira a área **Revise as transações** antes de considerar o resultado final.

## Testar a branch V2

### 1. Clonar

```bash
git clone -b feat/v2-autonomous-foundation --single-branch https://github.com/jquinteiroo/fatura-facil-ia.git
cd fatura-facil-ia
```

### 2. Criar ambiente virtual

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements-dev.txt
```

### 4. Rodar testes

```bash
pytest -q
```

### 5. Iniciar o app

```bash
python app.py
```

Abra:

```text
http://127.0.0.1:5000
```

## Faturas de exemplo

A pasta `examples/` contém duas faturas CSV fictícias que podem ser usadas para testar o dashboard e a comparação sem expor dados financeiros reais:

- `examples/fatura_setembro.csv`
- `examples/fatura_agosto.csv`

Carregue setembro como fatura principal e depois use **Comparar fatura** para selecionar agosto.

## Tecnologias

### Backend
- Python
- Flask
- pandas
- PyPDF2
- Gunicorn

### Frontend
- HTML
- Tailwind CSS
- JavaScript
- Chart.js
- Lucide
- DOMPurify

## Testes

Os testes cobrem:

- parsing de valores;
- detecção de banco;
- categorização;
- layouts representativos dos quatro bancos;
- consultas sobre a fatura;
- comparação entre faturas.

O workflow em `.github/workflows/tests.yml` executa `pytest` automaticamente em pushes e pull requests.

## Estado da V2

A V2 está na branch:

```text
feat/v2-autonomous-foundation
```

O desenvolvimento está sendo mantido fora da `main` até a validação manual com faturas reais anonimizadas.
