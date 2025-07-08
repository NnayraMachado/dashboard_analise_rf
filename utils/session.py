# utils/session.py
import pandas as pd
import os
import json
from datetime import datetime
import streamlit as st

def ensure_session_data():
    # Caminhos dos arquivos
    file_main = os.path.join("data", "questionario.csv")
    file_sent = os.path.join("data", "questionario_analisado.csv")
    file_geo = os.path.join("data", "geojs-uf.json")

    # Carrega DataFrame principal
    if 'df_original_main' not in st.session_state:
        if not os.path.exists(file_main):
            st.session_state['df_original_main'] = pd.DataFrame()
            st.session_state['main_data_loaded'] = False
        else:
            df = pd.read_csv(file_main, sep=';', encoding='utf-8')
            df.columns = df.columns.str.strip()
            if 'ID3' in df.columns:
                df['ID3_datetime'] = pd.to_datetime(df['ID3'], errors='coerce', dayfirst=True)
                today = datetime.now()
                df['Idade'] = (today.year - df['ID3_datetime'].dt.year) - (
                    (today.month < df['ID3_datetime'].dt.month) |
                    ((today.month == df['ID3_datetime'].dt.month) & (today.day < df['ID3_datetime'].dt.day))
                )
                df.loc[df['Idade'] < 0, 'Idade'] = pd.NA
                df.loc[df['Idade'] > 120, 'Idade'] = pd.NA
            st.session_state['df_original_main'] = df
            st.session_state['main_data_loaded'] = True

    # Carrega Sentimentos
    if 'df_original_sentiment' not in st.session_state:
        if os.path.exists(file_sent):
            df2 = pd.read_csv(file_sent, sep=';', encoding='utf-8')
            df2.columns = df2.columns.str.strip()
            st.session_state['df_original_sentiment'] = df2
        else:
            st.session_state['df_original_sentiment'] = pd.DataFrame()

    # Carrega GeoJSON
    if 'geojson_data' not in st.session_state:
        if os.path.exists(file_geo):
            with open(file_geo, 'r', encoding='utf-8') as f:
                st.session_state['geojson_data'] = json.load(f)
        else:
            st.session_state['geojson_data'] = {}

    # Sempre deixa pronto!
    st.session_state['df'] = st.session_state['df_original_main'].copy()
    st.session_state['df_sentiment_filtered_by_main'] = st.session_state['df_original_sentiment'].copy()

    # -------------------- DICIONÁRIOS PRINCIPAIS --------------------
    question_labels = {
        # ... cole aqui seu dicionário completo ...
        # Exemplo:
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

    # -------------------- FILTROS E LISTAS AUTOMÁTICAS --------------------
    df_main = st.session_state['df_original_main']
    df_sent = st.session_state['df_original_sentiment']

    available_cols_in_df_main = df_main.columns.tolist() 
    available_cols_in_df_sentiment = df_sent.columns.tolist()

    filtered_question_groups = {}
    for group_name, cols in question_groups.items():
        if group_name == "Sentimentos e Percepções":
            filtered_cols = [col for col in cols if col in available_cols_in_df_sentiment]
        else:
            filtered_cols = [col for col in cols if col in available_cols_in_df_main]
        if filtered_cols:
            filtered_question_groups[group_name] = filtered_cols

    all_selectable_categorical_cols = sorted(list(set(
        [col for cols_list in filtered_question_groups.values() if cols_list for col in cols_list]
    )))

    # -------------------- SALVA NA SESSÃO --------------------
    st.session_state['question_labels'] = question_labels
    st.session_state['filtered_question_groups'] = filtered_question_groups
    st.session_state['all_selectable_categorical_cols'] = all_selectable_categorical_cols
