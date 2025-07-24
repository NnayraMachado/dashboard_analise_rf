import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os # Para carregar CSS

# --- Função para carregar CSS (assumindo que 'styles.css' está na raiz do projeto) ---
# Se o CSS já é carregado globalmente no app.py, remova esta seção.
def load_css_from_root(file_name="styles.css"):
    current_script_dir = os.path.dirname(__file__)
    root_dir = os.path.join(current_script_dir, '..')
    css_file_path = os.path.join(root_dir, file_name)
    try:
        with open(css_file_path, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Certifique-se de que ele está na pasta raiz do seu projeto.")

# Carrega o CSS
load_css_from_root() # Assume styles.css está na raiz

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()
    
df = st.session_state.get('df')
df_sentiment_filtered_by_main = st.session_state.get('df_sentiment_filtered_by_main')
question_labels = st.session_state.get('question_labels')
all_selectable_categorical_cols = st.session_state.get('all_selectable_categorical_cols')

# --- Verifica se os DataFrames essenciais estão carregados ---
if df is None or df_sentiment_filtered_by_main is None or question_labels is None or all_selectable_categorical_cols is None:
    st.error("Erro: Dados essenciais não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop() 

# --- Funções Auxiliares para Geração de Gráficos Cruzados ---

def create_crosstab_bar_chart(df_plot, x_col, y_col, color_col, title, barmode_type, x_label, y_label):
    fig = px.bar(
        df_plot,
        x=x_col,
        y=y_col,
        color=color_col,
        barmode=barmode_type,
        title=title,
        text_auto=True, # Adicionado text_auto para valores nas barras
        color_discrete_sequence=px.colors.qualitative.Plotly # Paleta de cores consistente
    )
    fig.update_layout(
        xaxis={'categoryorder':'total descending', 'title': x_label},
        yaxis={'title': y_label},
        title_x=0.5, # Centraliza o título
        font=dict(size=12) # Ajusta o tamanho da fonte para melhor legibilidade
    )
    fig.update_traces(texttemplate='%{y}', textposition='inside') # Formatação do texto dentro da barra
    return fig

# --- Título e Descrição da Página ---
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Análise Cruzada de Questões</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Nesta seção, você pode explorar a relação entre duas questões da pesquisa. As visualizações e tabelas exibem a distribuição conjunta de respostas com base na **amostra coletada**. <br>
É importante lembrar que esta é uma análise **descritiva**, focada em identificar padrões e associações observadas nos dados da amostra, e não em fazer generalizações estatisticamente válidas para toda a população.
</p>
""", unsafe_allow_html=True)

# --- Controles de Seleção ---
if len(all_selectable_categorical_cols) >= 2:
    options_for_cross_selectbox = [("Selecione uma questão", None)] + [
        (question_labels.get(col, col), col) for col in all_selectable_categorical_cols
    ]
    
    col_sel1, col_sel2 = st.columns(2) # Coloca seletores lado a lado

    with col_sel1:
        selected_option_col1 = st.selectbox(
            "Questão para Linhas da Tabela (Eixo X do Gráfico):", # Rótulo mais claro
            options_for_cross_selectbox,
            format_func=lambda x: x[0],
            key="cross_col1"
        )
        col1_cross = selected_option_col1[1]

    with col_sel2:
        # Filtra para que a segunda coluna não seja a mesma da primeira
        options_for_col2_cross = [("Selecione uma questão", None)] + [
            (question_labels.get(col, col), col) for col in all_selectable_categorical_cols if col != col1_cross
        ]
        selected_option_col2 = st.selectbox(
            "Questão para Colunas da Tabela (Cores do Gráfico):", # Rótulo mais claro
            options_for_col2_cross,
            format_func=lambda x: x[0],
            key="cross_col2"
        )
        col2_cross = selected_option_col2[1]

    if col1_cross and col2_cross:
        temp_df_cross = None

        # Lógica para combinar DataFrames (mantida pois já funciona)
        # Otimizado para evitar repetir 'df.columns' e 'df_sentiment_filtered_by_main.columns'
        col1_in_main = col1_cross in df.columns
        col2_in_main = col2_cross in df.columns
        col1_in_sentiment = col1_cross in df_sentiment_filtered_by_main.columns
        col2_in_sentiment = col2_cross in df_sentiment_filtered_by_main.columns

        if col1_in_main and col2_in_main:
            temp_df_cross = df[[col1_cross, col2_cross]]
        elif col1_in_sentiment and col2_in_sentiment:
            temp_df_cross = df_sentiment_filtered_by_main[[col1_cross, col2_cross]]
        elif 'ID' in df.columns and 'ID' in df_sentiment_filtered_by_main.columns:
            if col1_in_main and col2_in_sentiment:
                temp_df_cross = df[[col1_cross, 'ID']].merge(
                    df_sentiment_filtered_by_main[[col2_cross, 'ID']], on='ID', how='inner'
                )
            elif col1_in_sentiment and col2_in_main:
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
                f"Não há dados válidos na amostra para cruzar as questões '{question_labels.get(col1_cross, col1_cross)}' e '{question_labels.get(col2_cross, col2_cross)}' após remover valores em branco."
            )
        else:
            st.subheader(
                f"Tabela Cruzada: '{question_labels.get(col1_cross, col1_cross)}' por '{question_labels.get(col2_cross, col2_cross)}' na Amostra"
            )

            col_cross_display, col_cross_chart = st.columns(2)
            with col_cross_display:
                cross_display_mode = st.radio(
                    "Exibir Tabela como:", # Rótulo mais claro
                    (
                        "Contagem (Número de Respondentes)",
                        "Porcentagem por Linha (%)",
                        "Porcentagem por Coluna (%)",
                        "Porcentagem Total (%)"
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

            # Lógica para a tabela e explicações
            if cross_display_mode == "Contagem (Número de Respondentes)":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross])
                st.caption(f"Tabela: Contagem do número de respondentes na amostra para cada combinação de respostas.")
            elif cross_display_mode == "Porcentagem por Linha (%)":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='index').mul(100).round(2)
                st.caption(f"Tabela: Porcentagem de respostas de '{question_labels.get(col2_cross, col2_cross)}' DENTRO de cada categoria de '{question_labels.get(col1_cross, col1_cross)}'.")
            elif cross_display_mode == "Porcentagem por Coluna (%)":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='columns').mul(100).round(2)
                st.caption(f"Tabela: Porcentagem de respostas de '{question_labels.get(col1_cross, col1_cross)}' DENTRO de cada categoria de '{question_labels.get(col2_cross, col2_cross)}'.")
            elif cross_display_mode == "Porcentagem Total (%)":
                crosstab_table = pd.crosstab(df_cross[col1_cross], df_cross[col2_cross], normalize='all').mul(100).round(2)
                st.caption(f"Tabela: Porcentagem de cada combinação de respostas sobre o TOTAL de respondentes válidos na amostra.")

            st.dataframe(crosstab_table, use_container_width=True)

            # --- Botões de Download ---
            download_col1, download_col2 = st.columns(2)
            with download_col1:
                csv_data_cross = crosstab_table.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Baixar Tabela (CSV)",
                    data=csv_data_cross,
                    file_name=f"{col1_cross}_x_{col2_cross}_cruzamento_amostra.csv", # Nome mais descritivo
                    mime="text/csv",
                    key=f"download_csv_cross_{col1_cross}_{col2_cross}",
                    help="Baixa os dados da tabela de cruzamento em formato CSV."
                )
            with download_col2:
                excel_buffer_cross = io.BytesIO()
                crosstab_table.to_excel(excel_buffer_cross, engine='xlsxwriter')
                excel_buffer_cross.seek(0)
                st.download_button(
                    label="📥 Baixar Tabela (Excel)",
                    data=excel_buffer_cross.getvalue(),
                    file_name=f"{col1_cross}_x_{col2_cross}_cruzamento_amostra.xlsx", # Nome mais descritivo
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_excel_cross_{col1_cross}_{col2_cross}",
                    help="Baixa os dados da tabela de cruzamento em formato XLSX."
                )
            st.markdown("---")
            st.info("💡 Dica: Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

            st.subheader("Visualização Cruzada na Amostra")
            
            # Preparar dados para o gráfico baseado no modo de exibição
            if cross_display_mode == "Contagem (Número de Respondentes)":
                plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Valor')
                y_axis_title = "Número de Respondentes"
                chart_title_suffix = "(Contagem)"
            elif cross_display_mode == "Porcentagem por Linha (%)":
                # Para porcentagem por linha no gráfico, precisamos recalcular
                # a partir do DataFrame original, para que o Plotly empilhe % de 100%
                plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Contagem')
                plot_df_pivot = plot_df.pivot_table(index=col1_cross, columns=col2_cross, values='Contagem', fill_value=0)
                plot_df_norm = plot_df_pivot.div(plot_df_pivot.sum(axis=1), axis=0).mul(100).round(2).reset_index()
                plot_df = plot_df_norm.melt(id_vars=col1_cross, var_name=col2_cross, value_name='Valor')
                y_axis_title = "Porcentagem (%)"
                chart_title_suffix = "(Porcentagem por Linha)"
            elif cross_display_mode == "Porcentagem por Coluna (%)":
                plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Contagem')
                plot_df_pivot = plot_df.pivot_table(index=col1_cross, columns=col2_cross, values='Contagem', fill_value=0)
                plot_df_norm = plot_df_pivot.div(plot_df_pivot.sum(axis=0), axis=1).mul(100).round(2).reset_index()
                plot_df = plot_df_norm.melt(id_vars=col1_cross, var_name=col2_cross, value_name='Valor')
                y_axis_title = "Porcentagem (%)"
                chart_title_suffix = "(Porcentagem por Coluna)"
            elif cross_display_mode == "Porcentagem Total (%)":
                plot_df = df_cross.groupby([col1_cross, col2_cross]).size().reset_index(name='Contagem')
                total_sum = plot_df['Contagem'].sum()
                plot_df['Valor'] = (plot_df['Contagem'] / total_sum) * 100
                y_axis_title = "Porcentagem (%)"
                chart_title_suffix = "(Porcentagem Total)"
            
            # Gráficos de barras
            if chart_type_cross == "Barras Empilhadas":
                fig_cross = create_crosstab_bar_chart(
                    plot_df,
                    x_col=col1_cross,
                    y_col='Valor',
                    color_col=col2_cross,
                    title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} na Amostra {chart_title_suffix}',
                    barmode_type='relative', # 'relative' para empilhar em 100% para porcentagens, 'stack' para contagens
                    x_label=question_labels.get(col1_cross, col1_cross),
                    y_label=y_axis_title
                )
                # Ajusta barmode para 'stack' se for contagem e 'relative' para porcentagem
                if cross_display_mode == "Contagem (Número de Respondentes)":
                    fig_cross.update_layout(barmode='stack')
                else:
                    fig_cross.update_layout(barmode='relative', yaxis_range=[0,100]) # Garante 0-100% para empilhado relativo

                st.plotly_chart(fig_cross, use_container_width=True)
            
            elif chart_type_cross == "Barras Agrupadas":
                fig_cross = create_crosstab_bar_chart(
                    plot_df,
                    x_col=col1_cross,
                    y_col='Valor',
                    color_col=col2_cross,
                    title=f'Distribuição de {question_labels.get(col1_cross, col1_cross)} por {question_labels.get(col2_cross, col2_cross)} na Amostra {chart_title_suffix}',
                    barmode_type='group',
                    x_label=question_labels.get(col1_cross, col1_cross),
                    y_label=y_axis_title
                )
                st.plotly_chart(fig_cross, use_container_width=True)
    else:
        st.info("Por favor, selecione duas questões para realizar a análise cruzada.")
else:
    st.warning("Não há colunas categóricas suficientes para realizar a análise cruzada (mínimo de 2). Verifique seus dados de configuração.")
