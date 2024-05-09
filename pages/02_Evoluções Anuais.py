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


# top 20

dados_filtrados = df.loc[df['Mes'] == 12]

df_aggregated = dados_filtrados.groupby(['Ano', 'codigo_IBGE', 'nome_municipio', 'sigla_UF']).agg({
        'Qtd_Cadastros': 'sum'
    }).reset_index()
# Agrupa os dados por código IBGE, calculando a soma dos valores absolutos e renomeia a coluna resultante
grouped = df_aggregated.groupby(['codigo_IBGE']).agg(Qtd_Cadastros_sum=('Qtd_Cadastros', 'sum'))
# Ordena o resultado pela soma absoluta em ordem decrescente
grouped_sorted = grouped.sort_values(by='Qtd_Cadastros_sum', ascending=False)

# Seleciona os NN primeiros códigos IBGE distintos
top_codes = grouped_sorted.head(20).reset_index()

# Merge dos DataFrames
df_top_cidades = pd.merge(df_aggregated, top_codes, how='inner', left_on='codigo_IBGE', right_on='codigo_IBGE')

# select a point for which to provide details-on-demand
label = alt.selection_single(
    encodings=['x'], # limit selection to x-axis value
    on='mouseover',  # select on mouseover events
    nearest=True,    # select data point nearest the cursor
    empty='none'     # empty selection includes no data points
)

# define our base line chart of stock prices
grafico_top20_cidades = alt.Chart(df_top_cidades).mark_bar().encode(
    alt.X('nome_municipio:N', sort=alt.EncodingSortField(field='Qtd_Cadastros',op='max',order='descending'), title="Municípios" ),
    alt.Y('Qtd_Cadastros:Q', title="Quantidade de Cadastros"),
    alt.Color('Ano:N', title="Ano", ),
    #tooltip=['Qtd_Cadastros', "Ano"]
).properties(
    title='Top 20 cidades em quantidades de Cadastros',
    width=1000,
    height=600
)

# fim top 20

# Evolução pelo Período

meses = {
    ano * 100 + mes: str(ano * 100 + mes) if mes == 1 else ''
    for ano in range(2013, 2024)
    for mes in range(1, 13)
}

# select a point for which to provide details-on-demand
label = alt.selection_single(
    encodings=['x'], # limit selection to x-axis value
    on='mouseover',  # select on mouseover events
    nearest=True,    # select data point nearest the cursor
    empty='none'     # empty selection includes no data points
)
# Agregar os dados por município e somar a quantidade de cadastrados em todos os programas sociais
df_evolucao = df.groupby(['AnoMes']).agg({
    'Qtd_Pobreza': 'sum',
    'Qtd_Baixa_Renda': 'sum',
    'Qtd_Acima_Metade_SM': 'sum'
}).reset_index()

# Realizar o "melt" nos dados para torná-los longos
df_evolucao = df_evolucao.melt(id_vars='AnoMes', var_name='Programa', value_name='Cadastros')

# Gerar coluna do Label
df_evolucao['EnquadramentoSocial'] = df_evolucao['Programa'].map(enquadramento)


# Converter o número do mês para o nome do mês
df_evolucao['Nome_Mes'] = df_evolucao['AnoMes'].map(meses)


# Gráfico de barras empilhadas
grafico_evolucao = alt.Chart(df_evolucao).mark_line().encode(
    x=alt.X('AnoMes:N', title='AnoMes', axis=alt.Axis(labelOverlap=True), sort=list(meses.values())),
    y=alt.Y('Cadastros:Q', title='Cadastros',),
    color=alt.Color('EnquadramentoSocial:N', title = "Enquadramento Social"),
    tooltip=[ 'Programa', 'Cadastros']
).properties(
    title='Evolução do Enquadramentos Sociais ao longo do período',
    width=1000,
    height=600
)

alt.layer(
    grafico_evolucao,

    # add a rule mark to serve as a guide line
    alt.Chart().mark_rule(color='#aaa').encode(
        x='AnoMes:N'
    ).transform_filter(label),

    # add circle marks for selected time points, hide unselected points
    grafico_evolucao.mark_circle().encode(
        opacity=alt.condition(label, alt.value(1), alt.value(0))
    ).add_selection(label),

    # add text labels for stock prices
    grafico_evolucao.mark_text(align='left', dx=5, dy=-5).encode(text='Cadastros:Q' ).transform_filter(label),

    data=df_evolucao
).properties(
    title='Evolução dos Cadastros dos Programas Sociais ao longo do período',
    width=1000,
    height=600
)

# Fim da Evolução pelo Período

# FIM - Municipios com mais diferenças entre os anos
dados_filtrados = df.loc[df['Mes'] == 12]

# Ordenar o DataFrame pela coluna 'AnoMes'
dados_filtrados = dados_filtrados.sort_values(by=['codigo_IBGE', 'nome_municipio', 'sigla_UF', 'AnoMes'])

# Calcular a diferença percentual de um mês para o outro
dados_filtrados['Diff_Perc_Cadastros'] = dados_filtrados.groupby(['codigo_IBGE', 'nome_municipio', 'sigla_UF'])['Perc_Cadastros'].diff()

dados_filtrados['Diff_Perc_Cadastros'].fillna(0, inplace=True)

# Calcular a soma acumulada por grupo

dados_filtrados['Abs_Diff_Perc_Cadastros'] = dados_filtrados['Diff_Perc_Cadastros'].abs()

# Visualizar o novo DataFrame com a coluna de diferença percentual

valores_unicos = dados_filtrados.query('(Abs_Diff_Perc_Cadastros > 20)')['codigo_IBGE'].unique()
# Filtrar o DataFrame original
df_filtrado = dados_filtrados.query('codigo_IBGE in @valores_unicos')


# select a point for which to provide details-on-demand
label_mun = alt.selection_single(
    encodings=['x'], # limit selection to x-axis value
    on='mouseover',  # select on mouseover events
    nearest=True,    # select data point nearest the cursor
    empty='none'     # empty selection includes no data points
)

lst_municipios = sorted(df_filtrado['nome_municipio'].unique())

primeiro_municipio = lst_municipios[0]


min_value = min(df_filtrado['Perc_Cadastros'])
max_value = max(df_filtrado['Perc_Cadastros'])
count_mun_20 = len(lst_municipios)

# Criar o menu suspenso
input_dropdown_mun = alt.binding_select(options=lst_municipios, name=f"Município:" )
selection_mun = alt.selection_single(fields=['nome_municipio'], bind=input_dropdown_mun, init={'nome_municipio': primeiro_municipio})


grafico_mun = alt.Chart(df_filtrado).mark_trail().encode(
    x='Ano:N',
    y=alt.Y('Perc_Cadastros:Q', title='Diferença +- %', scale=alt.Scale(domain=[min_value, max_value]) ),
    size=alt.Size('Perc_Cadastros:Q', title="Diferença Percentual"),
)

grafico_mun1 = alt.layer(
    grafico_mun, # base line chart
    data=df_filtrado
).properties(
    title="Municípios com Diferença Percentual entre os Anos acima de 20%",
    width=800,
    height=400
).add_selection(
     selection_mun
 ).transform_filter(
     selection_mun
 )

# Adicionando rótulos de texto aos valores do eixo Y
rotulos_y = alt.Chart(df_filtrado).mark_text(
    align='left',
    baseline='middle',
    dx=5,  # Deslocamento horizontal
    dy=0,  # Deslocamento vertical
    fontSize=15,  # Tamanho da fonte
).encode(
    x='Ano:N',  # Posiciona os rótulos de acordo com o eixo X
    y=alt.Y('Perc_Cadastros:Q', title='Diferença +- %'),  # Posiciona os rótulos ao longo do eixo Y
    text=alt.Text('Perc_Cadastros:Q', format=".0f")  # Mostra os valores de 'Diff_Perc_Cadastros' com duas casas decimais como texto
)

 # Exibindo o gráfico com a linha mais grossa no eixo y = 0
grafico_mun = (grafico_mun1 + rotulos_y)

# FIM - Municipios com mais diferenças entre os anos



TAB_TOP20, TAB_EVOLUCAO, TAB_MUN = st.tabs(["Top 20 Cidades",  "Evolução ao Longo do Período", "Municípios com Maiores Diferenças Anuais"])
with TAB_TOP20:
    st.altair_chart(grafico_top20_cidades)
with TAB_EVOLUCAO:
    st.altair_chart(grafico_evolucao)
with TAB_MUN:
    st.altair_chart(grafico_mun)

