import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

def carregar_dados():
    if 'dados_carregados' in st.session_state:
        return

    # Caminhos dos arquivos
    FILE_PATH_MAIN_DATA = os.path.join("data", "questionario.csv")
    FILE_PATH_SENTIMENT_DATA = os.path.join("data", "questionario_analisado.csv")
    FILE_PATH_GEOJSON = os.path.join("data", "geojs-uf.json")

    # Dados principais
    try:
        df_main = pd.read_csv(FILE_PATH_MAIN_DATA, sep=';', encoding='utf-8')
        df_main.columns = df_main.columns.str.strip()
        if 'ID3' in df_main.columns:
            df_main['ID3_datetime'] = pd.to_datetime(df_main['ID3'], errors='coerce', dayfirst=True)
            today = datetime(2025, 7, 3)
            df_main['Idade'] = (today.year - df_main['ID3_datetime'].dt.year) - (
                (today.month < df_main['ID3_datetime'].dt.month) | 
                ((today.month == df_main['ID3_datetime'].dt.month) & 
                 (today.day < df_main['ID3_datetime'].dt.day)))
            df_main.loc[df_main['Idade'] < 0, 'Idade'] = pd.NA
            df_main.loc[df_main['Idade'] > 120, 'Idade'] = pd.NA
        st.session_state['df_original_main'] = df_main.copy()
    except Exception as e:
        st.error(f"Erro ao carregar dados principais: {e}")
        st.stop()

    # Dados de sentimento
    try:
        if os.path.exists(FILE_PATH_SENTIMENT_DATA):
            df_sent = pd.read_csv(FILE_PATH_SENTIMENT_DATA, sep=';', encoding='utf-8')
            df_sent.columns = df_sent.columns.str.strip()
            st.session_state['df_original_sentiment'] = df_sent.copy()
        else:
            st.session_state['df_original_sentiment'] = pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados de sentimento: {e}")
        st.session_state['df_original_sentiment'] = pd.DataFrame()

    # GeoJSON
    try:
        with open(FILE_PATH_GEOJSON, 'r', encoding='utf-8') as f:
            st.session_state['geojson_data'] = json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        st.stop()
    
    st.session_state['dados_carregados'] = True
