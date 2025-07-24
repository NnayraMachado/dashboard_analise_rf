import streamlit as st
import pandas as pd
import plotly.express as px
import io
import plotly.graph_objects as go 
import os # <-- Adicione esta importação!

# Importar o CSS customizado (assumindo que 'styles.css' está na raiz do projeto)
# E a função ensure_session_data
from utils.session import ensure_session_data # Importar sua função existente

# Obtém o diretório do script atual (analise_categoria_unica.py)
current_script_dir = os.path.dirname(__file__)

# Constrói o caminho para o diretório raiz (onde app.py e styles.css estão)
root_dir = os.path.join(current_script_dir, '..')

# ----- CSS CUSTOMIZADO PARA MELHORAR O VISUAL (Lido de arquivo externo) -----
css_file_path = os.path.join(root_dir, "styles.css") # Caminho para o CSS na raiz
try:
    with open(css_file_path, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Certifique-se de que ele está na pasta raiz do seu projeto.")


# Certifica que os dados da sessão estão carregados
ensure_session_data()
    
df = st.session_state.get('df')
df_sentiment_filtered_by_main = st.session_state.get('df_sentiment_filtered_by_main')
question_labels = st.session_state.get('question_labels')
filtered_question_groups = st.session_state.get('filtered_question_groups')

# --- Constante para o número máximo de categorias a exibir por padrão ---
MAX_CATEGORIES_DEFAULT_DISPLAY = 10 # Você pode ajustar este número

# --- Verifica se os DataFrames essenciais estão carregados ---
if df is None or df_sentiment_filtered_by_main is None or question_labels is None or filtered_question_groups is None:
    st.error("Erro: Dados essenciais não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop() 

# --- Funções Auxiliares para Geração de Gráficos ---

def create_bar_chart(df_data, x_col, y_col, title, color_col, orientation='v'):
    if orientation == 'v':
        fig = px.bar(df_data, x=x_col, y=y_col, title=title, color=color_col, text_auto=True,
                     color_discrete_sequence=px.colors.qualitative.Plotly) 
        fig.update_layout(xaxis={'categoryorder':'total descending'}, title_x=0.5,
                          yaxis_title=y_col, xaxis_title=x_col) 
    else: # Horizontal
        fig = px.bar(df_data, y=x_col, x=y_col, title=title, color=color_col, orientation='h', text_auto=True,
                     color_discrete_sequence=px.colors.qualitative.Plotly)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, title_x=0.5,
                          yaxis_title=x_col, xaxis_title=y_col) 
    
    fig.update_traces(textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide') 
    
    return fig

def create_pie_chart(df_data, names_col, values_col, title):
    fig = px.pie(df_data, names=names_col, values=values_col, title=title, hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Plotly)
    fig.update_traces(textinfo='percent+label', pull=[0.05] * len(df_data))
    fig.update_layout(title_x=0.5)
    return fig

def display_cross_tabulation(df_base, col_to_analyze, cross_by_col, title_suffix, question_labels_map):
    st.markdown(f"#### Por {title_suffix}")
    df_cross = df_base[[col_to_analyze, cross_by_col]].dropna()
    
    if not df_cross.empty:
        crosstab = pd.crosstab(df_cross[col_to_analyze], df_cross[cross_by_col])
        st.dataframe(crosstab, use_container_width=True)
        st.caption(f"Tabela de contagem cruzada: Mostra o número de respondentes na amostra que selecionaram cada combinação de '{question_labels_map.get(col_to_analyze, col_to_analyze)}' e '{title_suffix}'.")


        fig = px.bar(
            crosstab.reset_index().melt(id_vars=col_to_analyze, var_name=title_suffix, value_name='Contagem'), 
            x=col_to_analyze, 
            y='Contagem', 
            color=title_suffix, 
            barmode='group', 
            title=f'Contagem de Respostas para "{question_labels_map.get(col_to_analyze, col_to_analyze)}" por {title_suffix} na Amostra', 
            text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Plotly 
        )
        fig.update_layout(xaxis={'categoryorder':'total descending'}, title_x=0.5,
                          yaxis_title='Número de Respondentes', xaxis_title=f'Respostas de {question_labels_map.get(col_to_analyze, col_to_analyze)}')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else: 
        st.info(f"Não há dados na amostra para cruzar com {title_suffix}.")

# --- Título e Descrição da Página ---
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Análise Descritiva de Questões</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Esta página apresenta uma análise descritiva de respostas a questões da pesquisa. É importante notar que os dados exibidos são baseados em uma **amostra** das famílias atingidas. As visualizações e estatísticas refletem as **observações e padrões identificados dentro desta amostra**. <br>
Portanto, as conclusões aqui apresentadas são referentes aos respondentes da pesquisa e não podem ser generalizadas diretamente para toda a população sem uma análise estatística inferencial adequada.
</p>
""", unsafe_allow_html=True)

# --- Controles de Seleção ---
if filtered_question_groups:
    col_group, col_question = st.columns([1, 2])
    
    with col_group:
        selected_group = st.selectbox(
            "Selecione um Grupo de Questões:",
            list(filtered_question_groups.keys()),
            key="group_selector"
        )

    if selected_group:
        if selected_group == "Sentimentos e Percepções":
            current_df_for_analysis = df_sentiment_filtered_by_main
        else:
            current_df_for_analysis = df 
        
        cols_in_selected_group = [col for col in filtered_question_groups[selected_group] if col in current_df_for_analysis.columns]
        options_for_selectbox = [("Selecione uma questão", None)] + [(question_labels.get(col, col), col) for col in cols_in_selected_group]
        
        with col_question:
            selected_option = st.selectbox(
                "Selecione uma Questão para Analisar:",
                options_for_selectbox,
                format_func=lambda x: x[0],
                key="single_question_selector"
            )
        selected_column = selected_option[1]

        if selected_column:
            is_numeric_column = pd.api.types.is_numeric_dtype(current_df_for_analysis[selected_column]) and selected_column != 'NF1'

            # --- Análise de Colunas Numéricas ---
            if is_numeric_column:
                st.subheader(f"📊 Distribuição de '{question_labels.get(selected_column, selected_column)}' na Amostra")
                
                fig_hist = px.histogram(
                    current_df_for_analysis.dropna(subset=[selected_column]),
                    x=selected_column,
                    title=f'Histograma de {question_labels.get(selected_column, selected_column)} na Amostra',
                    nbins=20,
                    color_discrete_sequence=px.colors.qualitative.G10 
                )
                fig_hist.update_layout(title_x=0.5, xaxis_title=question_labels.get(selected_column, selected_column), yaxis_title="Frequência (Contagem de Respondentes)")
                st.plotly_chart(fig_hist, use_container_width=True)
                
                st.markdown("#### Estatísticas Descritivas na Amostra")
                st.dataframe(current_df_for_analysis[selected_column].describe().to_frame(), use_container_width=True)
                st.caption("Estatísticas calculadas com base nas respostas válidas da amostra para esta questão (exclui valores nulos).")

            # --- Análise de Colunas Categóricas/Qualitativas ---
            else:
                contagem_geral = current_df_for_analysis[selected_column].dropna().value_counts()
                total_respostas = contagem_geral.sum() 

                if total_respostas == 0:
                    st.warning(f"Nenhuma resposta encontrada para a questão '{question_labels.get(selected_column, selected_column)}' nesta amostra.")
                else:
                    st.subheader(f"📈 Distribuição de Respostas para '{question_labels.get(selected_column, selected_column)}' na Amostra")

                    # --- Lógica de Agrupamento e Expansão ---
                    if len(contagem_geral) > MAX_CATEGORIES_DEFAULT_DISPLAY:
                        st.info(f"Mais de {MAX_CATEGORIES_DEFAULT_DISPLAY} categorias. Exibindo as principais respostas por padrão.")
                        show_all_categories = st.checkbox(
                            "Visualizar todas as categorias de respostas?",
                            key=f"show_all_categories_{selected_column}"
                        )
                        if not show_all_categories:
                            # Top N + "Outros"
                            top_n = contagem_geral.head(MAX_CATEGORIES_DEFAULT_DISPLAY - 1) 
                            outros_count = contagem_geral.iloc[MAX_CATEGORIES_DEFAULT_DISPLAY - 1:].sum()
                            
                            resultados_generais_display = pd.DataFrame({
                                'Resposta': top_n.index.tolist() + ['Outros'],
                                'Número de Respondentes': top_n.values.tolist() + [outros_count]
                            })
                            resultados_generais_display['Porcentagem (%)'] = (resultados_generais_display['Número de Respondentes'] / total_respostas) * 100 
                            resultados_generais_display['Porcentagem (%)'] = resultados_generais_display['Porcentagem (%)'].round(2)
                            
                            # Para garantir que 'Outros' esteja no final para visualização clara,
                            # mesmo que sua contagem seja alta.
                            if 'Outros' in resultados_generais_display['Resposta'].values:
                                outros_row = resultados_generais_display[resultados_generais_display['Resposta'] == 'Outros']
                                resultados_generais_display = resultados_generais_display[resultados_generais_display['Resposta'] != 'Outros'].sort_values(by='Número de Respondentes', ascending=False)
                                resultados_generais_display = pd.concat([resultados_generais_display, outros_row]).reset_index(drop=True)
                            else: # Caso não haja 'Outros' (número exato de categorias)
                                resultados_generais_display = resultados_generais_display.sort_values(by='Número de Respondentes', ascending=False)


                        else:
                            # Todas as categorias
                            resultados_generais_display = pd.DataFrame({
                                'Resposta': contagem_geral.index,
                                'Número de Respondentes': contagem_generais.values # Mudado para contagem_gerais.values
                            })
                            resultados_generais_display['Porcentagem (%)'] = (resultados_generais_display['Número de Respondentes'] / total_respostas) * 100 
                            resultados_generais_display['Porcentagem (%)'] = resultados_generais_display['Porcentagem (%)'].round(2)
                            resultados_generais_display = resultados_generais_display.sort_values(by='Número de Respondentes', ascending=False)
                    else:
                        # Menos categorias, mostra todas por padrão
                        resultados_generais_display = pd.DataFrame({
                            'Resposta': contagem_geral.index,
                            'Número de Respondentes': contagem_geral.values
                        })
                        resultados_generais_display['Porcentagem (%)'] = (resultados_generais_display['Número de Respondentes'] / total_respostas) * 100 
                        resultados_generais_display['Porcentagem (%)'] = resultados_generais_display['Porcentagem (%)'].round(2)
                        resultados_generais_display = resultados_generais_display.sort_values(by='Número de Respondentes', ascending=False)


                    col_options_display, col_options_chart = st.columns(2)
                    with col_options_display:
                        display_mode_general = st.radio(
                            "Visualizar como:", 
                            ("Número de Respondentes", "Porcentagem (%)"), 
                            index=0,
                            key=f"display_mode_{selected_column}"
                        )
                    with col_options_chart:
                        chart_type_general = st.radio(
                            "Tipo de Gráfico:", 
                            ("Barra Vertical", "Barra Horizontal", "Pizza"),
                            index=0,
                            key=f"chart_type_{selected_column}"
                        )
                    
                    st.dataframe(resultados_generais_display, use_container_width=True) 
                    st.caption(f"Tabela de frequência: Mostra a contagem de respondentes e a porcentagem de cada resposta **na amostra**. As porcentagens são calculadas sobre o total de {total_respostas} respostas válidas para esta questão na amostra.")

                    # --- Botões de Download (USAR resultados_generais_display) ---
                    download_col1, download_col2 = st.columns(2)
                    with download_col1:
                        csv_data = resultados_generais_display.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar Tabela (CSV)", 
                            data=csv_data, 
                            file_name=f"{selected_column}_distribuicao_amostra.csv", 
                            mime="text/csv", 
                            key=f"download_csv_{selected_column}",
                            help="Baixa os dados da tabela em formato CSV, baseados nas respostas da amostra."
                        )
                    with download_col2:
                        excel_buffer = io.BytesIO()
                        resultados_generais_display.to_excel(excel_buffer, index=False, engine='xlsxwriter')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="📥 Baixar Tabela (Excel)", 
                            data=excel_buffer.getvalue(), 
                            file_name=f"{selected_column}_distribuicao_amostra.xlsx", 
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                            key=f"download_excel_{selected_column}",
                            help="Baixa os dados da tabela em formato XLSX, baseados nas respostas da amostra."
                        )
                    st.markdown("---")
                    st.info("💡 Dica: Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

                    # --- Geração do Gráfico (USAR resultados_generais_display) ---
                    if chart_type_general == "Barra Vertical":
                        fig_general = create_bar_chart(resultados_generais_display, 'Resposta', display_mode_general, 
                                                       f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" na Amostra ({display_mode_general})', 
                                                       'Resposta', orientation='v')
                        st.plotly_chart(fig_general, use_container_width=True)
                    elif chart_type_general == "Barra Horizontal":
                        fig_general = create_bar_chart(resultados_generais_display, 'Resposta', display_mode_general, 
                                                       f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" na Amostra ({display_mode_general})', 
                                                       'Resposta', orientation='h')
                        st.plotly_chart(fig_general, use_container_width=True)
                    elif chart_type_general == "Pizza":
                        fig_general = create_pie_chart(resultados_generais_display, 'Resposta', display_mode_general, 
                                                       f'Distribuição de Respostas para "{question_labels.get(selected_column, selected_column)}" na Amostra ({display_mode_general})')
                        st.plotly_chart(fig_general, use_container_width=True)
        else:
            st.info("Por favor, selecione uma questão para visualizar a análise descritiva da amostra.")

        # --- Detalhamento por Território, Gênero e Raça/Cor ---
        if selected_column: 
            st.markdown("---")
            st.markdown("<h3 style='color: #264653;'>Padrões por Demografia Chave na Amostra</h3>", unsafe_allow_html=True)
            st.write(f"As visualizações a seguir exploram a distribuição da questão **'{question_labels.get(selected_column, selected_column)}'** cruzada com Território, Gênero e Raça/Cor, conforme observado **nesta amostra de respondentes.**")

            df_detail_data = None
            if selected_group == "Sentimentos e Percepções":
                if 'ID' in df_sentiment_filtered_by_main.columns and 'ID' in df.columns:
                    df_detail_data = df_sentiment_filtered_by_main[[selected_column, 'ID']].merge(
                        df[['ID', 'ADAI_CT4', 'ADAI_ID8', 'ID7']], on='ID', how='inner')
                else:
                    st.warning("Para detalhamento de sentimentos, a coluna 'ID' é necessária em ambos os DataFrames (Sentimentos e Principal) para cruzar com dados demográficos da amostra.")
                    df_detail_data = pd.DataFrame() 
            else:
                df_detail_data = df[[selected_column, 'ADAI_CT4', 'ADAI_ID8', 'ID7']].copy() 
            
            if df_detail_data is not None and not df_detail_data.empty:
                if 'ADAI_CT4' in df_detail_data.columns: 
                    display_cross_tabulation(df_detail_data, selected_column, 'ADAI_CT4', 'Território', question_labels)

                if 'ADAI_ID8' in df_detail_data.columns: 
                    display_cross_tabulation(df_detail_data, selected_column, 'ADAI_ID8', 'Gênero', question_labels)

                if 'ID7' in df_detail_data.columns: 
                    display_cross_tabulation(df_detail_data, selected_column, 'ID7', 'Raça/Cor', question_labels)
            else:
                st.warning("Não há dados de detalhamento demográfico disponíveis nesta amostra para a questão selecionada, após a combinação de DataFrames ou as colunas demográficas estão ausentes.")

else:
    st.warning("Nenhum grupo de colunas categóricas foi identificado para análise. Verifique seus dados de configuração (filtered_question_groups).")
