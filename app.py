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

    arquivos = sorted(pasta.glob("BH *.xlsx"))

    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta 'dados'.")
        st.stop()

    lista_df = []

    for arquivo in arquivos:

        periodo = arquivo.stem.replace("BH ", "").strip()

        try:
            df_arquivo = pd.read_excel(arquivo, header=6)
            df_arquivo["Período"] = periodo
            df_arquivo["Período Label"] = periodo_para_label(periodo)

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

if "CHAPA" in df.columns:
    df = df.dropna(subset=["CHAPA"])

df["Saldo Decimal"] = df["SALDO\nATUAL"].apply(saldo_para_decimal)

# ==================================================
# TÍTULO
# ==================================================

st.title("⏰ Dashboard de Banco de Horas")

st.markdown(
    "Aplicação desenvolvida com Streamlit para análise de banco de horas."
)

# ==================================================
# FILTROS
# ==================================================

st.subheader("Filtros")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
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
# EVOLUÇÃO MENSAL — ordem cronológica crescente
# ==================================================

import altair as alt

st.subheader("Evolução Mensal do Banco de Horas")

evolucao = (
    df_filtrado.groupby(
        ["Período Data", "Período Label"]
    )["Saldo Decimal"]
    .mean()
    .reset_index()
    .sort_values("Período Data", ascending=True)
)

# Lista de meses na ordem correta para forçar o eixo X
ordem_meses = evolucao["Período Label"].tolist()

grafico_evolucao = (
    alt.Chart(evolucao)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "Período Label:N",
            sort=ordem_meses,          # força a ordem cronológica
            title="Período",
            axis=alt.Axis(labelAngle=-45)
        ),
        y=alt.Y(
            "Saldo Decimal:Q",
            title="Saldo Médio (h)"
        ),
        tooltip=["Período Label", "Saldo Decimal"]
    )
    .properties(height=400)
)

st.altair_chart(grafico_evolucao, use_container_width=True)

# ==================================================
# RANKING
# ==================================================

col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("Funcionários com Maior Saldo")

    top5 = (
        df_filtrado
        .sort_values("Saldo Decimal", ascending=False)
        [["NOME", "SEÇÃO", "Período Label", "SALDO\nATUAL"]]
        .head(5)
        .rename(columns={"Período Label": "Período"})
    )

    st.table(top5)

with col_dir:
    st.subheader("Funcionários com Menor Saldo")

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