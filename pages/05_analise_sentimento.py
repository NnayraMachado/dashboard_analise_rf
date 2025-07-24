import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 

# Para a Word Cloud
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Para limpeza de texto
import re 
import nltk
from nltk.corpus import stopwords 

try:
    nltk.data.find('corpora/stopwords')
except LookupError: 
    nltk.download('stopwords', quiet=True)


import io 
import os 

# --- Função para carregar CSS ---
def load_css_from_root(file_name="styles.css"):
    current_script_dir = os.path.dirname(__file__)
    root_dir = os.path.join(current_script_dir, '..')
    css_file_path = os.path.join(root_dir, file_name)
    try:
        with open(css_file_path, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Certifique-se de que ele está na pasta raiz do seu projeto.")

load_css_from_root() 

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()

df_sentiment_filtered_by_main = st.session_state.get('df_sentiment_filtered_by_main') 
question_labels = st.session_state.get('question_labels') 

# --- Verifica se os DataFrames essenciais estão carregados ---
if df_sentiment_filtered_by_main is None or question_labels is None:
    st.error("Erro: Dados essenciais para análise de sentimento não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop() 

# --- Mapeamentos de Colunas de Sentimento (EXEMPLO - AJUSTE CONFORME SEUS DADOS REAIS) ---
sentiment_text_columns = {
    'PCT5.1_Sentimento_Geral': question_labels.get('PCT5.1_Sentimento_Geral', 'Perdas/Modos de Vida (Geral)'),
    'PCT5.1_Sentimento_Satisfacao': question_labels.get('PCT5.1_Sentimento_Satisfacao', 'Perdas/Modos de Vida (Satisfação)'),
    'PCT5.1_Sentimento_Emocao': question_labels.get('PCT5.1_Sentimento_Emocao', 'Perdas/Modos de Vida (Emoção)'),
    'PCT5.1_Sentimento_Justificativa': question_labels.get('PCT5.1_Sentimento_Justificativa', 'Perdas/Modos de Vida (Trechos Chave)'),
}

# --- PALAVRAS-CHAVE PARA FILTRAR NA NUVEM DE PALAVRAS E TRECHOS CHAVE ---
custom_stopwords_pt = stopwords.words('portuguese') + [
    # Sua lista extensiva de stopwords customizadas
    'simulado', 'simulados', 'null', 'nao', 'não', 'informado', 'informada', 'nao informado', 'não informado',
    'n/a', 'na', 'para', 'com', 'um', 'uma', 'e', 'o', 'a', 'de', 'do', 'da', 'que', 'em', 'se', 'mas', 'ou',
    'mais', 'como', 'ao', 'aos', 'as', 'às', 'no', 'nos', 'nas', 'pelo', 'pelos', 'pela', 'pelas', 'pra', 'pro',
    'mas', 'só', 'já', 'ainda', 'sem', 'ser', 'foi', 'foram', 'ter', 'tinha', 'tinham', 'ir', 'ia', 'vão', 'vem',
    'muito', 'pouco', 'poucos', 'poucas', 'muitas', 'grande', 'grandes', 'pequeno', 'pequena', 'faz', 'fazer',
    'dizer', 'disse', 'dizem', 'poder', 'pode', 'podem', 'todo', 'toda', 'todos', 'todas', 'quando', 'onde',
    'quem', 'por', 'porém', 'então', 'assim', 'apenas', 'desde', 'sobre', 'sob', 'comigo', 'contigo', 'conosco',
    'convosco', 'dele', 'dela', 'deles', 'delas', 'nele', 'nela', 'neles', 'nelas', 'nesse', 'nessa', 'nesses',
    'nessas', 'aqui', 'ali', 'aí', 'cá', 'lá', 'onde', 'qual', 'quais', 'quanto', 'quantos', 'quantas', 'cujo',
    'cujos', 'cujas', 'este', 'estas', 'isto', 'esse', 'essas', 'isso', 'aquele', 'aquelas', 'aquilo', 'tão',
    'tal', 'tais', 'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'seu', 'sua', 'seus', 'suas',
    'nosso', 'nossa', 'nossos', 'nossas', 'vosso', 'vossa', 'vossos', 'vossas', 'certo', 'certa', 'certos', 'certas',
    'vários', 'várias', 'diversos', 'diversas', 'ambos', 'ambas', 'cada', 'nenhum', 'nenhuma', 'nenhuns', 'nenhumas',
    'cujo', 'cujos', 'cujas', 'outra', 'outras', 'outros', 'primeiro', 'primeira', 'primeiros', 'primeiras',
    'segundo', 'segunda', 'segundos', 'segundas', 'último', 'última', 'últimos', 'últimas', 'até', 'já', 'ainda',
    'agora', 'depois', 'antes', 'logo', 'durante', 'enquanto', 'após', 'apesar', 'conforme', 'mediante', 'perante',
    'sempre', 'nunca', 'jamais', 'talvez', 'provavelmente', 'certamente', 'realmente', 'efetivamente',
    'principalmente', 'especialmente', 'exclusivamente', 'inclusive', 'apenas', 'só', 'também', 'tão', 'quase',
    'muito', 'pouco', 'demais', 'bastante', 'apenas', 'somente', 'até', 'mesmo', 'cerca', 'cerca de', 'menos',
    'mais ou menos', 'já', 'ainda', 'agora', 'depois', 'antes', 'logo', 'durante', 'enquanto', 'após', 'apesar',
    'conforme', 'mediante', 'perante', 'sempre', 'nunca', 'jamais', 'talvez', 'provavelmente', 'certamente',
    'realmente', 'efetivamente', 'principalmente', 'especialmente', 'exclusivamente', 'indubitavelmente',
    'inclusive', 'exclusive', 'literalmente', 'visivelmente', 'claro', 'clara', 'claros', 'claras', 'verdadeiro',
    'verdadeira', 'verdadeiros', 'verdadeiras', 'falso', 'falsa', 'falsos', 'falsas', 'bom', 'boa', 'bons', 'boas',
    'mal', 'mau', 'maus', 'má', 'más', 'melhor', 'melhores', 'pior', 'piores', 'pouco', 'poucos', 'pouca', 'poucas',
    'muito', 'muitos', 'muita', 'muitas', 'grande', 'grandes', 'pequeno', 'pequena', 'pequenos', 'pequenas', 'todo',
    'toda', 'todos', 'todas', 'certo', 'certa', 'certos', 'certas', 'tal', 'tais', 'qual', 'quais', 'cujo', 'cujos',
    'cuja', 'cujas', 'quanto', 'quantos', 'quanta', 'quantas', 'cujo', 'cujos', 'cuja', 'cujas', 'como', 'onde', 'quando',
    'porquê', 'apenas', 'só', 'somente', 'inclusive', 'exclusive', 'pelo menos', 'ao menos', 'nem', 'também', 'ainda',
    'já', 'agora', 'depois', 'antes', 'logo', 'durante', 'enquanto', 'após', 'apesar', 'conforme', 'mediante',
    'perante', 'sempre', 'nunca', 'jamais', 'talvez', 'provavelmente', 'certamente', 'realmente', 'efetivamente',
    'principalmente', 'especialmente', 'exclusivamente', 'indubitavelmente', 'literalmente', 'visivelmente',
    'claro', 'clara', 'claros', 'claras', 'verdadeiro', 'verdadeira', 'verdadeiros', 'verdadeiras', 'falso',
    'falsa', 'falsos', 'falsas', 'bom', 'boa', 'bons', 'boas', 'mal', 'mau', 'maus', 'má', 'más', 'melhor',
    'melhores', 'pior', 'piores', 'pouco', 'poucos', 'pouca', 'poucas', 'muito', 'muitos', 'muita', 'muitas',
    'grande', 'grandes', 'pequeno', 'pequena', 'pequenos', 'pequenas', 'todo', 'toda', 'todos', 'todas', 'certo',
    'certa', 'certos', 'certas', 'tal', 'tais', 'qual', 'quais', 'cujo', 'cujos', 'cuja', 'cujas', 'quanto',
    'quantos', 'quanta', 'quantas', 'cujo', 'cujos', 'cuja', 'cujas', 'como', 'onde', 'quando', 'porquê', 'por que', 'pra que', 'para que',
    'se', 'senão', 'isto', 'isso', 'aquilo', 'aqui', 'ali', 'aí', 'cá', 'lá', 'agora', 'hoje', 'ontem', 'amanhã',
    'sempre', 'nunca', 'jamais', 'logo', 'cedo', 'tarde', 'antes', 'depois', 'então', 'assim', 'melhor',
    'pior', 'mais', 'menos', 'muito', 'pouco', 'bastante', 'demais', 'quase', 'apenas', 'somente', 'só',
    'até', 'mesmo', 'inclusive', 'exclusive', 'também', 'nem', 'já', 'ainda', 'porém', 'contudo', 'todavia',
    'entretanto', 'portanto', 'consequentemente', 'logo', 'assim', 'então', 'pois', 'porque', 'porquanto',
    'visto que', 'já que', 'como', 'conforme', 'segundo', 'consoante', 'como', 'se', 'caso', 'contanto que',
    'desde que', 'embora', 'ainda que', 'mesmo que', 'apesar de', 'posto que', 'por mais que', 'para que',
    'a fim de que', 'que', 'para', 'a', 'o', 'as', 'os', 'um', 'uns', 'uma', 'umas', 'de', 'do', 'da', 'dos',
    'das', 'em', 'no', 'na', 'nos', 'nas', 'por', 'pelo', 'pela', 'pelos', 'pelas', 'com', 'contra', 'entre',
    'sem', 'sob', 'sobre', 'trás'
]

# --- Termos EXCLUSIVOS para FILTRAR nos TRECHOS CHAVE e NUVEM de PALAVRAS ---
# Adicione aqui termos que são considerados "nulos" ou ruído nos dados brutos.
non_informative_text_terms = [
    "[simulado] nulo", "nulo", "null", "não informado", "não se aplica", 
    "outros", "sem resposta", "indefinido", "não identificável", "",
    "zero", "[simulado] zero", "0" # Garante que string vazia seja filtrada
]


# --- Função para limpar texto ---
def clean_text_for_wordcloud(text, stopwords_list, non_informative_terms):
    text = str(text).lower() 
    
    # Primeiro, remover termos não informativos INTEIROS se presentes no início da string
    for term in non_informative_terms:
        if text.strip() == term.lower(): # Se o texto for EXATAMENTE um termo não informativo (após strip)
            return "" # Retorna string vazia para ser descartada
    
    # Continua com a limpeza normal para textos que não são *exatamente* termos não informativos
    text = re.sub(r'https?://\S+|www\.\S+', '', text) 
    text = re.sub(r'<.*?>', '', text) 
    text = re.sub(r'[^\w\s]', '', text) # Mantém apenas letras, números e espaços
    
    words = text.split()
    # Filtra stopwords e palavras de um único caractere
    filtered_words = [word for word in words if word not in stopwords_list and len(word) > 1]
    
    # Filtra palavras que, após a tokenização, se pareçam com termos não informativos
    # Ex: se "nulo" for uma palavra dentro de uma frase.
    filtered_words = [word for word in filtered_words if word not in [t.lower() for t in non_informative_terms if len(t) > 1]]
    
    return ' '.join(filtered_words)


# --- Título e Descrição da Página ---
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Análise de Sentimento por Tema</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Explore os sentimentos e emoções expressos nas respostas de texto livre, obtidas através de análises de Processamento de Linguagem Natural (PLN). <br>
Os dados são baseados em uma **amostra** de respondentes. As análises aqui são **descritivas**, focando em padrões e associações **observadas nesta amostra**, e não devem ser generalizadas para toda a população sem inferência estatística apropriada.
</p>
""", unsafe_allow_html=True)

# --- Opção de gráfico e Seletores ---
col_chart_type, col_sentiment_display = st.columns([1, 3])
with col_chart_type:
    chart_type = st.radio("Tipo de gráfico:", ["Pizza", "Barras"], horizontal=False, key="sentiment_chart_type") 
with col_sentiment_display:
    selected_sentiment_display_type = st.radio(
        "Visualizar análise de sentimento por:", 
        ["Sentimento Geral", "Satisfação", "Emoção", "Trechos Chave"],
        key="sentiment_display_type",
        horizontal=True 
    )

current_df_sentiment = df_sentiment_filtered_by_main 

available_sentiment_cols = {k: v for k, v in sentiment_text_columns.items() if k in current_df_sentiment.columns}

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
    st.info(f"Nenhum dado de '{selected_sentiment_display_type}' disponível na amostra para análise. Por favor, verifique seus dados.")
else:
    selected_sentiment_topic_code = st.selectbox(
        f"Selecione o Tópico para analisar {selected_sentiment_display_type}:", 
        list(filtered_sentiment_options_for_selectbox.keys()),
        format_func=lambda x: filtered_sentiment_options_for_selectbox[x],
        key="sentiment_topic_code_selector"
    )

    if selected_sentiment_topic_code:
        # ----- Análise de Sentimento Categórica (Geral, Satisfação, Emoção) -----
        if selected_sentiment_display_type != "Trechos Chave":
            total = current_df_sentiment[selected_sentiment_topic_code].notna().sum()
            sentiment_counts_abs = current_df_sentiment[selected_sentiment_topic_code].value_counts().reset_index()
            sentiment_counts_abs.columns = ['Categoria', 'Quantidade']
            sentiment_counts_abs['Porcentagem (%)'] = (sentiment_counts_abs['Quantidade']/total*100).round(2)
            
            st.markdown("##### Tabela de Distribuição dos Sentimentos na Amostra")
            st.dataframe(sentiment_counts_abs, use_container_width=True)
            st.caption(f"Mostra a contagem de respondentes e a porcentagem de cada categoria de sentimento **na amostra**. As porcentagens são calculadas sobre o total de {total} respostas válidas para este tópico.")

            # --- Botões de Download da Tabela ---
            st.download_button(
                label="📥 Baixar Tabela de Sentimentos (CSV)",
                data=sentiment_counts_abs.to_csv(index=False).encode('utf-8'),
                file_name=f"sentimentos_{selected_sentiment_topic_code}_amostra.csv",
                mime="text/csv"
            )

            # --- Gráfico ---
            st.subheader(f"Visualização da Distribuição de {selected_sentiment_display_type} para '{filtered_sentiment_options_for_selectbox[selected_sentiment_topic_code]}'")
            if chart_type == "Pizza":
                fig_sentiment = px.pie(
                    sentiment_counts_abs,
                    names='Categoria',
                    values='Quantidade',
                    title=f'Distribuição de {filtered_sentiment_options_for_selectbox[selected_sentiment_topic_code]} na Amostra',
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Plotly 
                )
                fig_sentiment.update_traces(textinfo='percent+label', pull=[0.05] * len(sentiment_counts_abs))
                fig_sentiment.update_layout(title_x=0.5)
            else: # Barras
                fig_sentiment = px.bar(
                    sentiment_counts_abs.sort_values("Quantidade", ascending=False),
                    x='Categoria',
                    y='Quantidade',
                    text='Porcentagem (%)', 
                    title=f'Distribuição de {filtered_sentiment_options_for_selectbox[selected_sentiment_topic_code]} na Amostra',
                    color='Categoria', 
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig_sentiment.update_layout(xaxis_title="Categoria de Sentimento", yaxis_title="Quantidade de Respondentes", title_x=0.5)
                fig_sentiment.update_traces(textposition='outside') 
            
            st.plotly_chart(fig_sentiment, use_container_width=True)
            st.info("💡 Dica: Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

        # --- Nuvem de palavras (Word Cloud) e Trechos Chave ---
        st.markdown("---")
        st.markdown("### 🌥️ Análise de Trechos Chave (Nuvem de Palavras)")
        st.write("Visualize as palavras mais frequentes nos trechos de texto livre da amostra, após a remoção de termos comuns e irrelevantes. Palavras maiores são mais frequentes.")
        
        # Detecta a coluna de justificativa associada
        original_col_prefix = selected_sentiment_topic_code.rsplit('_', 2)[0]
        justification_col_name = f"{original_col_prefix}_Sentimento_Justificativa"
        
        if justification_col_name in current_df_sentiment.columns:
            # Filtra textos vazios ou não informativos ANTES de passar para a limpeza/nuvem
            all_raw_texts_filtered = current_df_sentiment[justification_col_name].dropna().apply(str).loc[
                ~current_df_sentiment[justification_col_name].fillna('').apply(str.lower).isin([t.lower() for t in non_informative_text_terms])
            ]
            
            if not all_raw_texts_filtered.empty:
                # --- Processa o texto para a nuvem de palavras ---
                # A função clean_text_for_wordcloud já lida com a remoção de termos específicos
                cleaned_texts = all_raw_texts_filtered.apply(lambda x: clean_text_for_wordcloud(x, custom_stopwords_pt, non_informative_text_terms))
                
                # Concatena todos os textos limpos (após a limpeza, alguns podem se tornar vazios, filtramos aqui)
                final_text_for_wordcloud = ' '.join([text for text in cleaned_texts.tolist() if text.strip()])

                if final_text_for_wordcloud.strip():
                    # --- Configuração da WordCloud ---
                    wordcloud = WordCloud(
                        width=800, 
                        height=400, 
                        background_color='white', 
                        colormap='viridis', 
                        max_words=100, 
                        contour_width=3, 
                        contour_color='steelblue', 
                        collocations=False 
                    ).generate(final_text_for_wordcloud)
                    
                    fig_wc, ax = plt.subplots(figsize=(12, 6)) 
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                    st.caption("A nuvem de palavras destaca os termos mais frequentes nos textos livres da amostra, após a remoção de stopwords e termos irrelevantes. O tamanho da palavra indica sua frequência.")
                else: 
                    st.info("Não há textos significativos após a limpeza para gerar a nuvem de palavras para esta seleção.")
            else:
                st.info("Não há trechos de texto livre disponíveis para gerar a nuvem de palavras para esta seleção (ou são apenas não informativos).")
        else:
            st.info("Não há coluna de trechos chave ('_Sentimento_Justificativa') associada a esta seleção de tópico.")

        # --- Exemplos de Trechos Chave + download ---
        st.markdown("#### Exemplos de Trechos Chave (Textos Originais)")
        st.write("Estes são trechos diretos das respostas dos respondentes na amostra. Eles fornecem contexto qualitativo para as análises de sentimento e a nuvem de palavras.")
        
        if justification_col_name in current_df_sentiment.columns:
            # Filtra para display também
            all_raw_texts_for_display = current_df_sentiment[justification_col_name].dropna().apply(str).loc[
                ~current_df_sentiment[justification_col_name].fillna('').apply(str.lower).isin([t.lower() for t in non_informative_text_terms])
            ].tolist() 

            if all_raw_texts_for_display:
                # Usar um div para melhor espaçamento e visual
                st.markdown("<div style='background-color:#f5f5f5; border-radius:8px; padding:15px; margin-top:10px;'>", unsafe_allow_html=True)
                for i, sample_text in enumerate(all_raw_texts_for_display[:min(5, len(all_raw_texts_for_display))]): 
                    st.markdown(f"<p style='margin-bottom:5px; padding-bottom:5px; border-bottom:1px solid #eee;'>\"<span style='font-style:italic;'>{sample_text}</span>\"</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                if len(all_raw_texts_for_display) > 5:
                    st.info(f"Mostrando os primeiros 5 de {len(all_raw_texts_for_display)} trechos. Baixe o arquivo completo para ver todos.")

                st.download_button(
                    label="📥 Baixar todos os trechos chave (TXT)",
                    data="\n".join(all_raw_texts_for_display).encode('utf-8'), 
                    file_name=f"trechos_chave_{selected_sentiment_topic_code}_amostra.txt", 
                    mime="text/plain",
                    help="Baixa todos os trechos de texto livre da amostra para este tópico."
                )
            else:
                st.info("Não há trechos de texto livre válidos para download para esta seleção (apenas não informativos).")
        else:
            st.info("Não há coluna de trechos chave ('_Sentimento_Justificativa') associada a esta seleção de tópico.")

    else: # Este else pertence ao if selected_sentiment_topic_code: (mais externo)
        st.info("Por favor, selecione um tópico para visualizar a análise de sentimento.")
