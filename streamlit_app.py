!pip install gdown


import altair as alt
import streamlit as st
import pandas as pd
from PIL import Image
import json
import os
import numpy as np
import subprocess
import gdown
import time
import tempfile
import streamlit.components.v1 as components

# Desabilitanto o limite de 5.000 linhas de df do Altair
alt.data_transformers.enable('default', max_rows=None)

st.set_page_config(layout="wide")

# Definindo o diretório onde os arquivos serão salvos
dataset_dir = 'dataset'


# Exibindo um spinner enquanto o aplicativo é carregado
with st.spinner("Carregando arquivos..."):
    progress_text = "Aguarde..."
    my_bar = st.progress(0, text=progress_text)
    arquivos_para_baixar = {
        'municipios.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1NJ61uT7DjRNjq2T5hPLX325QCjgX0v_8',
            'nome_completo': os.path.join(dataset_dir, 'municipios.csv')
        },
        'cadunico.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1rQcmgk4YIDKBxP8ibgPN6ieHLWlxIk6w',
            'nome_completo': os.path.join(dataset_dir, 'cadunico.csv')
        },
        'Brasil.json': {
            'url': 'https://docs.google.com/uc?export=download&id=1W-9gmx9Rd9uXuYc6i9UO0Puiqz_HW97l',
            'nome_completo': os.path.join(dataset_dir, 'Brasil.json')
        },
        'ibge_populacao.csv': {
            'url': 'https://docs.google.com/uc?export=download&id=1am2PX_1fHyMN4GJDL2O7neMWPIR3d-3c',
            'nome_completo': os.path.join(dataset_dir, 'ibge_populacao.csv')
        },
        'logo.png':{
            'url': 'https://docs.google.com/uc?export=download&id=1DLW0mlRix4Gzd9h_TAnLN2v5Ht2YnX2e',
            'nome_completo': os.path.join('logo.png')	
        }
    }

    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
        st.write(f" ${dataset_dir} já criado ")
    # Itera sobre o dicionário de arquivos para download
    total_arquivos = len(arquivos_para_baixar)+2
    for idx, (arquivo, info) in enumerate(arquivos_para_baixar.items(), 1):
        arquivo_path = info['nome_completo']
        url = info['url']
        # Calcula a porcentagem concluída
        porcentagem_concluida = int((idx / total_arquivos) * 100)

        # Verifica se o arquivo já existe, senão faz o download
        if not os.path.exists(arquivo_path):
            gdown.download(url, arquivo_path, quiet=False)
            print(f'Arquivo {arquivo} baixado para {dataset_dir}.')
        else:
            print(f'Arquivo {arquivo} já existe em {dataset_dir}.')

        my_bar.progress(value=porcentagem_concluida, text=arquivo)

    my_bar.progress(value=99, text="git clone https://github.com/luizpedone/municipal-brazilian-geodata")

    # # Executa o comando shell
    # if not os.path.exists("municipal-brazilian-geodata"):
    #     resultado = subprocess.run("git clone https://github.com/luizpedone/municipal-brazilian-geodata", shell=True, capture_output=True, text=True)
    #
    # my_bar.progress(value=99, text="git clone https://github.com/tbrugz/geodata-br.git")
    #
    # if not os.path.exists("geodata-br"):
    #     resultado = subprocess.run("git clone https://github.com/tbrugz/geodata-br", shell=True, capture_output=True, text=True)
    #
    # with open('geodata-br/geojson/geojs-100-mun.json', encoding='utf-8') as f:
    #     geo_data_mun = json.load(f)

    # Exibindo o restante do aplicativo após o carregamento
    st.empty()
    my_bar.empty()


# Função para ler o arquivo CSV
@st.cache_data  # Use st.cache_data para dados que não mudam com o tempo
def carregar_arquivos():

    df_mun = pd.read_csv("dataset/municipios.csv")
    df_cadunico = pd.read_csv("dataset/cadunico.csv")
    df_populacao = pd.read_csv("dataset/ibge_populacao.csv")

    # Ajustar o código do município para ter apenas seis dígitos
    df_mun['CD_MUN_TRUNC'] = df_mun['CD_MUN'].astype(str).str[:-1].astype(int)

    # Seu código para mesclar os dataframes
    df_temp = pd.merge(df_mun, df_populacao, how='left', right_on=['uf', 'nome_municipio'], left_on=['SIGLA_UF', 'NM_MUN'])

    # Preencher valores ausentes com zero
    df_temp['populacao'].fillna(1, inplace=True)
    df_temp['cod_municipio'].fillna(0, inplace=True)
    df_temp['nome_municipio'].fillna('', inplace=True)
    df_temp['uf'].fillna('', inplace=True)

    df_dados = pd.merge(df_temp, df_cadunico, how='inner', left_on='CD_MUN_TRUNC', right_on='codigo_ibge')

    # Remover a coluna redundante
    df_dados.drop('codigo_ibge', axis=1, inplace=True)
    df_dados.drop('CD_MUN_TRUNC', axis=1, inplace=True)
    df_dados.drop('uf', axis=1, inplace=True)
    df_dados.drop('nome_municipio', axis=1, inplace=True)
    df_dados.drop('cod_municipio', axis=1, inplace=True)

    # Dividir a coluna AnoMes em Ano e Mês
    df_dados['Ano'] = (df_dados['anomes_s'] // 100).astype(str)
    df_dados['Mes'] = df_dados['anomes_s'] % 100

    # Renomear colunas
    df_dados.rename(columns={
        'NM_MUN': 'nome_municipio',
        'SIGLA_UF': 'sigla_UF',
        'AREA_KM2': 'area_km2',
        'CD_MUN': 'codigo_IBGE',
        'anomes_s': 'AnoMes',
        'cadun_qtd_pessoas_cadastradas_pobreza_pbf_i': 'Qtd_Pobreza',
        'cadun_qtd_pessoas_cadastradas_baixa_renda_i': 'Qtd_Baixa_Renda',
        'cadun_qtd_pessoas_cadastradas_rfpc_acima_meio_sm_i': 'Qtd_Acima_Metade_SM'
    }, inplace=True)

    df_dados['nome_municipio'] = df_dados['nome_municipio'] +" ("+df_dados['sigla_UF']+")"
    # Calcula a soma dos Cadastros
    df_dados['Qtd_Cadastros'] = df_dados[['Qtd_Pobreza','Qtd_Baixa_Renda','Qtd_Acima_Metade_SM']].abs().sum(axis=1)

    df_dados.loc[df_dados['codigo_IBGE'] == 5107800, 'populacao'] = 15246

    # Verificar se a população é zero antes de calcular a porcentagem
    df_dados['Perc_Cadastros'] = np.where(df_dados['populacao'] == 0, 0, ((df_dados['Qtd_Cadastros'] / df_dados['populacao']) * 100))
    df_dados['Perc_Cadastros'] = df_dados['Perc_Cadastros'].astype(int)

    return df_dados

# Ler os arquivos CSV e o dado em memória
df = carregar_arquivos()

# Depara dos labels
enquadramento = {
    'Qtd_Pobreza': 'Pobreza ',
    'Qtd_Baixa_Renda': 'Baixa Renda',
    'Qtd_Acima_Metade_SM': 'Acima 1/2 Salário Mínino',
}


# Exibir o logo e os filtros no topo do aplicativo
with st.sidebar:
    st.subheader('Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome')
    logo_teste = Image.open('logo.png')  # Certifique-se de que 'logo.png' esteja no mesmo diretório
    st.image(logo_teste, use_column_width=True)
    st.subheader('Seleção de Ano')
    fAno = st.selectbox(
        "Selecione o Ano:",
        options=df['Ano'].unique()
    )


# Função para mostrar a página 1
def show_page1():
    st.write("Conteúdo da página 1")

# Função para mostrar a página 2
def show_page2():
    st.write("Conteúdo da página 2")


dados_ano = df.loc[
    (df['Ano'] == fAno) & (df['Mes'] == 12 )
]

# ****************  Top 20 cidades *****************

# Top 20 cidades
# Filtrando o DataFrame para incluir apenas as linhas onde o valor da coluna "Mes" seja igual a 12
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

# FIM   Top 20 cidades *****************


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

# Municipios com mais diferenças entre os anos

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

lst_municipios = df_filtrado['nome_municipio'].unique()

primeiro_municipio = lst_municipios[0]


min_value = min(df_filtrado['Perc_Cadastros'])
max_value = max(df_filtrado['Perc_Cadastros'])
count_mun_20 = lst_municipios.shape[0]

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



# Mapa por municipios

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

altair_map = alt.Chart(geometry).mark_geoshape(
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


# Fim do Mapa por Municipios



## Evolução do valor de enquadramento de baixa renda ao longo dos anos

# Dados fornecidos
df_acima_meio_salario_minimo = {
    'Ano': ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022',  '2023'],
    'Valor': [362.00, 394.00, 339.00, 440.00, 468.50, 477.00, 499.00, 522.50, 550.00, 606.00, 660.00]
}

df_pobreza = {
    'Ano': ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022',  '2023'],
    'Valor': [140.00, 140.00, 154.00, 170.00, 170.00, 178.00,178.00,178.00, 200.00, 210.00, 218.00]

}

# Convertendo os dados em DataFrame
df_salario_minimo = pd.DataFrame(df_acima_meio_salario_minimo)

# Multiplicando os valores por 2
df_salario_minimo['Valor'] = df_salario_minimo['Valor'] * 2

# Convertendo os dados em DataFrames
df_1 = pd.DataFrame(df_acima_meio_salario_minimo)
df_2 = pd.DataFrame(df_pobreza)
df_3 = pd.DataFrame(df_salario_minimo)

# Gráfico de linhas para os dados 1
gr_area_acima_meio_salario_minimo = alt.Chart(df_3).mark_area().encode(
    x='Ano:N',
    y=alt.Y('Valor:Q', axis=alt.Axis(title='Valores em R$')),
    color=alt.value('blue'),
    # color=alt.Color('blue', legend=alt.Legend(title='Acima de meio salário minimo')),
    tooltip=['Ano:N', 'Valor:Q'],
    text=alt.Text('Valor:Q', format='.2f'),
    # legend=alt.Legend(title='Acima de meio salário minimo')
).properties(
    title='Evolução dos valores de enquadramento social ao longo dos anos',
    width=600,
    height=400
)

# Gráfico de linhas para os dados 1
gr_baixa_renda = alt.Chart(df_1).mark_area().encode(
    x='Ano:N',
    y=alt.Y('Valor:Q', axis=alt.Axis(title='Valores em R$')),
    color=alt.value('orange'),
    tooltip=['Ano:N', 'Valor:Q'],
    text=alt.Text('Valor:Q', format='.2f')
).properties(
    title='Evolução do valor de enquadramento de baixa renda ao longo dos anos',
    width=600,
    height=400
)


# Gráfico de linhas para os dados 2
gr_area_pobreza = alt.Chart(df_2).mark_area().encode(
    x='Ano:N',
    y=alt.Y('Valor:Q', axis=alt.Axis(title='Valores em R$')),
    color=alt.value('red'),
    tooltip=['Ano:N', 'Valor:Q'],
    text=alt.Text('Valor:Q', format='.2f')
).properties(
    title='Evolução dos valores de enquadramento social ao longo dos anos',
    width=600,
    height=400
)

grafico_valores = gr_area_acima_meio_salario_minimo  + gr_baixa_renda + gr_area_pobreza

##


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

# Exibir os dados filtrados
st.header('Pessoas por faixa de renda no Cadastro Único - MI Social')
st.markdown('**Ano Selecionado:** '+ fAno)



TAB_VALOR_ENQ, TAB_TOP20, TAB_MUN, B, C, D = \
    st.tabs(["Valores do Enquadramento Social",
             "Top 20 Cidades",
             "Municípios com Maiores Diferenças Anuais",
             "Cadastros dos Programas Sociais",
             "Evolução ao Longo do Período",
             "Mapa de Aproprição por Municípios"])
with TAB_VALOR_ENQ:
    st.altair_chart(grafico_valores)

    st.markdown("""
**Elegibilidade ao Programa Bolsa Família:**

Considera famílias com renda familiar per capita mensal até a linha administrativa de entrada no Programa Bolsa Família, que caracteriza a situação de pobreza da família.

**Histórico:**
*   -Até abril de 2014: renda familiar per capita mensal até 140 reais
*   -De maio de 2014 a junho de 2016: renda familiar per capita mensal até 154 reais
*   -De julho de 2016 a maio de 2018: renda familiar per capita mensal até 170 reais
*   -De junho de 2018 a outubro de 2021: renda familiar per capita mensal até 178 reais
*   -Novembro de 2021: renda familiar per capita mensal até 200 reais
*   -De dezembro de 2021 a fevereiro de 2023: renda familiar per capita mensal até 210 reais
*   -De março de 2023 em diante: renda familiar per capita mensal até 218 reais

**Baixa renda:**

Considera famílias com renda per capita mensal acima da linha de saída do Programa Bolsa Família até meio salário mínimo, linha que estabelece o público-alvo do Cadastro Único, conforme definição de baixa renda contida no Decreto nº 11.016, de 29 de março de 2022.

**Histórico:**
*   -Até abril de 2014: renda familiar per capita mensal de 140,01 reais até meio salário-mínimo
*   -De maio de 2014 a junho de 2016: renda familiar per capita mensal de 154,01 reais até meio salário-mínimo
*   -De julho de 2016 a maio de 2018: renda familiar per capita mensal de 170,01 reais até meio salário-mínimo
*   -De junho de 2018 a outubro de 2021: renda familiar per capita mensal de 178,01 reais até meio salário-mínimo
*   -Novembro de 2021: renda familiar per capita mensal de 200,01 reais até meio salário-mínimo
*   -De dezembro de 2021 a fevereiro de 2023: renda familiar per capita mensal de 210,01 reais até meio salário-mínimo
*   -De março de 2023 em diante: renda familiar per capita mensal de 218,01 reais até meio salário-mínimo

**Renda per capita mensal acima de meio salário mínimo:**

Considera famílias acima do perfil de baixa renda, ou seja, com renda familiar per capita mensal maior que meio salário-mínimo, o que corresponde aos seguintes valores em cada ano:
*   2013: R\$ 339,00
*   2013: R\$ 362,00
*   2014: R\$ 394,00
*   2015: R\$ 339,00
*   2016: R\$ 440,00
*   2017: R\$ 468,50
*   2018: R\$ 477,00
*   2019: R\$ 499,00
*   2020: R\$ 522,50
*   2021: R\$ 550,00
*   2022: R\$ 606,00
*   2023 (janeiro a abril): R\$ 651,00
*   2023 (a partir de maio): R\$ 660,00    """)
    st.session_state["selected_tab"] = "Valores do Enquadramento Social"
with TAB_TOP20:
    st.session_state["selected_tab"] = "Top 20 Cidades"
    st.altair_chart(grafico_top20_cidades)
with TAB_MUN:
    st.session_state["selected_tab"] = "Municípios com Maiores Diferenças Anuais"
    st.markdown('**Contagem de Municípios com mais de 20% de Diferença entre os Anos:** ' + str(count_mun_20))
    st.altair_chart(grafico_mun)
with B:

    st.session_state["selected_tab"] = "Cadastros dos Programas Sociais"
    st.altair_chart(grafico_df_distribuicao_uf)
with C:
    st.session_state["selected_tab"] = "Evolução ao Longo do Período"
    st.altair_chart(grafico_evolucao)
with D:
    st.session_state["selected_tab"] = "Mapa de Aproprição por Municípios"
    st.altair_chart(altair_map)




