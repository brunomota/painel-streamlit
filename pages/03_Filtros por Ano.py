import streamlit as st
import altair as alt
import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np

df = st.session_state.df

# Depara dos labels
enquadramento = {
    'Qtd_Pobreza': 'Pobreza ',
    'Qtd_Baixa_Renda': 'Baixa Renda',
    'Qtd_Acima_Metade_SM': 'Acima 1/2 Salário Mínino',
}


with st.sidebar:
    st.subheader('Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome')
    logo_teste = Image.open('logo.png')  # Certifique-se de que 'logo.png' esteja no mesmo diretório
    st.image(logo_teste, use_column_width=True)

st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)


# Divide a tela em duas colunas
col1, col2 = st.columns(2)

# Seleção de Estado
with col1:
    st.subheader('Seleção de Ano')
    fAno = st.selectbox("Selecione o Ano:", options=sorted(df['Ano'].unique()))

# Seleção de Ano
with col2:
    st.subheader('')


dados_ano = df.loc[
    (df['Ano'] == fAno) & (df['Mes'] == 12 )
]


#  Distribuicao entre os estados

df_distribuicao_uf = dados_ano.query("Mes == 12")
# Agregar os dados por município e somar a quantidade de cadastrados em todos os programas sociais
df_distribuicao_uf = df_distribuicao_uf.groupby(['sigla_UF']).agg({
    'Qtd_Pobreza': 'sum',
    'Qtd_Baixa_Renda': 'sum',
    'Qtd_Acima_Metade_SM': 'sum'
}).reset_index()


# Melt do DataFrame para tornar os dados longos
df_distribuicao_uf = df_distribuicao_uf.melt(id_vars='sigla_UF', var_name='Programa', value_name='Quantidade')

# Gerar coluna do Label
df_distribuicao_uf['EnquadramentoSocial'] = df_distribuicao_uf['Programa'].map(enquadramento)

# Gráfico de barras empilhadas
grafico_df_distribuicao_uf = alt.Chart(df_distribuicao_uf).mark_bar().encode(
    x=alt.X('sigla_UF:N', title='Estado'),
    y=alt.Y('Quantidade:Q', title='Quantidade de Cadastrados', scale=alt.Scale(domain=[0, 16000000])),
    color=alt.Color('EnquadramentoSocial:N', title="Enquadramento Social"),
    tooltip=['sigla_UF', 'Programa', 'Quantidade']
).properties(
    title='Quantidade de Cadastros por enquadramento social e Estado - '+fAno,
    width=1000,
    height=600)

#  FIM Distribuicao entre os estados



df_mapa = dados_ano.query("Mes == 12")
# Agregar os dados por 'codigo_IBGE' e 'populacao' e calcular a média de 'Perc_Cadastros' arredondada
df_mapa = df_mapa.groupby(['codigo_IBGE', 'populacao']).agg({
    'Perc_Cadastros': lambda x: min(round(x.mean(), 1), 100),
}).reset_index()

@st.cache_data()
def load_geometry():
    return (
        alt.Data(
            url="https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json",
            format=alt.DataFormat(property='features')
        )
    )

geometry = load_geometry()

grafico_mapa = alt.Chart(geometry).mark_geoshape(
    stroke='white',
    strokeWidth=0.1
).encode(
    color=alt.Color('Perc_Cadastros:Q', title='Percentual',
                    scale=alt.Scale(type='linear', scheme='blueorange')),
     tooltip=[
         alt.Tooltip('properties.name:N', title='Município '),
         alt.Tooltip('Perc_Cadastros:Q', title='Média %'),
         alt.Tooltip('populacao:Q', title='Populacao'),
     ]
).transform_lookup(
    lookup='properties.id',
    from_=alt.LookupData(df_mapa, 'codigo_IBGE', ['Perc_Cadastros','populacao'])
).properties(
    title='Média do Percentual Anual para Quantidade de Cadastros versus População',
    width=785,
    height=529
)
# Fim Mapa


TAB_SOCIAL, TAB_MAPA =  st.tabs(["Cadastros dos Programas Sociais", "Mapa de Aproprição por Municípios"])
with TAB_SOCIAL:
    st.altair_chart(grafico_df_distribuicao_uf)
with TAB_MAPA:
    st.altair_chart(grafico_mapa)
