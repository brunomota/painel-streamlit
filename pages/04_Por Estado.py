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
    st.subheader('Seleção de Estado')
    fEstado = st.selectbox("Selecione o Estado:", options=sorted(df['sigla_UF'].unique()))

# Seleção de Ano
with col2:
    st.subheader('Seleção de Ano')
    fAno = st.selectbox("Selecione o Ano:", options=sorted(df['Ano'].unique()))


dados_estado = df.loc[
    (df['sigla_UF'] == fEstado) & (df['Mes'] == 12 ) & (df['Ano'] == fAno )
]


@st.cache_data()
def load_geometry(estado):
    return (
        alt.Data(
            url="https://raw.githubusercontent.com/luizpedone/municipal-brazilian-geodata/master/data/"+estado+".json",
            format=alt.DataFormat(property='features')
        )
    )

geometry = load_geometry(fEstado)

grafico_mapa = alt.Chart(geometry).mark_geoshape(
    stroke='white',
    strokeWidth=0.1
).encode(
    color=alt.Color('Perc_Cadastros:Q', title='Percentual',
                    scale=alt.Scale(domain=[0, 100], scheme='blueorange')),
     tooltip=[
         alt.Tooltip('properties.NOME:N', title='Município: '),
         alt.Tooltip('Perc_Cadastros:Q', title='% de Cadastros: '),
         alt.Tooltip('populacao:Q', title='Populacao: '),
         alt.Tooltip('Ano:N', title='Ano: '),
     ]
).transform_lookup(
    lookup='properties.GEOCODIGO',
    from_=alt.LookupData(dados_estado, 'codigo_IBGE', ['Perc_Cadastros','populacao', 'Ano'])
).properties(
    title='Média do Percentual Anual para Quantidade de Cadastros versus População',
    width=785,
    height=529
)
# Fim Mapa

st.altair_chart(grafico_mapa);
