import altair as alt
import streamlit as st
import pandas as pd
from PIL import Image
import os
import numpy as np
import gdown

# Desabilitanto o limite de 5.000 linhas de df do Altair
alt.data_transformers.enable('default', max_rows=None)

st.set_page_config(layout="wide")

# Definindo o diretório onde os arquivos serão salvos
dataset_dir = 'dataset'

st.markdown("""
# Introdução

Foram analisados dados temporais de **10 anos** sobre assistência social financeira, conhecido como **Bolsa Família**. Os dados são oriundos do *Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome* (**MDS**) e do **IBGE**, que contêm informações sobre os municípios.

""")
st.markdown("""
# Informações sobre os dados

- São **735,171 registros**
- **5,572 municípios**
- **27 Estados**
- Séries temporais de **10 anos**


""")


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


# Função para carregar o DataFrame na Session State
def carregar_dataframe():
    # Verifica se o DataFrame já está na Session State
    if 'df' not in st.session_state:
        # Se não estiver, cria um novo DataFrame
        st.session_state.df = carregar_arquivos()

with st.sidebar:
    st.subheader('Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome')
    logo_teste = Image.open('logo.png')  # Certifique-se de que 'logo.png' esteja no mesmo diretório
    st.image(logo_teste, use_column_width=True)


carregar_dataframe()


# Depara dos labels
enquadramento = {
    'Qtd_Pobreza': 'Pobreza ',
    'Qtd_Baixa_Renda': 'Baixa Renda',
    'Qtd_Acima_Metade_SM': 'Acima 1/2 Salário Mínino',
}



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
