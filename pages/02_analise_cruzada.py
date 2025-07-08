import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()

    
df = st.session_state['df']
df_sentiment_filtered_by_main = st.session_state['df_sentiment_filtered_by_main']
question_labels = st.session_state['question_labels']
all_selectable_categorical_cols = st.session_state['all_selectable_categorical_cols']

st.header("Análise Cruzada de Questões")
st.write("Selecione duas questões para ver a relação entre elas.")

if len(all_selectable_categorical_cols) >= 2:
    options_for_cross_selectbox = [("Selecione uma questão", None)] + [
        (question_labels.get(col, col), col) for col in all_selectable_categorical_cols
    ]
    selected_option_col1 = st.selectbox(
        "Selecione a Questão Principal (Linhas):",
        options_for_cross_selectbox,
        format_func=lambda x: x[0],
        key="cross_col1"
    )
    col1_cross = selected_option_col1[1]

    options_for_col2_cross = [("Selecione uma questão", None)] + [
        (question_labels.get(col, col), col) for col in all_selectable_categorical_cols if col != col1_cross
    ]
    selected_option_col2 = st.selectbox(
        "Selecione a Questão para Cruzar (Colunas):",
        options_for_col2_cross,
        format_func=lambda x: x[0],
        key="cross_col2"
    )
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
                temp_df_cross = df[[col1_cross, 'ID']].merge(
                    df_sentiment_filtered_by_main[[col2_cross, 'ID']], on='ID', how='inner'
                )
            elif col1_cross in df_sentiment_filtered_by_main.columns and col2_cross in df.columns:
                temp_df_cross = df_sentiment_filtered_by_main[[col1_cross, 'ID']].merge(
                    df[[col2_cross, 'ID']], on='ID', how='inner'
                )

        if temp_df_cross is not None:
            df_cross = temp_df_cross.dropna()
        else:
            st.warning(
                f"Não foi possível encontrar ou combinar as colunas '{question_labels.get(col1_cross, col1_cross)}' e '{question_labels.get(col2_cross, col2_cross)}' para cruzamento. Verifique se estão nos DataFrames corretos e se há uma coluna 'ID' para união."
            )
            df_cross = pd.DataFrame()

        if df_cross.empty:
            st.warning(
                f"Não há dados para cruzar as questões '{question_labels.get(col1_cross, col1_cross)}' e '{question_labels.get(col2_cross, col2_cross)}' após remover valores em branco."
            )
        else:
            st.subheader(
                f"Cruzamento de '{question_labels.get(col1_cross, col1_cross)}' por '{question_labels.get(col2_cross, col2_cross)}'"
            )

            col_cross_display, col_cross_chart = st.columns(2)
            with col_cross_display:
                cross_display_mode = st.radio(
                    "Exibir como:",
                    (
                        "Contagem (Número de Entrevistados)",
                        "Porcentagem por Linha",
                        "Porcentagem por Coluna",
                        "Porcentagem Total"
                    ),
                    index=0,
                    key="cross_display_mode"
                )
            with col_cross_chart:
                chart_type_cross = st.radio(
                    "Tipo de Gráfico Cruzado:",
                    ("Barras Empilhadas", "Barras Agrupadas"),
                    index=0,
                    key="chart_type_cross"
                )

            if cross_display_mode == "Contagem (Número de Entrevistados)":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross])
            elif cross_display_mode == "Porcentagem por Linha":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='index').mul(100).round(2)
            elif cross_display_mode == "Porcentagem por Coluna":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='columns').mul(100).round(2)
            elif cross_display_mode == "Porcentagem Total":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='all').mul(100).round(2)

            st.dataframe(crosstab_table, use_container_width=True)

            csv_data_cross = crosstab_table.to_csv().encode('utf-8')
            st.download_button(
                label="Baixar Tabela como CSV",
                data=csv_data_cross,
                file_name=f"{col1_cross}_x_{col2_cross}_cruzamento.csv",
                mime="text/csv",
                key=f"download_csv_cross_{col1_cross}_{col2_cross}"
            )
            excel_buffer_cross = io.BytesIO()
            crosstab_table.to_excel(excel_buffer_cross, engine='xlsxwriter')
            excel_buffer_cross.seek(0)
            st.download_button(
                label="Baixar Tabela como Excel",
                data=excel_buffer_cross.getvalue(),
                file_name=f"{col1_cross}_x_{col2_cross}_cruzamento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_cross_{col1_cross}_{col2_cross}"
            )
            st.markdown("---")
            st.info("Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

            st.subheader("Visualização Cruzada")
            plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Contagem')

            if chart_type_cross == "Barras Empilhadas":
                fig_cross = px.bar(
                    plot_df,
                    x=col1_cross,
                    y='Contagem',
                    color=col2_cross,
                    title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} (Empilhado)',
                    text_auto=True
                )
                fig_cross.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_cross, use_container_width=True)
            elif chart_type_cross == "Barras Agrupadas":
                fig_cross = px.bar(
                    plot_df,
                    x=col1_cross,
                    y='Contagem',
                    color=col2_cross,
                    barmode='group',
                    title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} (Agrupado)',
                    text_auto=True
                )
                fig_cross.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_cross, use_container_width=True)
    else:
        st.info("Por favor, selecione duas questões para realizar a análise cruzada.")
else:
    st.warning("Não há colunas categóricas suficientes para realizar a análise cruzada (mínimo de 2).")
