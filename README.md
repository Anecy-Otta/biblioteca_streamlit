# biblioteca_streamlit

# ⏰ Dashboard de Banco de Horas

Aplicação web desenvolvida com **Streamlit** para visualização e análise do banco de horas dos funcionários, a partir de arquivos Excel exportados do sistema de RH.

---

## Funcionalidades

- Filtros interativos por **período**, **setor** e **funcionário**
- KPIs com total de funcionários, maior saldo, menor saldo e saldo médio
- Gráfico de barras com saldo por funcionário
- Gráfico de linha com evolução mensal do banco de horas em ordem cronológica
- Ranking dos funcionários com maior e menor saldo
- Tabela detalhada com todos os registros filtrados

---

## Estrutura do Projeto

```
BIBLIOTECA_STREAMLIT/
│
├── dados/
│   ├── BH 01-2026.xlsx
│   ├── BH 02-2026.xlsx
│   ├── BH 03-2026.xlsx
│   ├── BH 04-2026.xlsx
│   └── BH 05-2026.xlsx
│
├── app.py
├── requirements.txt
└── README.md
```

---

## Formato dos Arquivos Excel

Os arquivos devem seguir o padrão de nomenclatura **`BH MM-YYYY.xlsx`** e estar na pasta `dados/`.

Os dados são lidos a partir da **linha 7** (header na linha 6, índice base 0), e as colunas esperadas são:

| Coluna | Descrição |
|---|---|
| `CHAPA` | Matrícula do funcionário |
| `NOME` | Nome do funcionário |
| `SEÇÃO` | Setor/departamento |
| `FUNÇÃO` | Cargo |
| `SALDO\nATUAL` | Saldo do banco de horas no formato `HH:MM` ou `HH:MM-` para negativo |

---

## Instalação

**Pré-requisitos:** Python 3.8 ou superior.

1. Clone o repositório:

```bash
git clone https://github.com/Anecy-Otta/biblioteca_streamlit.git
cd biblioteca_streamlit
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Como Executar

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`.

---

## Dependências

```
streamlit
pandas
openpyxl
altair
```

> O arquivo `requirements.txt` contém todas as dependências necessárias.

---

## Observações

- Linhas sem matrícula (`CHAPA` vazia) são removidas automaticamente no carregamento.
- O saldo é convertido para horas decimais internamente para cálculos e gráficos. O valor exibido nas tabelas mantém o formato original do Excel.
- Os dados são mantidos em cache por **5 minutos**. Para forçar a releitura dos arquivos, recarregue a página e limpe o cache pelo menu do Streamlit.

---

## Projeto Acadêmico

Desenvolvido como projeto acadêmico utilizando Streamlit.