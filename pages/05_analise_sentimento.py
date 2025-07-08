import streamlit as st
import pandas as pd
import plotly.express as px

# Para a Word Cloud
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()

df_sentiment_filtered_by_main = st.session_state['df_sentiment_filtered_by_main']

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



            # --- Nuvem de palavras (Word Cloud)
            # Detecta a coluna de justificativa associada, mesmo para outras categorias!
            original_col_prefix = selected_sentiment_topic_code.rsplit('_', 2)[0]
            justification_col_name = f"{original_col_prefix}_Sentimento_Justificativa"
            st.markdown("---")
            st.markdown("### 🌥️ Visualize a nuvem de palavras dos trechos chave")
            mostrar_nuvem = st.checkbox(
                "Mostrar nuvem de palavras dos trechos chave",
                key=f"mostrar_nuvem_{selected_sentiment_topic_code}"
            )
            if mostrar_nuvem:
                if justification_col_name in current_df_sentiment.columns:
                    textos = current_df_sentiment[justification_col_name].dropna().astype(str).str.cat(sep=' ')
                    if textos.strip():
                        wordcloud = WordCloud(width=800, height=300, background_color='white', colormap='tab10').generate(textos)
                        fig_wc, ax = plt.subplots(figsize=(10,3))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig_wc)
                    else:
                        st.info("Não há textos suficientes para gerar a nuvem de palavras.")
                else:
                    st.info("Não há coluna de trechos chave para esta seleção.")

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

            st.markdown("---")
