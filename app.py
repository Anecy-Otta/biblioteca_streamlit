import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Dashboard Banco de Horas",
    page_icon="⏰",
    layout="wide"
)

# ==================================================
# FUNÇÕES
# ==================================================

MESES_PT = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março",
    "04": "Abril",   "05": "Maio",      "06": "Junho",
    "07": "Julho",   "08": "Agosto",    "09": "Setembro",
    "10": "Outubro", "11": "Novembro",  "12": "Dezembro"
}

def periodo_para_label(periodo: str) -> str:
    """Converte '01-2026' → 'Janeiro/2026'"""
    try:
        mes, ano = periodo.split("-")
        return f"{MESES_PT.get(mes, mes)}/{ano}"
    except:
        return periodo


def saldo_para_decimal(valor):

    if pd.isna(valor):
        return 0

    valor = str(valor).strip()

    if valor == "":
        return 0

    sinal = -1 if valor.endswith("-") else 1

    valor = valor.replace("+", "").replace("-", "")

    try:
        horas, minutos = valor.split(":")
        return sinal * (int(horas) + int(minutos) / 60)
    except:
        return 0


@st.cache_data(ttl=300)
def carregar_dados():

    pasta = Path("dados")

    # Ordena pelos arquivos — MM-YYYY ordena corretamente como string
    arquivos = sorted(pasta.glob("BH *.xlsx"))

    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta 'dados'.")
        st.stop()

    lista_df = []

    for arquivo in arquivos:

        # "BH 01-2026" → "01-2026"
        periodo = arquivo.stem.replace("BH ", "").strip()

        try:
            df_arquivo = pd.read_excel(arquivo, header=6)
            df_arquivo["Período"] = periodo

            # Cria coluna de label legível: "Janeiro/2026"
            df_arquivo["Período Label"] = periodo_para_label(periodo)

            # Cria coluna de data para ordenação cronológica correta
            mes, ano = periodo.split("-")
            df_arquivo["Período Data"] = pd.Timestamp(
                year=int(ano), month=int(mes), day=1
            )

            lista_df.append(df_arquivo)

        except Exception as erro:
            st.warning(f"Erro ao carregar {arquivo.name}: {erro}")

    if not lista_df:
        st.error("Nenhum arquivo pôde ser carregado.")
        st.stop()

    return pd.concat(lista_df, ignore_index=True)


# ==================================================
# CARREGAMENTO
# ==================================================

df = carregar_dados()

# Remove linhas sem matrícula
if "CHAPA" in df.columns:
    df = df.dropna(subset=["CHAPA"])

# Converte saldo
df["Saldo Decimal"] = df["SALDO\nATUAL"].apply(saldo_para_decimal)

# ==================================================
# TÍTULO
# ==================================================

st.title("⏰ Dashboard de Banco de Horas")

st.markdown(
    "Aplicação desenvolvida com Streamlit para análise de banco de horas."
)

# ==================================================
# FILTROS NO TOPO
# ==================================================

st.subheader("Filtros")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    # Ordena pelos períodos em ordem cronológica
    periodos_disponiveis = (
        df[["Período", "Período Label", "Período Data"]]
        .drop_duplicates()
        .sort_values("Período Data")
    )

    opcoes_periodo = ["Todos"] + list(
        periodos_disponiveis["Período Label"]
    )

    periodo_label = st.selectbox("Período", opcoes_periodo)

with col_f2:
    setores = sorted(df["SEÇÃO"].dropna().unique())

    setor = st.selectbox(
        "Setor",
        ["Todos"] + list(setores)
    )

with col_f3:
    funcionarios = sorted(df["NOME"].dropna().unique())

    funcionario = st.selectbox(
        "Funcionário",
        ["Todos"] + list(funcionarios)
    )

# ==================================================
# APLICAÇÃO DOS FILTROS
# ==================================================

df_filtrado = df.copy()

if periodo_label != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Período Label"] == periodo_label
    ]

if setor != "Todos":
    df_filtrado = df_filtrado[df_filtrado["SEÇÃO"] == setor]

if funcionario != "Todos":
    df_filtrado = df_filtrado[df_filtrado["NOME"] == funcionario]

st.divider()

# Guard clause — antes de qualquer KPI ou gráfico
if df_filtrado.empty:
    st.warning(
        "Nenhum registro encontrado para os filtros selecionados."
    )
    st.stop()

# ==================================================
# KPIs
# ==================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Funcionários",
    df_filtrado["NOME"].nunique()
)

col2.metric(
    "Maior Saldo",
    f"{df_filtrado['Saldo Decimal'].max():.2f} h"
)

col3.metric(
    "Menor Saldo",
    f"{df_filtrado['Saldo Decimal'].min():.2f} h"
)

col4.metric(
    "Saldo Médio",
    f"{df_filtrado['Saldo Decimal'].mean():.2f} h"
)

st.divider()

# ==================================================
# GRÁFICO POR FUNCIONÁRIO
# ==================================================

st.subheader("Saldo por Funcionário")

grafico_func = (
    df_filtrado.groupby("NOME")["Saldo Decimal"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(grafico_func)

# ==================================================
# GRÁFICO POR SETOR
# ==================================================

st.subheader("Saldo Médio por Setor")

grafico_setor = (
    df_filtrado.groupby("SEÇÃO")["Saldo Decimal"]
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(grafico_setor)

# ==================================================
# EVOLUÇÃO MENSAL — ordenada cronologicamente
# ==================================================

st.subheader("Evolução Mensal do Banco de Horas")

evolucao = (
    df_filtrado.groupby(
        ["Período Data", "Período Label"]
    )["Saldo Decimal"]
    .mean()
    .reset_index()
    .sort_values("Período Data")        # garante ordem cronológica
    .set_index("Período Label")         # rótulo legível no eixo X
    ["Saldo Decimal"]
)

st.line_chart(evolucao)

# ==================================================
# RANKING
# ==================================================

col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("🏆 Top 5 Maiores Saldos")

    top5 = (
        df_filtrado
        .sort_values("Saldo Decimal", ascending=False)
        [["NOME", "SEÇÃO", "Período Label", "SALDO\nATUAL"]]
        .head(5)
        .rename(columns={"Período Label": "Período"})
    )

    st.table(top5)

with col_dir:
    st.subheader("⚠️ Top 5 Menores Saldos")

    bottom5 = (
        df_filtrado
        .sort_values("Saldo Decimal", ascending=True)
        [["NOME", "SEÇÃO", "Período Label", "SALDO\nATUAL"]]
        .head(5)
        .rename(columns={"Período Label": "Período"})
    )

    st.table(bottom5)

# ==================================================
# TABELA COMPLETA
# ==================================================

st.subheader("Dados Detalhados")

colunas_exibir = [
    "Período Label",
    "CHAPA",
    "NOME",
    "SEÇÃO",
    "FUNÇÃO",
    "SALDO\nATUAL"
]

st.dataframe(
    df_filtrado[colunas_exibir].rename(
        columns={"Período Label": "Período"}
    ),
    use_container_width=True,
    height=450
)

# ==================================================
# RODAPÉ
# ==================================================

st.divider()

st.caption("Projeto acadêmico desenvolvido utilizando Streamlit.")