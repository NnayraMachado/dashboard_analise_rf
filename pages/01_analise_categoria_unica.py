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
filtered_question_groups = st.session_state['filtered_question_groups']

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

        # Detalhamento por Território, Gênero e Raça/Cor
        if selected_column and not is_numeric_column: 
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

else:
    st.warning("Nenhum grupo de colunas categóricas foi identificado para análise. Verifique seus dados.")
