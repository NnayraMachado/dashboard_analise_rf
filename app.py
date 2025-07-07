import streamlit as st
import folium
from streamlit_folium import folium_static
import json
import pandas as pd
import os
import json
import plotly.express as px
from datetime import datetime
import io
import numpy as np
import altair as alt 
import requests
import folium

# --- Funções Auxiliares ---
def create_formatted_crosstab(df_data, index_col, col_col):
    counts = pd.crosstab(df_data[index_col], df_data[col_col])
    percs = pd.crosstab(df_data[index_col], df_data[col_col], normalize='columns').mul(100).round(2)
    formatted_df = pd.DataFrame(index=counts.index)
    for c in counts.columns:
        formatted_df[c] = counts[c]
        formatted_df[f'{c} (%)'] = percs[c]
    sorted_cols = []
    for c in counts.columns:
        sorted_cols.append(c)
        sorted_cols.append(f'{c} (%)')
    formatted_df = formatted_df[sorted_cols]
    total_row_counts = counts.sum(axis=0)
    total_row_percs = pd.Series([100.0] * len(counts.columns), index=counts.columns)
    total_row_data = {}
    for c in counts.columns:
        total_row_data[c] = total_row_counts[c]
        total_row_data[f'{c} (%)'] = total_row_percs[c]
    total_df_row = pd.DataFrame([total_row_data], index=['Total respondentes'])
    return pd.concat([formatted_df, total_df_row])


# --- Configurações da Página Streamlit ---
st.set_page_config(
    page_title="Dashboard de Análise do RF",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Carregar os Dados (apenas uma vez por sessão) ---
# Caminhos para os dois arquivos CSV e o GeoJSON
FILE_PATH_MAIN_DATA = os.path.join("data", "questionario.csv") # SEU ARQUIVO PRINCIPAL
FILE_PATH_SENTIMENT_DATA = os.path.join("data", "questionario_analisado.csv") # SEU ARQUIVO DE SENTIMENTOS
FILE_PATH_GEOJSON = os.path.join("data", "geojs-uf.json") # SEU GEOJSON (pontos)

# Caminho do GeoJSON dos estados do Brasil
geojson_path = 'data/geojs-uf.json'  

# Carregar GeoJSON
with open(geojson_path, encoding='utf-8') as f:
    estados_geojson = json.load(f)


if 'main_data_loaded' not in st.session_state: # Flag para carregar uma única vez
    
    # --- Carregar DataFrame Principal ---
    if not os.path.exists(FILE_PATH_MAIN_DATA):
        st.error(f"ERRO CRÍTICO: O arquivo de dados principal '{FILE_PATH_MAIN_DATA}' NÃO FOI ENCONTRADO. "
                 "Verifique o nome do arquivo, a pasta 'data/'.")
        st.stop()
    try:
        df_main_loaded = pd.read_csv(FILE_PATH_MAIN_DATA, sep=';', encoding='utf-8')
        df_main_loaded.columns = df_main_loaded.columns.str.strip()
        
        # Pré-processamento de ID3 para Idade no DF principal
        if 'ID3' in df_main_loaded.columns:
            df_main_loaded['ID3_datetime'] = pd.to_datetime(df_main_loaded['ID3'], errors='coerce', dayfirst=True)
            today = datetime(2025, 7, 3) 
            df_main_loaded['Idade'] = (today.year - df_main_loaded['ID3_datetime'].dt.year) - \
                                 ((today.month < df_main_loaded['ID3_datetime'].dt.month) | \
                                  ((today.month == df_main_loaded['ID3_datetime'].dt.month) & \
                                   (today.day < df_main_loaded['ID3_datetime'].dt.day)))
            df_main_loaded.loc[df_main_loaded['Idade'] < 0, 'Idade'] = pd.NA
            df_main_loaded.loc[df_main_loaded['Idade'] > 120, 'Idade'] = pd.NA
        else:
            df_main_loaded['Idade'] = pd.NA
        
        st.session_state['df_original_main'] = df_main_loaded.copy()
        #st.success(f"Dados principais ('{FILE_PATH_MAIN_DATA}') carregados com sucesso! Total de {len(st.session_state.df_original_main)} linhas.")
       # st.info("Colunas do DataFrame Principal: " + ", ".join(st.session_state.df_original_main.columns.tolist()))

    except Exception as e:
        st.error(f"ERRO CRÍTICO: Falha ao carregar ou processar '{FILE_PATH_MAIN_DATA}': {e}. Verifique separador, encoding ou integridade.")
        st.stop()

    # --- Carregar DataFrame de Sentimentos ---
    if not os.path.exists(FILE_PATH_SENTIMENT_DATA):
        st.warning(f"AVISO: O arquivo de dados de sentimento '{FILE_PATH_SENTIMENT_DATA}' NÃO FOI ENCONTRADO. "
                   "As análises de sentimento não estarão disponíveis. Execute 'processar_sentimentos.py'.")
        st.session_state['df_original_sentiment'] = pd.DataFrame() # Cria um DF vazio para evitar erros
    else:
        try:
            df_sentiment_loaded = pd.read_csv(FILE_PATH_SENTIMENT_DATA, sep=';', encoding='utf-8')
            df_sentiment_loaded.columns = df_sentiment_loaded.columns.str.strip()
            st.session_state['df_original_sentiment'] = df_sentiment_loaded.copy()
            #st.success(f"Dados de sentimento ('{FILE_PATH_SENTIMENT_DATA}') carregados com sucesso! Total de {len(st.session_state.df_original_sentiment)} linhas.")
        except Exception as e:
            st.error(f"ERRO CRÍTICO: Falha ao carregar ou processar '{FILE_PATH_SENTIMENT_DATA}': {e}.")
            st.session_state['df_original_sentiment'] = pd.DataFrame() # Cria um DF vazio
    
    # --- Carregar o arquivo GeoJSON ---
    if not os.path.exists(FILE_PATH_GEOJSON):
        st.error(f"ERRO CRÍTICO: O arquivo GeoJSON '{FILE_PATH_GEOJSON}' NÃO FOI ENCONTRADO. "
                 "Certifique-se de que ele está na pasta 'data/'.")
        st.stop()
    try:
        with open(FILE_PATH_GEOJSON, 'r', encoding='utf-8') as f:
            st.session_state['geojson_data'] = json.load(f)
        
        # DEBUG: Verifica o tipo de geometria no GeoJSON
        first_feature_type = st.session_state['geojson_data']['features'][0]['geometry']['type'] if st.session_state['geojson_data']['features'] else 'N/A'
        if first_feature_type not in ['Point', 'Polygon', 'MultiPolygon']: # Se não for nem ponto nem polígono
             st.warning(f"AVISO: O GeoJSON carregado parece conter geometrias do tipo '{first_feature_type}'. O mapa pode não ser exibido corretamente. Esperado 'Point', 'Polygon' ou 'MultiPolygon'.")
       # st.success(f"Mapa GeoJSON ('{FILE_PATH_GEOJSON}') carregado com sucesso!")
    except Exception as e:
        st.error(f"ERRO CRÍTICO: Falha ao carregar o arquivo GeoJSON: {e}")
        st.stop()
    
    st.session_state['main_data_loaded'] = True # Define a flag para que o carregamento não se repita

#else:
  #  st.info(f"Dados e GeoJSON já carregados (usando cache da sessão).")


# DF principal para filtros e análises (copiado do original para resetar filtros)
df_main = st.session_state.df_original_main.copy() 
# DF de sentimentos (separado para análises específicas)
df_sentiment = st.session_state.df_original_sentiment.copy() 


# --- DEFINIÇÃO DE GRUPOS DE QUESTÕES E SEUS RÓTULOS COMPLETOS ---
# Atualiza question_labels para incluir colunas de sentimentos com base no df_sentiment
# e outras colunas que podem não estar no df_main
question_labels = {
    # Identificação
    'ID3': 'ID3 - Qual sua data de nascimento?', 'Idade': 'Idade (Calculada)', 'ID7': 'ID7 - Raça/Cor',
    'ADAI_ID8': 'ADAI_ID8 - Qual seu sexo?', 'ID8': 'ID8 - Gênero', 'ID9': 'ID9 - Orientação sexual:',
    'ID10': 'ID10 - É pessoa com deficiência?', 'ID10.1': 'ID10.1 - Qual o tipo de deficiência?',
    'ID11': 'ID11 - Qual sua escolaridade?', 'ID12': 'ID12 - É adepto de alguma dessas práticas religiosas?',
    'ADAI_ID12': 'ADAI_ID12 - Qual(is) a(s) sua(s) profissão(ões)?',
    'PCT0': 'PCT0 - Você e/ou seu núcleo familiar pertencem a algum povo ou comunidade tradicional?',
    'NF1': 'NF1 - Quantas pessoas compõem o núcleo familiar?',
    'ADAI_CT4': 'ADAI_CT4 - O território ao qual pertence o entrevistado está em qual dessas localidades?',

    # Colunas de Sentimento (NOME PRECISA SER EXATO NO questionario_analisado.csv)
    # Use os nomes curtos 'PCT5.1', 'PC1.1.8.1', 'ADAI_PC2' pois o processador renomeia para estes.
    'PCT5.1_Sentimento_Geral': 'PCT5.1 - Sentimento Geral (Modos de Vida)',
    'PCT5.1_Sentimento_Satisfacao': 'PCT5.1 - Satisfação (Modos de Vida)',
    'PCT5.1_Sentimento_Emocao': 'PCT5.1 - Emoção (Modos de Vida)',
    'PCT5.1_Sentimento_Justificativa': 'PCT5.1 - Trecho Chave (Modos de Vida)', 
    
    'PC1.1.8.1_Sentimento_Geral': 'PC1.1.8.1 - Sentimento Geral (Sugestões Reparação)',
    'PC1.1.8.1_Sentimento_Satisfacao': 'PC1.1.8.1 - Satisfação (Sugestões Reparação)',
    'PC1.1.8.1_Sentimento_Emocao': 'PC1.1.8.1 - Emoção (Sugestões Reparação)',
    'PC1.1.8.1_Sentimento_Justificativa': 'PC1.1.8.1 - Trecho Chave (Sugestões Reparação)',

    'ADAI_PC2_Sentimento_Geral': 'ADAI_PC2 - Sentimento Geral (Avaliação Participação)',
    'ADAI_PC2_Sentimento_Satisfacao': 'ADAI_PC2 - Satisfação (Avaliação Participação)',
    'ADAI_PC2_Sentimento_Emocao': 'ADAI_PC2 - Emoção (Avaliação Participação)',
    'ADAI_PC2_Sentimento_Justificativa': 'ADAI_PC2 - Trecho Chave (Avaliação Participação)',
    
    # Condições de Acesso às Fontes Hídricas
    'DM11': 'DM11 - Tipo de esgotamento sanitário', 'DM12': 'DM12 - Abastecimento de energia elétrica', 'DM13': 'DM13 - Destino do lixo', 
    'ADAI_AQAMN2': 'ADAI_AQAMN2 - Uso doméstico de rios/açudes', 'AQA3': 'AQA3 - Dúvida sobre qualidade da água', 'AQA6.1': 'AQA6.1 - Avaliação da alteração na água', 
    'EC2': 'EC2 - Domicílio exposto a rejeitos?', 'ADAI_PCE1.2.1.1': 'ADAI_PCE1.2.1.1 - Dificuldade de acesso a outros equipamentos',

    # Condições de Saúde/Socioassistência
    'CAI1': 'CAI1 - Acesso à internet?', 'PCT2.1': 'PCT2.1 - Mudanças na relação com o território', 'EC4.2.2': 'EC4.2.2 - Doenças após enchentes', 
    'ADAI_CSS1': 'ADAI_CSS1 - Fatores de vulnerabilidade surgiram/aumentaram', 'CCS1': 'CCS1 - Fatores que influenciaram saúde da comunidade', 
    'CCS2': 'CCS2 - Fatores que influenciaram sua saúde', 'CCS3': 'CCS3 - Agravos de saúde surgiram?', 
    'CCS4.2.1': 'CCS4.2.1 - Onde buscou cuidado de saúde?', 'CCS4.2.1.1': 'CCS4.2.1.1 - Aumento busca UBS?', 
    'CCS5': 'CCS5 - Mantém práticas tradicionais de saúde?', 'CCS7': 'CCS7 - Aumento gastos com saúde?',

    # Segurança/Insegurança Alimentar
    'SA1': 'SA1 - Comprometimento qualidade de alimentos?', 'SA1.1': 'SA1.1 - Razão diminuição qualidade alimentos', 'SA3': 'SA3 - Diminuição quantidade de alimentos?', 
    'SA4': 'SA4 - Formas de acesso a alimentos ANTES', 'SA5': 'SA5 - Formas de acesso a alimentos DEPOIS', 
    'SA6.1': 'SA6.1 - Deixou de consumir alimento da região?', 'ADAI_SA7': 'ADAI_SA7 - Preocupação c/ falta de comida?',

    # Questões de Acesso aos Programas
    'ID13': 'ID13 - Acessava programas sociais ANTES?',
    'ID14': 'ID14 - Acessou programas sociais DEPOIS?', 
    'ID15': 'ID15 - Aumento atividades/tarefas mulheres?', 'ID15.1': 'ID15.1 - Quais atividades mulheres aumentaram?', 'ID15.2': 'ID15.2 - Quais atividades mulheres diminuíram?',
    'AD2': 'AD2 - Aumento de despesas?', 'AD2.2': 'AD2.2 - Quais despesas aumentaram?',
    'CAD1': 'CAD1 - Solicitou cadastro Renova?', 'CAD1.1': 'CAD1.1 - Categorias/danos informados no cadastro?', 'CAD1.1.1': 'CAD1.1.1 - Quais categorias/danos no cadastro?', 'CAD2': 'CAD2 - Recebeu resposta sobre cadastro?', 'CAD2.1': 'CAD2.1 - Cadastro aprovado?', 'CAD3': 'CAD3 - O que constou no cadastro correspondeu ao declarado?', 'CAD3.1': 'CAD3.1 - Solicitou revisão de cadastro?', 'CAD3.1.1': 'CAD3.1.1 - Cadastro revisado?', 'PRM1': 'PRM1 - Recebeu indenização individual?', 'PRM1.1': 'PRM1.1 - Não recebeu por recusar quitação geral?', 'PRM1.2': 'PRM1.2 - Informado sobre quitação geral (NOVEL)?', 'PRM1.2.1': 'PRM1.2.1 - Danos informados NOVEL?', 'PRM1.3': 'PRM1.3 - Informado sobre quitação geral (PIM)?', 'PRM1.3.1': 'PRM1.3.1 - Danos informados PIM?', 'PRM1.5': 'PRM1.5 - Informado sobre interrupção AFE?', 'PRM1.7': 'PRM1.7 - Dimensões não indenizadas NOVEL?', 'PRM1.8': 'PRM1.8 - Dimensões não indenizadas PIM?', 'PRM1.4': 'PRM1.4 - Recebeu parcelas anuais PIM?', 'PRM1.4.2': 'PRM1.4.2 - Por que parou de receber PIM?', 'PRM1.4.3': 'PRM1.4.3 - Valor PIM equivalente ao antes?',

    # Mudanças no Acesso a Benefícios Sociais e Políticas Públicas Pós-Rompimento
    'ID13.1': 'ID13.1 - Outros programas acessados ANTES?', 'ID14.1': 'ID14.1 - Outros programas acessados DEPOIS?', 'ID16': 'ID16 - Possui CADÚNICO?',

    # Impacto no Trabalho e na Renda
    'AER1': 'AER1 - Exercia atividade remunerada ANTES?', 
    'AER2': 'AER2 - Possuía empresa ANTES?', 'AER3': 'AER3 - Recebia outro recurso ANTES?', 'AER3.1': 'AER3.1 - De onde provinha outro recurso ANTES?',
    'ARF1.3': 'ARF1.3 - Atividades de subsistência ALTERADAS?', 'ARF1.3.3.1': 'ARF1.3.3.1 - Documento que comprove diminuição renda?',
    'ARF3.1': 'ARF3.1 - Documento que comprove perda de renda?', 'PRM3': 'PRM3 - Solicitou AFE?', 'PRM3.1': 'PRM3.1 - Recebeu AFE?', 'PRM3.1.1': 'PRM3.1.1 - Ainda recebe AFE?', 'PRM3.1.1.1': 'PRM3.1.1.1 - Justificativa cancelamento AFE?', 'PRM3.1.1.1.1': 'PRM3.1.1.1.1 - Motivo interrupção AFE?',
    'ARF1.1': 'ARF1.1 - Quais atividades de subsistência realizadas?', 

    # Endividamento e Perda de Patrimônio
    'DP1': 'DP1 - Patrimônio desvalorizou/perdeu valor?', 'DP2': 'DP2 - Vendeu patrimônio para se manter/quitar dívidas?',
    'DF1': 'DF1 - Contraiu/aumentou dívida?', 'DF1.1': 'DF1.1 - Tipo de dívida?', 'DF1.2': 'DF1.2 - Valor dívida atual?', 'DF1.4': 'DF1.4 - Documento que comprove dívida?',
}

# Dicionário para agrupar os códigos das questões
# Usamos os nomes curtos para as colunas de sentimento aqui
question_groups = {
    "Identificação": [
        'ID3', 'Idade', 'ID7', 'ADAI_ID8', 'ID8', 'ID9', 'ID10', 'ID10.1', 'ID11', 'ID12', 'ADAI_ID12', 'PCT0', 'NF1', 'ADAI_CT4'
    ], 
    "Sentimentos e Percepções": [ # Colunas de sentimentos - agora usando nomes curtos
        'PCT5.1_Sentimento_Geral', 'PCT5.1_Sentimento_Satisfacao', 'PCT5.1_Sentimento_Emocao', 'PCT5.1_Sentimento_Justificativa',
        'PC1.1.8.1_Sentimento_Geral', 'PC1.1.8.1_Sentimento_Satisfacao', 'PC1.1.8.1_Sentimento_Emocao', 'PC1.1.8.1_Sentimento_Justificativa',
        'ADAI_PC2_Sentimento_Geral', 'ADAI_PC2_Sentimento_Satisfacao', 'ADAI_PC2_Sentimento_Emocao', 'ADAI_PC2_Sentimento_Justificativa'
    ],
    "Condições de Acesso às Fontes Hídricas": [
        'DM11', 'DM12', 'DM13', 'ADAI_AQAMN2', 'AQA3', 'AQA6.1', 'EC2', 'ADAI_PCE1.2.1.1'
    ],
    "Condições de Saúde/Socioassistência": [
        'CAI1', 'PCT2.1', 'EC4.2.2', 'ADAI_CSS1', 'CCS1', 'CCS2', 'CCS3', 'CCS4.2.1', 'CCS4.2.1.1', 'CCS5', 'CCS7'
    ],
    "Segurança/Insegurança Alimentar": [
        'SA1', 'SA1.1', 'SA3', 'SA4', 'SA5', 'SA6.1', 'ADAI_SA7'
    ],
    "Questões de Acesso aos Programas": [
        'ID13', 'ID14', 'ID15', 'ID15.1', 'ID15.2', 'AD2', 'AD2.2', 'CAD1', 'CAD1.1', 'CAD1.1.1', 'CAD2', 'CAD2.1',
        'CAD3', 'CAD3.1', 'CAD3.1.1', 'PRM1', 'PRM1.1', 'PRM1.2', 'PRM1.2.1', 'PRM1.3', 'PRM1.3.1', 'PRM1.5',
        'PRM1.7', 'PRM1.8', 'PRM1.4', 'PRM1.4.2', 'PRM1.4.3'
    ],
    "Mudanças no Acesso a Benefícios Sociais e Políticas Públicas Pós-Rompimento": [
        'ID13', 'ID13.1', 'ID14', 'ID14.1', 'ID16'
    ],
    "Impacto no Trabalho e na Renda": [
        'AER1', 'AER2', 'AER3', 'AER3.1', 'ARF1.3', 'ARF1.3.3.1', 'ARF3.1', 'PRM3', 'PRM3.1', 'PRM3.1.1',
        'PRM3.1.1.1', 'PRM3.1.1.1.1'
    ],
    "Endividamento e Perda de Patrimônio": [
        'DP1', 'DP2', 'DF1', 'DF1.1', 'DF1.2', 'DF1.4'
    ]
}

# Filtra apenas as colunas que realmente existem no DataFrame principal (df_original_main)
available_cols_in_df_main = st.session_state.df_original_main.columns.tolist() 
# E as colunas de sentimento que existem no df_original_sentiment
available_cols_in_df_sentiment = st.session_state.df_original_sentiment.columns.tolist()

filtered_question_groups = {}
for group_name, cols in question_groups.items():
    if group_name == "Sentimentos e Percepções":
        # Para sentimentos, verifique se as colunas estão no df_sentiment
        filtered_cols = [col for col in cols if col in available_cols_in_df_sentiment]
    else:
        # Para outros grupos, verifique se as colunas estão no df_main
        filtered_cols = [col for col in cols if col in available_cols_in_df_main]

    if filtered_cols:
        filtered_question_groups[group_name] = filtered_cols

# all_selectable_categorical_cols deve incluir colunas de ambos os DFs se forem usadas para cruzamento
all_selectable_categorical_cols = sorted(list(set(
    [col for cols_list in filtered_question_groups.values() if cols_list for col in cols_list]
)))


# --- SIDEBAR (MENU LATERAL) ---
# Adicionando a logo
logo_path = "imagens/logo_adai.png" 
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, caption='https://adaibrasil.org.br/', use_container_width=True)
else:
    st.sidebar.warning(f"Logo não encontrada em: {logo_path}")

st.sidebar.title("Associação de Desenvolvimento Agrícola Interestadual | ADAI")
st.sidebar.markdown("---")

st.sidebar.header("Filtros Globais")

# Filters now apply to df_main
# Opções de localidade do DF principal
locality_options = ['Todas as Localidades'] + sorted(st.session_state.df_original_main['ADAI_CT4'].dropna().unique().tolist())
selected_locality = st.sidebar.selectbox(
    "Filtrar por Localidade:",
    locality_options,
    key="global_locality_filter"
)

gender_options = sorted(st.session_state.df_original_main['ADAI_ID8'].dropna().unique().tolist())
selected_gender = st.sidebar.multiselect(
    "Filtrar por Gênero:",
    gender_options,
    default=gender_options, # Seleciona todos por padrão
    key="global_gender_filter"
)

race_options = sorted(st.session_state.df_original_main['ID7'].dropna().unique().tolist())
selected_race = st.sidebar.multiselect(
    "Filtrar por Raça/Cor:",
    race_options,
    default=race_options, # Seleciona todos por padrão
    key="global_race_filter"
)

if 'Idade' in st.session_state.df_original_main.columns and not st.session_state.df_original_main['Idade'].dropna().empty:
    min_age = int(st.session_state.df_original_main['Idade'].min())
    max_age = int(st.session_state.df_original_main['Idade'].max())
    age_range = st.sidebar.slider(
        "Filtrar por Faixa Etária:",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age),
        key="global_age_filter"
    )
else:
    age_range = (0, 120)
    st.sidebar.info("Coluna 'Idade' não disponível ou sem dados para filtro.")

# --- Filtro Global por Sentimento (NOVO) ---
# Este filtro se baseia nas colunas de sentimento do DF de sentimentos
all_general_sentiment_cols_in_df_sentiment = [col for col in df_sentiment.columns if col.endswith('_Sentimento_Geral')]
available_sentiment_options = []
if all_general_sentiment_cols_in_df_sentiment:
    for col_s in all_general_sentiment_cols_in_df_sentiment:
        available_sentiment_options.extend(df_sentiment[col_s].dropna().unique().tolist())
    available_sentiment_options = sorted(list(set(available_sentiment_options)))

    selected_sentiment_filter = st.sidebar.multiselect(
        "Filtrar por Sentimento Geral (Análise):", 
        available_sentiment_options,
        default=available_sentiment_options,
        key="global_sentiment_filter_new"
    )
else:
    selected_sentiment_filter = []
    st.sidebar.info("Colunas de Sentimento Geral (de análise) não disponíveis para filtro. Execute o script de processamento.")


# --- Aplica todos os filtros ao DataFrame PRINCIPAL (df_main) ---
df_filtered_main = st.session_state.df_original_main.copy()

if selected_locality != 'Todas as Localidades':
    df_filtered_main = df_filtered_main[df_filtered_main['ADAI_CT4'] == selected_locality]

if selected_gender:
    df_filtered_main = df_filtered_main[df_filtered_main['ADAI_ID8'].isin(selected_gender)]

if selected_race:
    df_filtered_main = df_filtered_main[df_filtered_main['ID7'].isin(selected_race)]

df_filtered_main = df_filtered_main[
    (df_filtered_main['Idade'].fillna(-1) >= age_range[0]) & 
    (df_filtered_main['Idade'].fillna(-1) <= age_range[1])
]

# AQUI: Se o filtro de sentimento for aplicado, precisamos combiná-lo com o DF principal.
# Isso requer que ambos os DFs (principal e sentimento) tenham uma coluna de ID para merge.
# Assumindo que a coluna 'ID' é a chave para união
if selected_sentiment_filter and all_general_sentiment_cols_in_df_sentiment and 'ID' in df_main.columns and 'ID' in df_sentiment.columns:
    # Cria uma máscara no DF de sentimentos primeiro
    mask_sentiment_df = pd.Series(False, index=df_sentiment.index)
    for col_s in all_general_sentiment_cols_in_df_sentiment:
        if col_s in df_sentiment.columns:
            mask_sentiment_df = mask_sentiment_df | df_sentiment[col_s].isin(selected_sentiment_filter)
    
    # Pega os IDs dos respondentes que atendem ao filtro de sentimento
    ids_from_sentiment_filter = df_sentiment.loc[mask_sentiment_df, 'ID'].unique()
    
    # Filtra o DF principal usando esses IDs
    df_filtered_main = df_filtered_main[df_filtered_main['ID'].isin(ids_from_sentiment_filter)]
elif selected_sentiment_filter and not all_general_sentiment_cols_in_df_sentiment:
    st.sidebar.warning("Filtro de Sentimento Geral aplicado, mas as colunas de sentimento não foram encontradas no DataFrame de análise. Sem efeito.")


# Atualiza o DataFrame principal na session_state para todas as análises
st.session_state['df'] = df_filtered_main.copy()
df = st.session_state.df # Variável 'df' agora sempre aponta para o df principal filtrado

# --- DF de Sentimentos Filtrado (para uso nas análises de sentimento) ---
# Filtra o df_sentiment APENAS pelos IDs presentes no df_filtered_main.
# Isso garante que a análise de sentimento respeite os filtros demográficos.
if 'ID' in df_sentiment.columns and 'ID' in df.columns:
    df_sentiment_filtered_by_main = df_sentiment[df_sentiment['ID'].isin(df['ID'])]
else:
    df_sentiment_filtered_by_main = df_sentiment.copy() # Se não houver ID para merge, usa o DF de sentimento completo


# Feedback sobre o número de entrevistados após a filtragem
if not df.empty:
    st.sidebar.success(f"Dados filtrados. Total de **{len(df)}** entrevistados.")
else:
    st.sidebar.warning("Nenhum entrevistado encontrado com os filtros aplicados.")


st.sidebar.markdown("---")

modo_admin = st.sidebar.checkbox("🔧 Modo Admin (mostrar detalhes técnicos)", value=False)

st.sidebar.header("Escolha o Tipo de Análise")
analysis_type = st.sidebar.radio(
    "Selecione o tipo de análise:",
    (
     "🏠 Home",
     "Análise de Categoria Única",
     "Análise Cruzada de Questões",
     "Visualização por Mapa",
     "Análise de Sentimento por Tema",
     "Análise de Lacunas (Antes vs. Depois)",
     "Análise de Vulnerabilidade",
     "Sobre o Dashboard",
     "Sobre a IA"
     ),
    index=0,  # Sempre começa na Home
    key="main_analysis_type"
)
st.sidebar.info("Para informações institucionais, selecione as opções no menu acima.")


if analysis_type == "🏠 Home":
    # Conteúdo da Home
    st.title("📊 Dashboard de Análise do RF")
    st.markdown("---")
    st.markdown("""
    Bem-vindo ao painel de análise dos dados do RF!  
    <br>
    Este dashboard permite explorar e analisar os dados do questionário de forma dinâmica.  
    **Use o menu lateral** para selecionar o tipo de análise desejada:  
    - Visualize mapas, cruzamentos, gráficos, tabelas e relatórios.
    - Aplique filtros por território, raça/cor, gênero, faixa etária, etc.
    - Use a inteligência artificial para obter insights automáticos.
    
    <br>
    Para dúvidas ou sugestões, fale com a equipe técnica do projeto.
    """, unsafe_allow_html=True)
    # Você pode colocar aqui instruções, imagens, link para documentação, etc.

# ... os demais blocos

if modo_admin:
    st.success(f"Dados principais ('{FILE_PATH_MAIN_DATA}') carregados com sucesso! Total de {len(st.session_state.df_original_main)} linhas.")
    st.success(f"Dados de sentimento ('{FILE_PATH_SENTIMENT_DATA}') carregados com sucesso! Total de {len(st.session_state.df_original_sentiment)} linhas.")
    st.success("Dados carregados e painel pronto para análise.")
    st.success(f"Mapa GeoJSON ('{FILE_PATH_GEOJSON}') carregado com sucesso!")

st.sidebar.markdown("---")

st.sidebar.markdown("<h3 style='text-align: center;'>Ações e Informações</h3>", unsafe_allow_html=True)

st.sidebar.write("---")
if st.sidebar.button("Resetar Filtros", use_container_width=True):
    st.session_state['global_locality_filter'] = 'Todas as Localidades'
    if 'global_gender_filter' in st.session_state: st.session_state['global_gender_filter'] = gender_options
    if 'global_race_filter' in st.session_state: st.session_state['global_race_filter'] = race_options
    
    if 'Idade' in st.session_state.df_original_main.columns and not st.session_state.df_original_main['Idade'].dropna().empty:
        st.session_state['global_age_filter'] = (int(st.session_state.df_original_main['Idade'].min()), int(st.session_state.df_original_main['Idade'].max()))
    else: st.session_state['global_age_filter'] = (0, 120)

    if 'global_sentiment_filter_new' in st.session_state and available_sentiment_options: 
        st.session_state['global_sentiment_filter_new'] = available_sentiment_options
    elif 'global_sentiment_filter_new' in st.session_state:
        st.session_state['global_sentiment_filter_new'] = []
    
    st.session_state['df'] = st.session_state.df_original_main.copy() # Reseta para o DF principal original
    st.rerun() 

if st.sidebar.button("Limpar Dashboard", use_container_width=True):
    st.session_state['df'] = st.session_state.df_original_main.copy() # Limpa para o DF principal original
    if 'main_analysis_type' in st.session_state: del st.session_state['main_analysis_type'] 
    
    st.session_state['global_locality_filter'] = 'Todas as Localidades'
    if 'global_gender_filter' in st.session_state: st.session_state['global_gender_filter'] = gender_options
    if 'global_race_filter' in st.session_state: st.session_state['global_race_filter'] = race_options
    if 'Idade' in st.session_state.df_original_main.columns and not st.session_state.df_original_main['Idade'].dropna().empty:
        st.session_state['global_age_filter'] = (int(st.session_state.df_original_main['Idade'].min()), int(st.session_state.df_original_main['Idade'].max()))
    else: st.session_state['global_age_filter'] = (0, 120)
    if 'global_sentiment_filter_new' in st.session_state and available_sentiment_options:
        st.session_state['global_sentiment_filter_new'] = available_sentiment_options
    elif 'global_sentiment_filter_new' in st.session_state:
        st.session_state['global_sentiment_filter_new'] = []
            
    st.rerun()

st.sidebar.write("---")


st.markdown("---")

# --- Renderização do Conteúdo Principal com base no Tipo de Análise ---

# BLOCO 0: Sobre o Dashboard (Mantido, mas fora da ordem numérica para não confundir com os blocos que você pediu)
if analysis_type == "Sobre o Dashboard":
    st.header("Sobre o Dashboard, Metadados e Métodos Estatísticos")
    st.markdown("""
    ## O que é este painel?

    Este dashboard foi desenvolvido para **análise interativa, estatística e exploratória** dos dados coletados em questionários aplicados no contexto da pesquisa [NOME/TEMA DA PESQUISA]. O painel foi idealizado para facilitar a compreensão, interpretação e comunicação dos resultados tanto para especialistas quanto para gestores, pesquisadores e público geral.

    ### Principais funcionalidades do painel

    - Visualização dinâmica de dados categóricos, quantitativos e abertos.
    - Cruzamentos automáticos entre variáveis para identificar padrões, tendências e possíveis associações.
    - Visualização espacial (mapa) para análise territorial dos dados.
    - Análise de lacunas (antes vs. depois), vulnerabilidades e distribuição por grupo demográfico.
    - Download fácil das tabelas em formatos CSV e Excel.
    - Apoio automatizado de **Inteligência Artificial** para interpretação rápida de dados e respostas abertas.

    ## Metadados dos dados

    - **Fonte**: [descrever de onde vêm os dados, por exemplo: levantamento primário, instituição, projeto, etc.]
    - **População-alvo**: [descrever o perfil da população entrevistada]
    - **Período de coleta**: [data inicial - data final]
    - **Número de respondentes válidos**: [colocar número]
    - **Principais campos**: identificação, dados sociodemográficos, condições de saúde, trabalho, acesso a programas, percepções, sentimentos e impactos do rompimento.

    ## Métodos estatísticos e matemáticos aplicados

    - **Estatística descritiva**: cálculo de frequências absolutas e relativas, médias, medianas, mínimos, máximos, desvios-padrão (quando aplicável).
    - **Tabelas de contingência**: cruzamento automático de variáveis categóricas, análise de distribuições condicionais.
    - **Comparações de grupos**: filtros para subgrupos de acordo com território, idade, raça/cor, gênero, etc.
    - **Visualização**: gráficos de barras, pizza, histogramas, mapas de calor, mapas espaciais.
    - **Análise automatizada de texto**: uso de modelos de linguagem (IA) para classificação de sentimento, emoção e sumarização de respostas abertas.

    ## Limitações e recomendações

    - Os resultados apresentados são descritivos/exploratórios. Recomenda-se a análise detalhada por especialistas para interpretações finais.
    - Não há ponderação amostral automática (salvo ajuste manual).
    - Em respostas abertas, a classificação é feita por algoritmos de IA — sempre validar com revisão humana em casos sensíveis.
    - O painel depende da qualidade dos dados fornecidos (ausências, respostas múltiplas, inconsistências podem afetar as análises).

    ---
    **Dica:** Para entender como funciona a inteligência artificial do painel e seus limites, clique em "Sobre a IA" no menu lateral.
    """)

elif analysis_type == "Sobre a IA":
    st.header("Sobre a Inteligência Artificial do Painel")
    st.markdown("""
    Este painel utiliza **Inteligência Artificial (IA)** para auxiliar na análise e interpretação dos dados de duas formas principais:

    ### 1. Análise Automatizada de Respostas Abertas
    - As respostas de texto livre dos questionários passam por um processamento automatizado com IA de linguagem natural, que identifica **sentimentos gerais, emoções e justificativas chave**.
    - O modelo classifica sentimentos em categorias como “Muito Negativo”, “Negativo”, “Neutro”, “Positivo” e “Muito Positivo”, além de mapear emoções mais frequentes.
    - Trechos significativos das respostas podem ser destacados como exemplos para ilustrar o que os respondentes estão sentindo ou sugerindo.

    ### 2. Apoio à Interpretação dos Dados
    - A IA resume tendências estatísticas (mais frequentes), destaca mudanças relevantes e pode sugerir insights iniciais automaticamente a partir dos filtros aplicados.
    - As interpretações automáticas visam apoiar o usuário não-especialista, mas **não substituem a leitura crítica humana** dos dados.

    ### Como funciona a IA aqui?
    - O painel utiliza modelos avançados de linguagem (semelhantes ao ChatGPT), treinados para análise de sentimento e sumarização de dados.
    - Para cada filtro ou análise aplicada, a IA pode gerar resumos automáticos sobre o perfil da amostra, sentimentos predominantes e exemplos de justificativas, sempre com base apenas nos dados filtrados.
    - Nenhum dado pessoal identificável é exibido ou utilizado para treinamento posterior.

    ### Limitações e Boas Práticas
    - A IA é uma **ferramenta auxiliar**: sempre revise as interpretações, especialmente em temas sensíveis ou polêmicos.
    - Em caso de dúvidas ou dados ambíguos, priorize a avaliação por especialistas humanos.
    - A qualidade da análise automatizada depende da clareza e completude das respostas dos entrevistados.

    ---
    Para sugestões ou dúvidas sobre a IA do painel, consulte a equipe técnica responsável pelo projeto.
    """)


# BLOCO 1: Análise de Categoria Única
elif analysis_type == "Análise de Categoria Única":
    st.header("Análise de Categoria Única")
    st.write("Selecione um grupo e uma questão para ver sua distribuição de respostas.")

    if filtered_question_groups:
        selected_group = st.selectbox(
            "Selecione um Grupo de Questões:",
            list(filtered_question_groups.keys()),
            key="group_selector"
        )

        if selected_group:
            # Decide qual DF usar para este grupo
            if selected_group == "Sentimentos e Percepções":
                current_df_for_analysis = df_sentiment_filtered_by_main
            else:
                current_df_for_analysis = df  # df é o df_main filtrado
            
            cols_in_selected_group = [col for col in filtered_question_groups[selected_group] if col in current_df_for_analysis.columns]
            options_for_selectbox = [("Selecione uma questão", None)] + [(question_labels.get(col, col), col) for col in cols_in_selected_group]
            selected_option = st.selectbox(
                "Selecione uma Questão para Analisar:",
                options_for_selectbox,
                format_func=lambda x: x[0],
                key="single_question_selector"
            )
            selected_column = selected_option[1]

            if selected_column:
                is_numeric_column = pd.api.types.is_numeric_dtype(current_df_for_analysis[selected_column]) and selected_column != 'NF1'

                if is_numeric_column:
                    st.subheader(f"Distribuição de '{question_labels.get(selected_column, selected_column)}'")
                    fig_hist = px.histogram(
                        current_df_for_analysis.dropna(subset=[selected_column]),
                        x=selected_column,
                        title=f'Histograma de {question_labels.get(selected_column, selected_column)}',
                        nbins=20
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    st.markdown("#### Estatísticas Descritivas")
                    st.dataframe(current_df_for_analysis[selected_column].describe().to_frame(), use_container_width=True)

                else:
                    contagem_geral = current_df_for_analysis[selected_column].dropna().value_counts()
                    total_respostas = len(current_df_for_analysis[selected_column].dropna())

                    if total_respostas == 0:
                        st.warning(f"Nenhuma resposta encontrada para a questão '{question_labels.get(selected_column, selected_column)}'.")
                    else:
                        resultados_generais = pd.DataFrame({
                            'Resposta': contagem_geral.index,
                            'Número de Respostas': contagem_geral.values,
                            'Porcentagem (%)': (contagem_geral.values / total_respostas) * 100 
                        })
                        resultados_generais['Porcentagem (%)'] = resultados_generais['Porcentagem (%)'].round(2)
                        resultados_generais = resultados_generais.sort_values(by='Número de Respostas', ascending=False)

                        st.subheader(f"Distribuição de Respostas para '{question_labels.get(selected_column, selected_column)}'")

                        col_display, col_chart = st.columns(2)
                        with col_display:
                            display_mode_general = st.radio(
                                "Escolha o que exibir:",
                                ("Número de Respostas", "Porcentagem (%)"),
                                index=0,
                                key=f"display_mode_{selected_column}"
                            )
                        with col_chart:
                            chart_type_general = st.radio(
                                "Escolha o tipo de gráfico:",
                                ("Barra Vertical", "Barra Horizontal", "Pizza"),
                                index=0,
                                key=f"chart_type_{selected_column}"
                            )
                        
                        st.dataframe(resultados_generais, use_container_width=True)

                        csv_data = resultados_generais.to_csv(index=False).encode('utf-8')
                        st.download_button(label="Baixar Tabela como CSV", data=csv_data, file_name=f"{selected_column}_distribuicao.csv", mime="text/csv", key=f"download_csv_{selected_column}")
                        
                        excel_buffer = io.BytesIO()
                        resultados_generais.to_excel(excel_buffer, index=False, engine='xlsxwriter')
                        excel_buffer.seek(0)
                        st.download_button(label="Baixar Tabela como Excel", data=excel_buffer.getvalue(), file_name=f"{selected_column}_distribuicao.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"download_excel_{selected_column}")
                        st.markdown("---")
                        st.info("Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

                        if chart_type_general == "Barra Vertical":
                            fig_general = px.bar(resultados_generais, x='Resposta', y=display_mode_general, title=f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" ({display_mode_general})', color='Resposta', text_auto=True)
                            fig_general.update_layout(xaxis={'categoryorder':'total descending'})
                            st.plotly_chart(fig_general, use_container_width=True)
                        elif chart_type_general == "Barra Horizontal":
                            fig_general = px.bar(resultados_generais, y='Resposta', x=display_mode_general, title=f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" ({display_mode_general})', color='Resposta', orientation='h', text_auto=True)
                            fig_general.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_general, use_container_width=True)
                        elif chart_type_general == "Pizza":
                            fig_general = px.pie(resultados_generais, names='Resposta', values=display_mode_general, title=f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" ({display_mode_general})', hole=0.3)
                            st.plotly_chart(fig_general, use_container_width=True)
            else:
                st.info("Por favor, selecione uma questão para visualizar a análise.")
    else:
        st.warning("Nenhum grupo de colunas categóricas foi identificado para análise. Verifique seus dados.")

    # Detalhamento por Território, Gênero e Raça/Cor
    if 'selected_column' in locals() and selected_column and not ('is_numeric_column' in locals() and is_numeric_column): 
        st.markdown("---")
        st.subheader("Detalhamento por Variáveis Chave")
        st.write(f"Veja a distribuição da questão **'{question_labels.get(selected_column, selected_column)}'** cruzada com Território, Gênero e Raça/Cor.")

        df_detail_data = None
        if selected_group == "Sentimentos e Percepções":
            if 'ID' in df_sentiment_filtered_by_main.columns and 'ID' in df.columns:
                df_detail_data = df_sentiment_filtered_by_main[[selected_column, 'ID']].merge(
                    df[['ID', 'ADAI_CT4', 'ADAI_ID8', 'ID7']], on='ID', how='inner')
            else:
                st.warning("Para detalhamento de sentimentos, 'ID' é necessário em ambos os DataFrames.")
                df_detail_data = pd.DataFrame() 
        else:
            df_detail_data = df[[selected_column, 'ADAI_CT4', 'ADAI_ID8', 'ID7']]
        
        if df_detail_data is not None and not df_detail_data.empty:
            if 'ADAI_CT4' in df_detail_data.columns: 
                st.markdown("#### Por Território")
                df_cross_territory = df_detail_data[[selected_column, 'ADAI_CT4']].dropna()
                if not df_cross_territory.empty:
                    crosstab_territory = pd.crosstab(df_cross_territory[selected_column], df_cross_territory['ADAI_CT4'])
                    st.dataframe(crosstab_territory, use_container_width=True)
                    fig_territory = px.bar(crosstab_territory.reset_index().melt(id_vars=selected_column, var_name='Território', value_name='Contagem'), x=selected_column, y='Contagem', color='Território', barmode='group', title=f'Distribuição de {question_labels.get(selected_column, selected_column)} por Território', text_auto=True)
                    fig_territory.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_territory, use_container_width=True)
                else: st.info("Não há dados para cruzar com Território.")

            if 'ADAI_ID8' in df_detail_data.columns: 
                st.markdown("#### Por Gênero")
                df_cross_gender = df_detail_data[[selected_column, 'ADAI_ID8']].dropna()
                if not df_cross_gender.empty:
                    crosstab_gender = pd.crosstab(df_cross_gender[selected_column], df_cross_gender['ADAI_ID8'])
                    st.dataframe(crosstab_gender, use_container_width=True)
                    fig_gender = px.bar(crosstab_gender.reset_index().melt(id_vars=selected_column, var_name='Gênero', value_name='Contagem'), x=selected_column, y='Contagem', color='Gênero', barmode='group', title=f'Distribuição de {question_labels.get(selected_column, selected_column)} por Gênero', text_auto=True)
                    fig_gender.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_gender, use_container_width=True)
                else: st.info("Não há dados para cruzar com Gênero.")

            if 'ID7' in df_detail_data.columns: 
                st.markdown("#### Por Raça/Cor")
                df_cross_race = df_detail_data[[selected_column, 'ID7']].dropna()
                if not df_cross_race.empty:
                    crosstab_race = pd.crosstab(df_cross_race[selected_column], df_cross_race['ID7'])
                    st.dataframe(crosstab_race, use_container_width=True)
                    fig_race = px.bar(crosstab_race.reset_index().melt(id_vars=selected_column, var_name='Raça/Cor', value_name='Contagem'), x=selected_column, y='Contagem', color='Raça/Cor', barmode='group', title=f'Distribuição de {question_labels.get(selected_column, selected_column)} por Raça/Cor', text_auto=True)
                    fig_race.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_race, use_container_width=True)
                else: st.info("Não há dados para cruzar com Raça/Cor.")
        else:
            st.warning("Não há dados de detalhamento disponíveis após a combinação de DataFrames.")

    # --- ANÁLISE AUTOMÁTICA DA IA ---
    st.markdown("---")
    st.subheader("🤖 Análise Automática da IA (experimental)")
    mostrar_ia = st.toggle("Mostrar análise automática da IA para esta análise", value=False, key="toggle_ia_unica")
    if mostrar_ia:
        st.markdown("A IA pode gerar um resumo ou responder perguntas sobre os dados filtrados desta análise.")
        if "historico_ia_unica" not in st.session_state:
            st.session_state.historico_ia_unica = []
        if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_unica"):
            with st.spinner("A IA está analisando os dados..."):
                total_respondents = len(df)
                if total_respondents == 0:
                    ia_response = "**Não há dados para analisar com os filtros atuais.**"
                else:
                    gender_mode = df['ADAI_ID8'].mode()[0] if not df['ADAI_ID8'].empty else 'Não informado'
                    race_mode = df['ID7'].mode()[0] if not df['ID7'].empty else 'Não informado'
                    avg_age = f"{df['Idade'].mean():.1f}" if not df['Idade'].dropna().empty else 'N/A'
                    ia_response = f"""
**Resumo dos {total_respondents} entrevistados filtrados:**
- **Gênero mais frequente:** {gender_mode}
- **Raça/Cor mais representativa:** {race_mode}
- **Idade média:** {avg_age} anos

- **Sugestão:** Utilize a análise cruzada para aprofundar os insights.
- **Perguntas para a IA:**  
    - Quantos entrevistados são mulheres negras em Colatina?  
    - Qual o sentimento predominante sobre 'modos de vida' em Baixo Guandu?  
    - Como a renda mudou após o rompimento para povos tradicionais?
"""
                st.session_state.historico_ia_unica.append({"pergunta": "Resumo Automático", "resposta": ia_response})
                st.markdown(ia_response)
        pergunta_livre = st.text_input("Pergunte algo para a IA sobre os dados filtrados:", key="pergunta_livre_unica")
        if st.button("Perguntar à IA", key="perguntar_ia_unica"):
            try:
                import openai
                client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                sample = df.sample(min(len(df), 250)).to_dict(orient="records")
                user_question = f"Considere esta amostra dos dados: {sample}\nPergunta: {pergunta_livre}"
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                )
                ia_resp = completion.choices[0].message.content
            except Exception as e:
                ia_resp = f"Não foi possível usar IA externa (API): {e}"
            st.session_state.historico_ia_unica.append({"pergunta": pergunta_livre, "resposta": ia_resp})
            st.markdown("**Resposta da IA:**")
            st.write(ia_resp)
        if st.session_state.historico_ia_unica:
            with st.expander("Ver histórico de perguntas à IA"):
                for h in st.session_state.historico_ia_unica[::-1]:
                    st.markdown(f"**Pergunta:** {h['pergunta']}")
                    st.markdown(h["resposta"])
                    st.markdown("---")

# BLOCO 2: Análise Cruzada de Questões
elif analysis_type == "Análise Cruzada de Questões":
    st.header("Análise Cruzada de Questões")
    st.write("Selecione duas questões para ver a relação entre elas.")

    if len(all_selectable_categorical_cols) >= 2:
        options_for_cross_selectbox = [("Selecione uma questão", None)] + [(question_labels.get(col, col), col) for col in all_selectable_categorical_cols]
        selected_option_col1 = st.selectbox("Selecione a Questão Principal (Linhas):", options_for_cross_selectbox, format_func=lambda x: x[0], key="cross_col1")
        col1_cross = selected_option_col1[1]

        options_for_col2_cross = [("Selecione uma questão", None)] + [(question_labels.get(col, col), col) for col in all_selectable_categorical_cols if col != col1_cross]
        selected_option_col2 = st.selectbox("Selecione a Questão para Cruzar (Colunas):", options_for_col2_cross, format_func=lambda x: x[0], key="cross_col2")
        col2_cross = selected_option_col2[1]

        if col1_cross and col2_cross:
            temp_df_cross = None
            
            # Checa onde estão as colunas e faz merge se necessário
            if col1_cross in df.columns and col2_cross in df.columns:
                temp_df_cross = df[[col1_cross, col2_cross]]
            elif col1_cross in df_sentiment_filtered_by_main.columns and col2_cross in df_sentiment_filtered_by_main.columns:
                temp_df_cross = df_sentiment_filtered_by_main[[col1_cross, col2_cross]]
            elif 'ID' in df.columns and 'ID' in df_sentiment_filtered_by_main.columns:
                if col1_cross in df.columns and col2_cross in df_sentiment_filtered_by_main.columns:
                    temp_df_cross = df[[col1_cross, 'ID']].merge(df_sentiment_filtered_by_main[[col2_cross, 'ID']], on='ID', how='inner')
                elif col1_cross in df_sentiment_filtered_by_main.columns and col2_cross in df.columns:
                    temp_df_cross = df_sentiment_filtered_by_main[[col1_cross, 'ID']].merge(df[[col2_cross, 'ID']], on='ID', how='inner')
            
            if temp_df_cross is not None:
                df_cross = temp_df_cross.dropna()
            else:
                st.warning(f"Não foi possível encontrar ou combinar as colunas '{question_labels.get(col1_cross, col1_cross)}' e '{question_labels.get(col2_cross, col2_cross)}' para cruzamento. Verifique se estão nos DataFrames corretos e se há uma coluna 'ID' para união.")
                df_cross = pd.DataFrame()

            if df_cross.empty:
                st.warning(f"Não há dados para cruzar as questões '{question_labels.get(col1_cross, col1_cross)}' e '{question_labels.get(col2_cross, col2_cross)}' após remover valores em branco.")
            else:
                st.subheader(f"Cruzamento de '{question_labels.get(col1_cross, col1_cross)}' por '{question_labels.get(col2_cross, col2_cross)}'")

                col_cross_display, col_cross_chart = st.columns(2)
                with col_cross_display:
                    cross_display_mode = st.radio("Exibir como:", ("Contagem (Número de Entrevistados)", "Porcentagem por Linha", "Porcentagem por Coluna", "Porcentagem Total"), index=0, key="cross_display_mode")
                with col_cross_chart:
                    chart_type_cross = st.radio("Tipo de Gráfico Cruzado:", ("Barras Empilhadas", "Barras Agrupadas"), index=0, key="chart_type_cross")

                if cross_display_mode == "Contagem (Número de Entrevistados)": crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross])
                elif cross_display_mode == "Porcentagem por Linha": crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='index').mul(100).round(2)
                elif cross_display_mode == "Porcentagem por Coluna": crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='columns').mul(100).round(2)
                elif cross_display_mode == "Porcentagem Total": crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='all').mul(100).round(2)

                st.dataframe(crosstab_table, use_container_width=True)

                csv_data_cross = crosstab_table.to_csv().encode('utf-8')
                st.download_button(label="Baixar Tabela como CSV", data=csv_data_cross, file_name=f"{col1_cross}_x_{col2_cross}_cruzamento.csv", mime="text/csv", key=f"download_csv_cross_{col1_cross}_{col2_cross}")
                excel_buffer_cross = io.BytesIO()
                crosstab_table.to_excel(excel_buffer_cross, engine='xlsxwriter')
                excel_buffer_cross.seek(0)
                st.download_button(label="Baixar Tabela como Excel", data=excel_buffer_cross.getvalue(), file_name=f"{col1_cross}_x_{col2_cross}_cruzamento.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"download_excel_cross_{col1_cross}_{col2_cross}")
                st.markdown("---")
                st.info("Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

                st.subheader("Visualização Cruzada")
                plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Contagem')

                if chart_type_cross == "Barras Empilhadas":
                    fig_cross = px.bar(plot_df, x=col1_cross, y='Contagem', color=col2_cross, title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} (Empilhado)', text_auto=True)
                    fig_cross.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_cross, use_container_width=True)
                elif chart_type_cross == "Barras Agrupadas":
                    fig_cross = px.bar(plot_df, x=col1_cross, y='Contagem', color=col2_cross, barmode='group', title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} (Agrupado)', text_auto=True)
                    fig_cross.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_cross, use_container_width=True)
                
        else:
            st.info("Por favor, selecione duas questões para realizar a análise cruzada.")
    else:
        st.warning("Não há colunas categóricas suficientes para realizar a análise cruzada (mínimo de 2).")

    # --- ANÁLISE AUTOMÁTICA DA IA ---
    st.markdown("---")
    st.subheader("🤖 Análise Automática da IA (experimental)")
    mostrar_ia = st.toggle("Mostrar análise automática da IA para esta análise", value=False, key="toggle_ia_cruzada")
    if mostrar_ia:
        st.markdown("A IA pode gerar insights automáticos ou responder perguntas sobre o cruzamento apresentado acima.")
        if "historico_ia_cruzada" not in st.session_state:
            st.session_state.historico_ia_cruzada = []
        if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_cruzada"):
            with st.spinner("A IA está analisando os dados cruzados..."):
                if 'df_cross' in locals() and not df_cross.empty:
                    n = len(df_cross)
                    top_linhas = df_cross[col1_cross].mode()[0] if not df_cross[col1_cross].empty else 'N/A'
                    top_colunas = df_cross[col2_cross].mode()[0] if not df_cross[col2_cross].empty else 'N/A'
                    ia_resp = f"""
**Resumo do cruzamento:**
- Total de pares de respostas: {n}
- Valor mais frequente para "{question_labels.get(col1_cross, col1_cross)}": {top_linhas}
- Valor mais frequente para "{question_labels.get(col2_cross, col2_cross)}": {top_colunas}

- **Sugestão:** Observe as combinações de respostas com maior frequência para identificar padrões relevantes.
"""
                else:
                    ia_resp = "Não há dados cruzados suficientes para análise com a IA."
                st.session_state.historico_ia_cruzada.append({"pergunta": "Resumo Automático", "resposta": ia_resp})
                st.markdown(ia_resp)
        pergunta_livre = st.text_input("Pergunte algo para a IA sobre o cruzamento:", key="pergunta_livre_cruzada")
        if st.button("Perguntar à IA", key="perguntar_ia_cruzada"):
            try:
                import openai
                client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                sample = df_cross.sample(min(len(df_cross), 250)).to_dict(orient="records")
                user_question = f"Considere esta amostra do cruzamento de duas colunas: {sample}\nPergunta: {pergunta_livre}"
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                )
                ia_resp = completion.choices[0].message.content
            except Exception as e:
                ia_resp = f"Não foi possível usar IA externa (API): {e}"
            st.session_state.historico_ia_cruzada.append({"pergunta": pergunta_livre, "resposta": ia_resp})
            st.markdown("**Resposta da IA:**")
            st.write(ia_resp)
        if st.session_state.historico_ia_cruzada:
            with st.expander("Ver histórico de perguntas à IA"):
                for h in st.session_state.historico_ia_cruzada[::-1]:
                    st.markdown(f"**Pergunta:** {h['pergunta']}")
                    st.markdown(h["resposta"])
                    st.markdown("---")

# BLOCO 3: Visualização por Mapa 
elif analysis_type == "Visualização por Mapa":
    st.header("Visualização por Mapa")
    st.info("Este mapa exibe a distribuição espacial dos municípios onde há respondentes. O tamanho do círculo indica o número de respondentes.")
    st.markdown("---")

    # Posição central do ES
    center = [-19.5, -40.5]

    # --- Cria DataFrame de municípios e total de respondentes
    df_map_data = df.groupby('ADAI_CT4').size().reset_index(name='Total Respondentes')
    df_map_data = df_map_data.rename(columns={'ADAI_CT4': 'nome'}) 

    # Merge com lat/lon
    lat_lon_df = pd.read_csv('data/municipios_es_lat_lon.csv', sep=';', encoding='utf-8')
    df_map_data = df_map_data.merge(lat_lon_df, on='nome', how='left')

    # Total de homens/mulheres por município
    sexo_counts = (
        df[df['ADAI_ID8'].isin(['Homem', 'Mulher'])]
        .groupby(['ADAI_CT4', 'ADAI_ID8']).size().unstack(fill_value=0)
        .reset_index().rename(columns={'ADAI_CT4': 'nome'})
    )
    df_map_data = df_map_data.merge(sexo_counts, on='nome', how='left')

    df_map_data['Pct_Homens'] = (df_map_data.get('Homem', 0) / df_map_data['Total Respondentes'] * 100).round(1)
    df_map_data['Pct_Mulheres'] = (df_map_data.get('Mulher', 0) / df_map_data['Total Respondentes'] * 100).round(1)

    # Profissão mais comum por município
    profissao_pred = (
        df.groupby('ADAI_CT4')['ADAI_ID12']
        .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
        .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ADAI_ID12': 'Profissao_Predominante'})
    )
    df_map_data = df_map_data.merge(profissao_pred, on='nome', how='left')

    # Escolaridade mais comum
    escolaridade_pred = (
        df.groupby('ADAI_CT4')['ID11']
        .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
        .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID11': 'Escolaridade_Predominante'})
    )
    df_map_data = df_map_data.merge(escolaridade_pred, on='nome', how='left')

    # Religião mais comum
    religiao_pred = (
        df.groupby('ADAI_CT4')['ID12']
        .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
        .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID12': 'Religiao_Predominante'})
    )
    df_map_data = df_map_data.merge(religiao_pred, on='nome', how='left')

    # Povo tradicional: % de respondentes por município
    povo_pct = (
        df[df['PCT0'] == 'Sim']
        .groupby('ADAI_CT4').size() / df.groupby('ADAI_CT4').size()
    ).mul(100).round(1).reset_index(name='Pct_Povo_Tradicional')
    povo_pct = povo_pct.rename(columns={'ADAI_CT4': 'nome'})
    df_map_data = df_map_data.merge(povo_pct, on='nome', how='left')

    # Deficiência: % de respondentes com deficiência
    if 'Deficiencia' in df.columns:
        def_pct = (
            df[df['Deficiencia'] == 'Sim']
            .groupby('ADAI_CT4').size() / df.groupby('ADAI_CT4').size()
        ).mul(100).round(1).reset_index(name='Pct_Deficiencia')
        def_pct = def_pct.rename(columns={'ADAI_CT4': 'nome'})
        df_map_data = df_map_data.merge(def_pct, on='nome', how='left')
    else:
        df_map_data['Pct_Deficiencia'] = None

    # Raça/cor: mais comum por município
    raca_pred = (
        df.groupby('ADAI_CT4')['ID7']
        .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
        .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID7': 'Raca_Predominante'})
    )
    df_map_data = df_map_data.merge(raca_pred, on='nome', how='left')

    # --- Remover colunas duplicadas de 'nome'
    df_map_data = df_map_data.loc[:, ~df_map_data.columns.duplicated()]

    # Set dos municípios com respostas
    municipios_com_respostas = set(df_map_data['nome'])

    # Função melhorada para popup: mostra mais detalhes e emojis
    def make_popup(row):
        return folium.Popup(f"""
            <b>{row['nome']}</b><br>
            👤 <b>Total respondentes:</b> {row['Total Respondentes']}<br>
            👩 <b>Mulheres:</b> {row.get('Mulher', 0)} ({row.get('Pct_Mulheres', 0)}%)<br>
            👨 <b>Homens:</b> {row.get('Homem', 0)} ({row.get('Pct_Homens', 0)}%)<br>
            🧑‍🦱 <b>Raça predominante:</b> {row.get('Raca_Predominante', 'n/d')}<br>
            🎓 <b>Escolaridade predominante:</b> {row.get('Escolaridade_Predominante', 'n/d')}<br>
            💼 <b>Profissão predominante:</b> {row.get('Profissao_Predominante', 'n/d')}<br>
            🙏 <b>Religião predominante:</b> {row.get('Religiao_Predominante', 'n/d')}<br>
            🌱 <b>% Povo tradicional:</b> {row.get('Pct_Povo_Tradicional', 0)}%<br>
            ♿ <b>% com deficiência:</b> {row.get('Pct_Deficiencia', 'n/d')}%
        """, max_width=350)

    # --- Mapa Folium dos limites do ES
    m = folium.Map(location=center, zoom_start=7, tiles='cartodbpositron')

    for feature in estados_geojson['features']:
        nome_municipio_geojson = feature['properties'].get('name')
        if nome_municipio_geojson in municipios_com_respostas:
            color = '#ffe74c'
            fill_opacity = 0.8
            row = df_map_data[df_map_data['nome'] == nome_municipio_geojson].iloc[0]
            popup = make_popup(row)
        else:
            color = '#c0c0c0'
            fill_opacity = 0.2
            popup = None

        folium.GeoJson(
            feature,
            style_function=lambda x, color=color, fill_opacity=fill_opacity: {
                'fillColor': color,
                'color': 'black',
                'weight': 1,
                'fillOpacity': fill_opacity
            },
            tooltip=nome_municipio_geojson,
            popup=popup
        ).add_to(m)

   # folium_static(m, width=900, height=650)

    # --- Mapa Plotly dos pontos
    if 'lat' in df_map_data.columns and 'lon' in df_map_data.columns and not df_map_data[['lat', 'lon']].isna().all().all():
        try:
            lat_center = df_map_data["lat"].mean()
            lon_center = df_map_data["lon"].mean()
            fig_map = px.scatter_mapbox(
                df_map_data,
                lat="lat",
                lon="lon",
                size="Total Respondentes",
                color="Total Respondentes",
                color_continuous_scale=px.colors.sequential.Viridis,
                hover_name="nome",
                hover_data={
                    "Total Respondentes": True,
                    "Mulher": True,
                    "Homem": True,
                    "Pct_Mulheres": True,
                    "Pct_Homens": True,
                    "Profissao_Predominante": True,
                    "Escolaridade_Predominante": True,
                    "Religiao_Predominante": True,
                    "Pct_Povo_Tradicional": True,
                    "Pct_Deficiencia": True,
                    "Raca_Predominante": True,
                    "lat": False, "lon": False
                },
                mapbox_style="carto-positron",
                zoom=6,
                center={"lat": lat_center, "lon": lon_center},
                title="Total de Respondentes por Município (Mapa de Pontos)"
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar o mapa Plotly: {e}")
    else:
        st.warning("Não há coordenadas (lat/lon) dos municípios no DataFrame para plotar pontos no mapa. Exibindo apenas a tabela.")

    # --- Exibe tabela e download
    st.markdown("#### Detalhes por Município (Mapa)")
    st.dataframe(df_map_data[['nome', 'Total Respondentes', 'Homem', 'Mulher', 'Pct_Mulheres', 'Profissao_Predominante',
                         'Escolaridade_Predominante', 'Religiao_Predominante', 'Pct_Povo_Tradicional',
                         'Pct_Deficiencia', 'Raca_Predominante']], use_container_width=True)
    st.download_button("Baixar Tabela Municípios", df_map_data.to_csv(index=False), file_name="municipios_respondentes.csv")

    # --- ANÁLISE AUTOMÁTICA DA IA ---
    st.markdown("---")
    st.subheader("🤖 Análise Automática da IA (experimental)")
    mostrar_ia = st.toggle("Mostrar análise automática da IA para o mapa", value=False, key="toggle_ia_mapa")
    st.markdown("---")
    if mostrar_ia:
        st.markdown("A IA pode gerar um resumo ou responder perguntas sobre os municípios e variáveis deste mapa.")
        if "historico_ia_mapa" not in st.session_state:
            st.session_state.historico_ia_mapa = []
        if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_mapa"):
            with st.spinner("A IA está analisando a distribuição geográfica..."):
                n = len(df_map_data)
                top_cidade = df_map_data.sort_values('Total Respondentes', ascending=False).iloc[0] if n > 0 else None
                if n == 0 or top_cidade is None:
                    ia_response = "**Não há dados geográficos para análise com os filtros atuais.**"
                else:
                    ia_response = f"""
**Resumo da distribuição espacial:**
- **Total de municípios com respondentes:** {n}
- **Município com mais respondentes:** {top_cidade['nome']} ({top_cidade['Total Respondentes']} pessoas)
- **% média de mulheres:** {df_map_data['Pct_Mulheres'].mean():.1f}%
- **% média de povos tradicionais:** {df_map_data['Pct_Povo_Tradicional'].mean():.1f}%
- **% média com deficiência:** {df_map_data['Pct_Deficiencia'].mean():.1f}%

- **Sugestão:** Clique sobre um município no mapa para detalhes e use filtros para comparar perfis.
"""
                st.session_state.historico_ia_mapa.append({"pergunta": "Resumo Automático", "resposta": ia_response})
                st.markdown(ia_response)
        pergunta_livre = st.text_input("Pergunte algo para a IA sobre os municípios ou o mapa:", key="pergunta_livre_mapa")
        if st.button("Perguntar à IA", key="perguntar_ia_mapa"):
            try:
                import openai
                client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                sample = df_map_data.sample(min(len(df_map_data), 80)).to_dict(orient="records")
                user_question = f"Considere esta amostra dos dados de municípios: {sample}\nPergunta: {pergunta_livre}"
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                )
                ia_resp = completion.choices[0].message.content
            except Exception as e:
                ia_resp = f"Não foi possível usar IA externa (API): {e}"
            st.session_state.historico_ia_mapa.append({"pergunta": pergunta_livre, "resposta": ia_resp})
            st.markdown("**Resposta da IA:**")
            st.write(ia_resp)
        if st.session_state.historico_ia_mapa:
            with st.expander("Ver histórico de perguntas à IA"):
                for h in st.session_state.historico_ia_mapa[::-1]:
                    st.markdown(f"**Pergunta:** {h['pergunta']}")
                    st.markdown(h["resposta"])
                    st.markdown("---")


# BLOCO 4: Análise de Sentimento por Tema
elif analysis_type == "Análise de Sentimento por Tema":
    st.header("Análise de Sentimento por Tema")
    st.markdown("Explore os sentimentos e emoções expressos nas respostas de texto livre para diferentes tópicos.")

    current_df_sentiment = df_sentiment_filtered_by_main

    # --- Opção de gráfico
    chart_type = st.radio("Tipo de gráfico:", ["Pizza", "Barras"], horizontal=True, key="sentiment_chart_type")

    # Sentiment columns (ajuste conforme seus dados reais)
    sentiment_text_columns = {
        'PCT5.1_Sentimento_Geral': 'Perdas/Modos de Vida (Geral)',
        'PCT5.1_Sentimento_Satisfacao': 'Perdas/Modos de Vida (Satisfação)',
        'PCT5.1_Sentimento_Emocao': 'Perdas/Modos de Vida (Emoção)',
        'PCT5.1_Sentimento_Justificativa': 'Perdas/Modos de Vida (Trechos Chave)',
        # ... [adicione outros mapeamentos conforme seu dicionário]
    }
    available_sentiment_cols = {k: v for k, v in sentiment_text_columns.items() if k in current_df_sentiment.columns}

    if not available_sentiment_cols:
        st.warning("Nenhuma coluna de sentimento encontrada.")
    else:
        selected_sentiment_display_type = st.radio(
            "Visualizar por:",
            ["Sentimento Geral", "Satisfação", "Emoção", "Trechos Chave"],
            key="sentiment_display_type"
        )

        filtered_sentiment_options_for_selectbox = {}
        for col_code, col_label in available_sentiment_cols.items():
            if selected_sentiment_display_type == "Sentimento Geral" and col_code.endswith('_Sentimento_Geral'):
                filtered_sentiment_options_for_selectbox[col_code] = col_label
            elif selected_sentiment_display_type == "Satisfação" and col_code.endswith('_Sentimento_Satisfacao'):
                filtered_sentiment_options_for_selectbox[col_code] = col_label
            elif selected_sentiment_display_type == "Emoção" and col_code.endswith('_Sentimento_Emocao'):
                filtered_sentiment_options_for_selectbox[col_code] = col_label
            elif selected_sentiment_display_type == "Trechos Chave" and col_code.endswith('_Sentimento_Justificativa'):
                filtered_sentiment_options_for_selectbox[col_code] = col_label

        if not filtered_sentiment_options_for_selectbox:
            st.info(f"Nenhum dado de '{selected_sentiment_display_type}' disponível.")
        else:
            selected_sentiment_topic_code = st.selectbox(
                f"Selecione a pergunta para analisar {selected_sentiment_display_type}:",
                list(filtered_sentiment_options_for_selectbox.keys()),
                format_func=lambda x: filtered_sentiment_options_for_selectbox[x],
                key="sentiment_topic_code_selector"
            )

            # Só daqui para baixo pode acessar selected_sentiment_topic_code!
            if selected_sentiment_topic_code:
                # ----- Tudo protegido! -----
                total = current_df_sentiment[selected_sentiment_topic_code].notna().sum()
                sentiment_counts_abs = current_df_sentiment[selected_sentiment_topic_code].value_counts().reset_index()
                sentiment_counts_abs.columns = ['Categoria', 'Quantidade']
                sentiment_counts_abs['Porcentagem (%)'] = (sentiment_counts_abs['Quantidade']/total*100).round(2)
                st.markdown("##### Tabela de Distribuição dos Sentimentos")
                st.dataframe(sentiment_counts_abs, use_container_width=True)

                st.download_button(
                    "Baixar distribuição (CSV)",
                    sentiment_counts_abs.to_csv(index=False),
                    file_name=f"sentimentos_{selected_sentiment_topic_code}.csv"
                )

                # --- Gráfico
                if chart_type == "Pizza":
                    fig_sentiment = px.pie(
                        sentiment_counts_abs,
                        names='Categoria',
                        values='Quantidade',
                        title=f'Distribuição de {filtered_sentiment_options_for_selectbox[selected_sentiment_topic_code]}',
                        hole=0.3
                    )
                else:  # Barras
                    fig_sentiment = px.bar(
                        sentiment_counts_abs.sort_values("Quantidade", ascending=False),
                        x='Categoria',
                        y='Quantidade',
                        text='Porcentagem (%)',
                        title=f'Distribuição de {filtered_sentiment_options_for_selectbox[selected_sentiment_topic_code]}'
                    )
                    fig_sentiment.update_layout(xaxis_title="", yaxis_title="Quantidade")
                st.plotly_chart(fig_sentiment, use_container_width=True)

                # --- Nuvem de palavras (opcional)
                original_col_prefix = selected_sentiment_topic_code.rsplit('_', 2)[0]
                justification_col_name = f"{original_col_prefix}_Sentimento_Justificativa"
                mostrar_nuvem = st.checkbox("Mostrar nuvem de palavras dos trechos chave (experimental)")
                if mostrar_nuvem:
                    try:
                        from wordcloud import WordCloud
                        import matplotlib.pyplot as plt
                        textos = current_df_sentiment[justification_col_name].dropna().str.cat(sep=' ')
                        wordcloud = WordCloud(width=800, height=300, background_color='white').generate(textos)
                        fig_wc, ax = plt.subplots(figsize=(10,3))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig_wc)
                    except Exception as e:
                        st.warning(f"Não foi possível gerar a nuvem de palavras: {e}")

                # --- Exemplos de Trechos Chave + download
                if justification_col_name in current_df_sentiment.columns:
                    all_samples = current_df_sentiment[justification_col_name].dropna().tolist()
                    st.download_button(
                        "Baixar trechos chave (TXT)",
                        "\n".join(all_samples),
                        file_name=f"trechos_{selected_sentiment_topic_code}.txt"
                    )
                else:
                    st.info("Não há coluna de trechos chave para esta seleção.")

                # --- Análise automática da IA
                st.markdown("---")
                st.subheader("🤖 Análise Automática da IA (experimental)")
                mostrar_ia = st.toggle("Mostrar análise da IA para os sentimentos", value=False, key="toggle_ia_sentimentos")
                st.markdown("---")
                if mostrar_ia:
                    st.markdown("A IA pode gerar um resumo automático ou responder perguntas sobre os sentimentos.")
                    if "historico_ia_sentimentos" not in st.session_state:
                        st.session_state.historico_ia_sentimentos = []
                    if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_sent"):
                        with st.spinner("A IA está analisando os sentimentos..."):
                            n = total
                            top = sentiment_counts_abs.iloc[0] if n > 0 else None
                            if n == 0 or top is None:
                                ia_response = "**Não há dados para análise com os filtros atuais.**"
                            else:
                                ia_response = f"""
**Resumo dos sentimentos analisados:**
- **Total de exemplos analisados:** {n}
- **Sentimento/Categoria mais citada:** {top['Categoria']} ({top['Quantidade']} respostas, {top['Porcentagem (%)']}%)
- **Distribuição geral:** {dict(zip(sentiment_counts_abs['Categoria'], sentiment_counts_abs['Porcentagem (%)']))}
- **Sugestão:** Veja exemplos reais abaixo ou filtre por tópicos para aprofundar.
"""
                            st.session_state.historico_ia_sentimentos.append({"pergunta": "Resumo Automático", "resposta": ia_response})
                            st.markdown(ia_response)
                    pergunta_livre = st.text_input("Pergunte algo para a IA sobre os sentimentos ou as citações:", key="pergunta_livre_sent")
                    if st.button("Perguntar à IA", key="perguntar_ia_sent"):
                        try:
                            import openai
                            client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                            sample = current_df_sentiment[[selected_sentiment_topic_code, justification_col_name]].dropna().sample(min(40, len(current_df_sentiment))).to_dict(orient="records")
                            user_question = f"Considere esta amostra dos sentimentos e justificativas: {sample}\nPergunta: {pergunta_livre}"
                            completion = client.chat.completions.create(
                                model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                            )
                            ia_resp = completion.choices[0].message.content
                        except Exception as e:
                            ia_resp = f"Não foi possível usar IA externa (API): {e}"
                        st.session_state.historico_ia_sentimentos.append({"pergunta": pergunta_livre, "resposta": ia_resp})
                        st.markdown("**Resposta da IA:**")
                        st.write(ia_resp)
                    if st.session_state.historico_ia_sentimentos:
                        with st.expander("Ver histórico de perguntas à IA"):
                            for h in st.session_state.historico_ia_sentimentos[::-1]:
                                st.markdown(f"**Pergunta:** {h['pergunta']}")
                                st.markdown(h["resposta"])
                                st.markdown("---")


# BLOCO 5: Análise de Lacunas (Antes vs. Depois)
elif analysis_type == "Análise de Lacunas (Antes vs. Depois)":
    st.header("Análise de Lacunas: Antes vs. Depois do Rompimento")
    st.markdown("Compare a situação dos respondentes antes e depois do rompimento da barragem em áreas chave para identificar as principais lacunas e impactos.")

    gap_analysis_pairs = {
        "Acesso a Programas Sociais (ID13/ID14)": ('ID13', 'ID14'),
        "Acesso à Água do Rio Doce (AQA1/AQA2)": ('AQA1', 'AQA2'),
        "Exercia Atividade Remunerada (AER1/ARF1.1)": ('AER1', 'ARF1.1'), 
    }
    available_gap_pairs = {k:v for k,v in gap_analysis_pairs.items() if v[0] in df.columns and v[1] in df.columns}

    if not available_gap_pairs:
        st.warning("Nenhum par de perguntas 'Antes/Depois' encontrado para análise de lacunas.")
    else:
        selected_gap_pair_label = st.selectbox(
            "Selecione a Dimensão para Análise de Lacunas:",
            list(available_gap_pairs.keys()),
            key="gap_pair_selector"
        )

        if selected_gap_pair_label:
            col_antes, col_depois = available_gap_pairs[selected_gap_pair_label]

            st.subheader(f"Comparativo: {question_labels.get(col_antes, col_antes)} vs. {question_labels.get(col_depois, col_depois)}")
            df_gap = df[[col_antes, col_depois]].dropna()

            if not df_gap.empty:
                counts_antes = df_gap[col_antes].value_counts(normalize=True).mul(100).round(2).reset_index()
                counts_antes.columns = ['Resposta', 'Porcentagem (%)']
                counts_antes['Período'] = 'Antes do Rompimento'

                counts_depois = df_gap[col_depois].value_counts(normalize=True).mul(100).round(2).reset_index()
                counts_depois.columns = ['Resposta', 'Porcentagem (%)']
                counts_depois['Período'] = 'Depois do Rompimento'

                combined_counts = pd.concat([counts_antes, counts_depois])

                fig_gap = px.bar(
                    combined_counts,
                    x='Resposta',
                    y='Porcentagem (%)',
                    color='Período',
                    barmode='group',
                    title=f'Comparativo de "{selected_gap_pair_label}" Antes e Depois do Rompimento',
                    text_auto=True
                )
                fig_gap.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_gap, use_container_width=True)

                st.markdown("#### Tabela Comparativa (Porcentagens)")
                crosstab_gap = pd.crosstab(df_gap[col_antes], df_gap[col_depois], normalize='index').mul(100).round(2)
                st.dataframe(crosstab_gap, use_container_width=True)
                st.info("A tabela acima mostra a porcentagem de respondentes de uma categoria 'Antes' que caíram em cada categoria 'Depois'.")

                kpi_text = ""
                if 'Sim' in counts_antes['Resposta'].values and 'Sim' in counts_depois['Resposta'].values:
                    perc_antes_sim = counts_antes[counts_antes['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
                    perc_depois_sim = counts_depois[counts_depois['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
                    kpi_text = (
                        f"**KPI:** A porcentagem de respondentes que afirmam '{selected_gap_pair_label}' (resposta 'Sim') mudou de **{perc_antes_sim:.1f}%** antes para **{perc_depois_sim:.1f}%** depois do rompimento. "
                        f"Isso representa uma **mudança de {perc_depois_sim - perc_antes_sim:.1f} pontos percentuais**."
                    )
                    st.markdown(kpi_text)

                # --- IA: Resumo Automático
                st.markdown("---")
                st.subheader("🤖 Análise Automática da IA (experimental)")
                mostrar_ia = st.toggle("Mostrar análise automática da IA para esta lacuna", value=False, key="toggle_ia_gap")
                if mostrar_ia:
                    st.markdown("---")
                    st.markdown("A IA pode gerar um resumo interpretando as mudanças entre antes e depois ou responder perguntas livres.")
                    if "historico_ia_gap" not in st.session_state:
                        st.session_state.historico_ia_gap = []
                    if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_gap"):
                        with st.spinner("A IA está analisando os dados..."):
                            resumo = f"""
**Resumo IA - Análise Antes vs. Depois:**
- **Dimensão:** {selected_gap_pair_label}
- **Principais mudanças:** {kpi_text if kpi_text else "Veja as tabelas acima."}
- **Distribuição Antes:** {dict(zip(counts_antes['Resposta'], counts_antes['Porcentagem (%)']))}
- **Distribuição Depois:** {dict(zip(counts_depois['Resposta'], counts_depois['Porcentagem (%)']))}
"""
                            st.session_state.historico_ia_gap.append({"pergunta": "Resumo Automático", "resposta": resumo})
                            st.markdown(resumo)
                    pergunta_livre = st.text_input("Pergunte algo à IA sobre essa lacuna:", key="pergunta_livre_gap")
                    if st.button("Perguntar à IA", key="perguntar_ia_gap"):
                        try:
                            import openai
                            client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                            sample = df_gap.sample(min(40, len(df_gap))).to_dict(orient="records")
                            user_question = f"Considere esta amostra dos dados antes/depois: {sample}\nPergunta: {pergunta_livre}"
                            completion = client.chat.completions.create(
                                model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                            )
                            ia_resp = completion.choices[0].message.content
                        except Exception as e:
                            ia_resp = f"Não foi possível usar IA externa (API): {e}"
                        st.session_state.historico_ia_gap.append({"pergunta": pergunta_livre, "resposta": ia_resp})
                        st.markdown("**Resposta da IA:**")
                        st.write(ia_resp)
                    if st.session_state.historico_ia_gap:
                        with st.expander("Ver histórico de perguntas à IA (lacunas)"):
                            for h in st.session_state.historico_ia_gap[::-1]:
                                st.markdown(f"**Pergunta:** {h['pergunta']}")
                                st.markdown(h["resposta"])
                                st.markdown("---")
            else:
                st.warning("Não há dados válidos para este par de análise de lacunas com os filtros atuais.")
        else:
            st.info("Por favor, selecione uma dimensão para a análise de lacunas.")

# BLOCO 6: Análise de Vulnerabilidade
elif analysis_type == "Análise de Vulnerabilidade":
    st.header("Análise de Vulnerabilidade")
    st.markdown("Explore como diferentes grupos demográficos foram impactados ou percebem a situação, identificando potenciais vulnerabilidades.")

    vulnerability_vars = {
        'ID7': 'Raça/Cor',
        'ADAI_ID8': 'Gênero',
        'ID10': 'Pessoa com Deficiência',
        'PCT0': 'Povo/Comunidade Tradicional',
    }

    impact_vars = {
        'PCT5.1_Sentimento_Geral': 'Perdas/Modos de Vida (Sentimento Geral)',
        'PCT5.1_Sentimento_Emocao': 'Perdas/Modos de Vida (Emoção)',
        'PC1.1.8.1_Sentimento_Satisfacao': 'Sugestões Reparação (Satisfação)',
        'ADAI_PC2_Sentimento_Geral': 'Avaliação Participação (Sentimento Geral)',
        'ARF3.1': 'Perda de Renda (Comprovada)', 
        'DF1': 'Dívida Contraída/Aumentada',
        'SA1': 'Comprometimento Qualidade Alimentos',
        'CCS7': 'Aumento Gastos Saúde',
    }
    
    available_impact_vars = {k:v for k,v in impact_vars.items() if k in df.columns or k in df_sentiment.columns}

    if not available_impact_vars:
        st.warning("Nenhuma variável de impacto encontrada para análise de vulnerabilidade.")
    else:
        selected_v_var = st.selectbox(
            "Selecione a Variável Demográfica/Vulnerabilidade:",
            list(vulnerability_vars.keys()),
            format_func=lambda x: vulnerability_vars[x],
            key="v_var_selector"
        )

        selected_impact_var = st.selectbox(
            "Selecione a Variável de Impacto:",
            list(available_impact_vars.keys()),
            format_func=lambda x: available_impact_vars[x],
            key="impact_var_selector"
        )

        if selected_v_var and selected_impact_var:
            st.subheader(f"Impacto de '{vulnerability_vars.get(selected_v_var, selected_v_var)}' na '{impact_vars.get(selected_impact_var, selected_impact_var)}'")

            # Lógica de cruzamento (robusta)
            if selected_impact_var in df_sentiment.columns:  # Se a variável de impacto é de sentimento
                if selected_v_var in df.columns and 'ID' in df.columns and 'ID' in df_sentiment_filtered_by_main.columns:
                    df_vulnerability_analysis = df_sentiment_filtered_by_main[[selected_impact_var, 'ID']].merge(
                        df[[selected_v_var, 'ID']], on='ID', how='inner'
                    ).dropna()
                else:
                    st.warning("Não foi possível cruzar a variável de sentimento com a demográfica. IDs ausentes ou variáveis não encontradas.")
                    df_vulnerability_analysis = pd.DataFrame()
            elif selected_impact_var in df.columns:
                df_vulnerability_analysis = df[[selected_v_var, selected_impact_var]].dropna()
            else:
                st.warning("Variável de impacto não encontrada em nenhum dos DataFrames carregados.")
                df_vulnerability_analysis = pd.DataFrame()
            
            if not df_vulnerability_analysis.empty:
                crosstab_v = pd.crosstab(df_vulnerability_analysis[selected_v_var], df_vulnerability_analysis[selected_impact_var], normalize='index').mul(100).round(2)
                st.dataframe(crosstab_v, use_container_width=True)

                fig_v = px.bar(
                    crosstab_v.reset_index().melt(id_vars=selected_v_var, var_name='Impacto', value_name='Porcentagem (%)'),
                    x=selected_v_var,
                    y='Porcentagem (%)',
                    color='Impacto',
                    barmode='group',
                    title=f'Porcentagem de Respostas para "{impact_vars.get(selected_impact_var, selected_impact_var)}" por "{vulnerability_vars.get(selected_v_var, selected_v_var)}"',
                    text_auto=True
                )
                fig_v.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_v, use_container_width=True)

                # --- Insights automáticos simples
                st.markdown("#### Insights de Vulnerabilidade (Exemplo):")
                if selected_v_var == 'ID7' and selected_impact_var == 'PCT5.1_Sentimento_Geral':
                    if 'Muito Negativo' in crosstab_v.columns:
                        st.markdown(f"**Dados Concretos:** A análise mostra que entre os grupos raciais, **{crosstab_v['Muito Negativo'].idxmax()}** teve a maior porcentagem de sentimento 'Muito Negativo' sobre perdas e modos de vida, com **{crosstab_v['Muito Negativo'].max():.1f}%** dos respondentes desse grupo expressando esse sentimento. Em contraste, **{crosstab_v['Muito Negativo'].idxmin()}** teve a menor porcentagem, com **{crosstab_v['Muito Negativo'].min():.1f}%**.")

                if selected_v_var == 'ID10' and selected_impact_var == 'DF1':
                    if 'Sim' in crosstab_v.columns:
                        pcd_sim_divida = crosstab_v.loc['Sim', 'Sim'] if 'Sim' in crosstab_v.index and 'Sim' in crosstab_v.columns else 0
                        nao_pcd_sim_divida = crosstab_v.loc['Não', 'Sim'] if 'Não' in crosstab_v.index and 'Sim' in crosstab_v.columns else 0
                        st.markdown(f"**Dados Concretos:** Entre os respondentes, **{pcd_sim_divida:.1f}%** das pessoas com deficiência reportaram ter contraído ou aumentado dívidas, enquanto para pessoas sem deficiência, essa porcentagem foi de **{nao_pcd_sim_divida:.1f}%**. Isso sugere uma potencial vulnerabilidade maior para pessoas com deficiência em relação ao endividamento.")

                # --- IA: Resumo Automático
                st.markdown("---")
                st.subheader("🤖 Análise Automática da IA (experimental)")
                mostrar_ia = st.toggle("Mostrar análise automática da IA para vulnerabilidade", value=False, key="toggle_ia_vuln")
                if mostrar_ia:
                    st.markdown("A IA pode gerar um resumo automático ou responder perguntas sobre a análise de vulnerabilidade.")
                    if "historico_ia_vuln" not in st.session_state:
                        st.session_state.historico_ia_vuln = []
                    if st.button("Gerar Resumo Automático da IA", key="botao_resumo_ia_vuln"):
                        with st.spinner("A IA está analisando os dados..."):
                            resumo = f"""
**Resumo IA - Vulnerabilidade:**
- **Grupo analisado:** {vulnerability_vars.get(selected_v_var, selected_v_var)}
- **Variável de impacto:** {impact_vars.get(selected_impact_var, selected_impact_var)}
- **Principais distribuições:** {crosstab_v.to_dict()}
"""
                            st.session_state.historico_ia_vuln.append({"pergunta": "Resumo Automático", "resposta": resumo})
                            st.markdown(resumo)
                    pergunta_livre = st.text_input("Pergunte algo à IA sobre vulnerabilidade:", key="pergunta_livre_vuln")
                    if st.button("Perguntar à IA", key="perguntar_ia_vuln"):
                        try:
                            import openai
                            client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
                            sample = df_vulnerability_analysis.sample(min(40, len(df_vulnerability_analysis))).to_dict(orient="records")
                            user_question = f"Considere esta amostra da análise de vulnerabilidade: {sample}\nPergunta: {pergunta_livre}"
                            completion = client.chat.completions.create(
                                model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_question}], temperature=0
                            )
                            ia_resp = completion.choices[0].message.content
                        except Exception as e:
                            ia_resp = f"Não foi possível usar IA externa (API): {e}"
                        st.session_state.historico_ia_vuln.append({"pergunta": pergunta_livre, "resposta": ia_resp})
                        st.markdown("**Resposta da IA:**")
                        st.write(ia_resp)
                    if st.session_state.historico_ia_vuln:
                        with st.expander("Ver histórico de perguntas à IA (vulnerabilidade)"):
                            for h in st.session_state.historico_ia_vuln[::-1]:
                                st.markdown(f"**Pergunta:** {h['pergunta']}")
                                st.markdown(h["resposta"])
                                st.markdown("---")
            else:
                st.warning("Não há dados válidos para esta combinação de variáveis com os filtros atuais.")
        else:
            st.info("Por favor, selecione as variáveis para a análise de vulnerabilidade.")

    st.markdown("---")
