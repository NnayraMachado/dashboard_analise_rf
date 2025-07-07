import pandas as pd
import os
import numpy as np
import unicodedata
import re

# --- Configurações de Caminho ---
CURRENT_DIR = os.path.dirname(__file__)
DATA_FOLDER = os.path.join(CURRENT_DIR, "data")
INPUT_CSV_PATH = os.path.join(DATA_FOLDER, "questionario.csv") # <-- LENDO O CSV PRINCIPAL AGORA
OUTPUT_CSV_PATH = os.path.join(DATA_FOLDER, "questionario_analisado.csv")

# --- Colunas de Texto ESPECÍFICAS para Análise de Sentimento ---
# ESTES NOMES DEVEM SER EXATAMENTE COMO APARECEM NO SEU questionario.csv ORIGINAL (curtos e limpos)
# Ex: Se a coluna se chama "PCT5.1" no seu CSV, use "PCT5.1" aqui.
# Se ainda tem caracteres estranhos no nome da coluna (ex: "mudanÃ§as"), VOCÊ PRECISA RENOMEAR NO CSV ANTES.
COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES = [
    'PCT5.1', # Quais seriam as perdas ou mudanças nos seus modos de vida e tradições?
    'PC1.1.8.1', # Qual(is) outra(s) medida(s) reparatória(s) você e o seu núcleo familiar acham que poderia(m) ser implementada(s) para Monitoramento de Segurança em Barragem e acesso à informação (Garantia da não repetição):
    'ADAI_PC2' # Como você avalia a participação das pessoas atingidas na elaboração dos projetos comunitários?
]

# --- Função de Normalização de Texto ---
def normalize_text(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', '', text).lower()
    return text.strip()

# --- Função de Análise de Sentimento SIMULADA (REFINADA) ---
def analyze_sentiment_refined_simulated(original_text, base_column_name=""):
    if pd.isna(original_text) or not isinstance(original_text, str) or original_text.strip() == "":
        return {
            "Geral": None,
            "Satisfacao": None,
            "Emocao": None,
            "Justificativa": None
        }

    normalized_text = normalize_text(original_text)
    
    # --- Simulação para Sentimento Geral (5 Categorias) ---
    general_sentiment_options = ["Muito Negativo", "Negativo", "Neutro", "Positivo", "Muito Positivo"]
    if "problema" in normalized_text or "ruim" in normalized_text or "dificil" in normalized_text or "perda" in normalized_text or "sem" in normalized_text or "nao" in normalized_text:
        if "muito" in normalized_text or "total" in normalized_text or "nunca" in normalized_text or "pessimo" in normalized_text:
            general_sentiment = "Muito Negativo"
        else:
            general_sentiment = "Negativo"
    elif "ajuda" in normalized_text or "bom" in normalized_text or "melhorou" in normalized_text or "consegui" in normalized_text or "positivo" in normalized_text or "certo" in normalized_text:
        if "muito" in normalized_text or "totalmente" in normalized_text or "otimo" in normalized_text or "excelente" in normalized_text:
            general_sentiment = "Muito Positivo"
        else:
            general_sentiment = "Positivo"
    else:
        general_sentiment = np.random.choice(general_sentiment_options, p=[0.1, 0.2, 0.4, 0.2, 0.1])

    # --- Simulação para Avaliação/Satisfação (5 Categorias) ---
    satisfaction_options = ["Muito Insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito Satisfeito"]
    if "nao funciona" in normalized_text or "pessima" in normalized_text or "zero" in normalized_text or "nunca funciona" in normalized_text or "descontente" in normalized_text:
        satisfaction = "Muito Insatisfeito"
    elif "nao" in normalized_text or "pouco" in normalized_text or "ruim" in normalized_text or "insatisfeito" in normalized_text:
        satisfaction = "Insatisfeito"
    elif "funciona" in normalized_text or "razoavel" in normalized_text or "ok" in normalized_text:
        satisfaction = "Satisfeito"
    elif "muito bom" in normalized_text or "otima" in normalized_text or "excelente" in normalized_text or "satisfeito" in normalized_text:
        satisfaction = "Muito Satisfeito"
    else:
        satisfaction = np.random.choice(satisfaction_options, p=[0.1, 0.3, 0.3, 0.2, 0.1])

    # --- Simulação para Natureza da Emoção/Conteúdo ---
    emotion_nature_options = [
        "Perda/Dificuldade", "Frustração/Crítica", "Descrença/Revolta", 
        "Esperança/Melhora", "Sugestão Construtiva", "Resiliência/Adaptação", "Neutro/Factual"
    ]
    if "perda" in normalized_text or "dificuldade" in normalized_text or "sofrimento" in normalized_text or "prejuizo" in normalized_text:
        emotion_nature = "Perda/Dificuldade"
    elif "critica" in normalized_text or "culpa" in normalized_text or "nao resolvem" in normalized_text or "absurdo" in normalized_text:
        emotion_nature = "Frustração/Crítica"
    elif "nunca" in normalized_text or "enganado" in normalized_text or "mentira" in normalized_text or "nao confio" in normalized_text:
        emotion_nature = "Descrença/Revolta"
    elif "melhorar" in normalized_text or "proposta" in normalized_text or "solucao" in normalized_text or "alternativa" in normalized_text:
        emotion_nature = "Sugestão Construtiva"
    elif "esperanca" in normalized_text or "superar" in normalized_text:
        emotion_nature = "Esperança/Melhora"
    elif "reconstruir" in normalized_text or "adaptacao" in normalized_text:
        emotion_nature = "Resiliência/Adaptação"
    else:
        emotion_nature = np.random.choice(emotion_nature_options, p=[0.2, 0.15, 0.1, 0.15, 0.15, 0.1, 0.15])
    
    # --- Trecho Chave/Citação (Justificativa) ---
    words = original_text.split()
    if len(words) > 15:
        justification = " ".join(words[:15]) + "..."
    else:
        justification = original_text
    
    justification = f"[Simulado] {justification}"

    return {
        "Geral": general_sentiment,
        "Satisfacao": satisfaction,
        "Emocao": emotion_nature,
        "Justificativa": justification
    }

# --- Carregar o DataFrame ---
print(f"--- Iniciando processamento de sentimentos ---")
print(f"Verificando caminho de entrada: {INPUT_CSV_PATH}")

if not os.path.exists(INPUT_CSV_PATH):
    print(f"ERRO CRÍTICO: O arquivo de entrada '{INPUT_CSV_PATH}' NÃO FOI ENCONTRADO.")
    print("Por favor, certifique-se de que o arquivo 'questionario.csv' está na pasta 'data/'")
    print("E que você está executando este script a partir do diretório raiz do seu projeto.")
    exit()

try:
    # Tenta ler com sep=';' e encoding='utf-8'
    df_main = pd.read_csv(INPUT_CSV_PATH, sep=';', encoding='utf-8')
    df_main.columns = df_main.columns.str.strip() # Limpa espaços em nomes de colunas
    print(f"DataFrame principal carregado com sucesso. Total de {len(df_main)} linhas.")
    
    print("\nNomes das colunas ORIGINAIS no DataFrame principal:")
    for col in df_main.columns:
        print(f"- '{col}'")
    
    # --- Cria um DataFrame SÓ COM OS IDs e as colunas de texto para análise ---
    # Isso garante que o DF de sentimentos seja menor e contenha apenas o necessário
    # Assumimos que 'ID' (ou 'ID1') é a coluna de ID única para merge posterior no dashboard
    
    # Primeiro, identifique a coluna de ID. Se não for 'ID', ajuste aqui
    id_column_name = 'ID' 
    if 'ID1' in df_main.columns: # Se ID1 for o nome da coluna de identificação
        id_column_name = 'ID1'
    elif 'ID' not in df_main.columns: # Se não tem ID nem ID1, o merge será problemático
        print("AVISO: Coluna 'ID' ou 'ID1' não encontrada no DataFrame principal. O merge pode falhar no dashboard.")
        # Pode ser necessário criar um ID temporário se não houver um
        df_main['ID_Temp'] = df_main.index 
        id_column_name = 'ID_Temp'

    cols_for_sentiment_df = [id_column_name] + COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES
    
    # Seleciona apenas as colunas necessárias para o DataFrame de sentimentos
    # e garante que elas existam no df_main
    cols_for_sentiment_df = [col for col in cols_for_sentiment_df if col in df_main.columns]

    if id_column_name not in cols_for_sentiment_df:
        print(f"ERRO: Coluna de ID '{id_column_name}' não encontrada no DataFrame principal para criar o DF de sentimentos. A análise pode falhar.")
        exit()

    df_sentiment_processed = df_main[cols_for_sentiment_df].copy()

    # Imprime os primeiros valores de uma coluna de texto para verificar caracteres especiais
    if COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES and COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES[0] in df_sentiment_processed.columns:
        print(f"\nPrimeiros 5 valores da coluna '{COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES[0]}' (original) no DF de sentimento:")
        print(df_sentiment_processed[COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES[0]].head().tolist())

except Exception as e:
    print(f"ERRO CRÍTICO ao carregar o arquivo CSV: {e}")
    print("Possíveis causas: separador errado (tente sep=','), codificação errada (tente encoding='latin1' ou 'ISO-8859-1'), arquivo corrompido.")
    exit()

# --- Aplicar análise de sentimento SOMENTE nas colunas especificadas (nomes curtos) ---
print("\nIniciando análise de sentimento e criação de novas colunas...")

if not COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES:
    print("\nAVISO: Nenhuma coluna para análise de sentimento foi especificada ou encontrada com os nomes limpos. O CSV de saída será o mesmo que o principal.")
    df_main.to_csv(OUTPUT_CSV_PATH, sep=';', encoding='utf-8', index=False)
    print(f"Arquivo salvo (sem novas colunas de sentimento) em: {OUTPUT_CSV_PATH}")
    exit()

for col_name in COLUMNS_FOR_SENTIMENT_ANALYSIS_CLEAN_NAMES:
    if col_name not in df_sentiment_processed.columns:
        print(f"AVISO: Coluna '{col_name}' especificada para análise não encontrada no DataFrame de sentimentos. Pulando.")
        continue

    print(f"Processando coluna: {col_name}")
    
    new_general_col = f"{col_name}_Sentimento_Geral"
    new_satisfaction_col = f"{col_name}_Sentimento_Satisfacao"
    new_emotion_col = f"{col_name}_Sentimento_Emocao"
    new_justification_col = f"{col_name}_Sentimento_Justificativa"

    general_sentiments = []
    satisfaction_sentiments = []
    emotion_sentiments = []
    justifications = []

    for text in df_sentiment_processed[col_name]:
        result = analyze_sentiment_refined_simulated(text, base_column_name=col_name)
        general_sentiments.append(result["Geral"])
        satisfaction_sentiments.append(result["Satisfacao"])
        emotion_sentiments.append(result["Emocao"])
        justifications.append(result["Justificativa"])
    
    df_sentiment_processed[new_general_col] = general_sentiments
    df_sentiment_processed[new_satisfaction_col] = satisfaction_sentiments
    df_sentiment_processed[new_emotion_col] = emotion_sentiments
    df_sentiment_processed[new_justification_col] = justifications
    print(f"Colunas de sentimento criadas para '{col_name}'.")

print("\nAnálise de sentimento concluída para as colunas especificadas.")

# --- Salvar o DataFrame processado (APENAS COM AS COLUNAS DE ID E SENTIMENTOS) ---
print(f"\nTentando salvar o DataFrame de sentimentos processado em: {OUTPUT_CSV_PATH}")
try:
    # Salvamos APENAS as colunas de ID e as novas colunas de sentimento
    cols_to_save = [id_column_name] + [col for col in df_sentiment_processed.columns if col.endswith(('_Geral', '_Satisfacao', '_Emocao', '_Justificativa'))]
    df_sentiment_processed[cols_to_save].to_csv(OUTPUT_CSV_PATH, sep=';', encoding='utf-8', index=False)
    
    print(f"DataFrame de sentimentos processado salvo com sucesso em: {OUTPUT_CSV_PATH}")
    print("\nPRÓXIMO PASSO CRÍTICO: Atualize seu dashboard Streamlit para carregar 'questionario.csv' como principal e 'questionario_analisado.csv' para os sentimentos.")
    print("\n--- Processamento Finalizado ---")
except Exception as e:
    print(f"ERRO CRÍTICO ao salvar o arquivo CSV: {e}")
    print("Verifique permissões de escrita ou espaço em disco.")