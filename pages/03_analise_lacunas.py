import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os # Para carregar CSS

# --- Função para carregar CSS (assumindo que 'styles.css' está na raiz do projeto) ---
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
load_css_from_root() 

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()
    
df = st.session_state.get('df')
df_sentiment_filtered_by_main = st.session_state.get('df_sentiment_filtered_by_main') # Garantir que esta variável exista na sessão se for usada
question_labels = st.session_state.get('question_labels')

# --- Verifica se os DataFrames essenciais estão carregados ---
if df is None or question_labels is None: # df_sentiment_filtered_by_main não é diretamente usado aqui.
    st.error("Erro: Dados essenciais não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop() 

# --- Definição dos Pares de Análise de Lacunas ---
gap_analysis_pairs = {
    "Acesso a Programas Sociais (ID13/ID14)": ('ID13', 'ID14'),
    "Acesso à Água do Rio Doce (AQA1/AQA2)": ('AQA1', 'AQA2'),
    "Exercia Atividade Remunerada (AER1/ARF1.1)": ('AER1', 'ARF1.1'), 
}

# Filtra pares disponíveis com base nas colunas do DF
available_gap_pairs = {k: v for k, v in gap_analysis_pairs.items() if v[0] in df.columns and v[1] in df.columns}

# --- Título e Descrição da Página ---
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Análise de Lacunas: Antes vs. Depois</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Esta seção permite comparar a situação dos respondentes em dimensões específicas **antes e depois do rompimento da barragem**, identificando impactos e lacunas. <br>
Os dados apresentados são baseados em uma **amostra** das famílias afetadas. As análises aqui são **descritivas**, mostrando padrões e mudanças **observadas dentro desta amostra**, e não devem ser generalizadas para toda a população sem inferência estatística apropriada.
</p>
""", unsafe_allow_html=True)

if not available_gap_pairs:
    st.warning("Nenhum par de perguntas 'Antes/Depois' encontrado para análise de lacunas na sua base de dados. Verifique a existência das colunas necessárias.")
else:
    selected_gap_pair_label = st.selectbox(
        "Selecione a Dimensão para Análise de Lacunas:",
        list(available_gap_pairs.keys()),
        key="gap_pair_selector"
    )

    if selected_gap_pair_label:
        col_antes, col_depois = available_gap_pairs[selected_gap_pair_label]

        st.subheader(f"Comparativo: '{question_labels.get(col_antes, col_antes)}' vs. '{question_labels.get(col_depois, col_depois)}' na Amostra")
        df_gap = df[[col_antes, col_depois]].dropna()

        if not df_gap.empty:
            counts_antes = df_gap[col_antes].value_counts(normalize=True).mul(100).round(2).reset_index()
            counts_antes.columns = ['Resposta', 'Porcentagem (%)']
            counts_antes['Período'] = 'Antes do Rompimento'

            counts_depois = df_gap[col_depois].value_counts(normalize=True).mul(100).round(2).reset_index()
            counts_depois.columns = ['Resposta', 'Porcentagem (%)']
            counts_depois['Período'] = 'Depois do Rompimento'

            combined_counts = pd.concat([counts_antes, counts_depois])

            # --- Gráfico de Barras Agrupadas para Comparação ---
            fig_gap = px.bar(
                combined_counts,
                x='Resposta',
                y='Porcentagem (%)',
                color='Período',
                barmode='group',
                title=f'Comparativo de "{selected_gap_pair_label}" Antes e Depois do Rompimento na Amostra',
                text_auto=True, # Exibe valores automaticamente
                color_discrete_map={ # Cores mais contrastantes
                    'Antes do Rompimento': '#2a9d8f', # Um verde azulado
                    'Depois do Rompimento': '#e76f51' # Um laranja avermelhado
                }
            )
            fig_gap.update_layout(
                xaxis={'categoryorder':'total descending', 'title': 'Resposta'},
                yaxis={'title': 'Porcentagem de Respondentes (%)'},
                title_x=0.5, # Centraliza o título
                font=dict(size=12) # Ajusta o tamanho da fonte para melhor legibilidade
            )
            fig_gap.update_traces(textposition='outside') # Coloca o texto fora das barras para clareza
            st.plotly_chart(fig_gap, use_container_width=True)
            st.caption("Gráfico: Porcentagem de respondentes na amostra que selecionaram cada resposta em cada período. As porcentagens são calculadas sobre o total de respostas válidas para o respectivo período.")

            st.markdown("#### Tabela Comparativa de Transição (Contagens Absolutas)")
            crosstab_gap_counts = pd.crosstab(df_gap[col_antes], df_gap[col_depois])
            st.dataframe(crosstab_gap_counts, use_container_width=True)
            st.caption("Tabela: Mostra o número absoluto de respondentes na amostra que passaram de uma situação 'Antes' para uma situação 'Depois'.")

            st.markdown("#### Tabela de Impacto (Porcentagem por Linha)")
            crosstab_gap_perc = pd.crosstab(df_gap[col_antes], df_gap[col_depois], normalize='index').mul(100).round(2)
            st.dataframe(crosstab_gap_perc, use_container_width=True)
            st.caption("Tabela: Para cada situação 'Antes' (linha), mostra a porcentagem de respondentes que se encontraram em cada situação 'Depois' (coluna). Útil para entender como as pessoas *transitaram* de um estado para outro na amostra.")

            # --- KPI de Mudança (usando st.metric) ---
            st.markdown("---")
            st.subheader("Indicador Chave de Desempenho (KPI)")
            kpi_value_before = 0
            kpi_value_after = 0
            
            # Tenta encontrar a porcentagem de 'Sim' ou 'Positivo' para o KPI
            # Idealmente, você definiria qual resposta é a 'positiva' ou 'de interesse'
            # Por simplicidade, vamos focar em 'Sim' ou na primeira resposta positiva.
            
            # Busca por "Sim"
            if 'Sim' in counts_antes['Resposta'].values:
                kpi_value_before = counts_antes[counts_antes['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
            if 'Sim' in counts_depois['Resposta'].values:
                kpi_value_after = counts_depois[counts_depois['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
            
            # Se 'Sim' não for encontrado, tenta 'Sim, tinha' ou similar
            elif 'Sim, tinha' in counts_antes['Resposta'].values:
                kpi_value_before = counts_antes[counts_antes['Resposta'] == 'Sim, tinha']['Porcentagem (%)'].iloc[0]
            if 'Sim, tinha' in counts_depois['Resposta'].values:
                kpi_value_after = counts_depois[counts_depois['Resposta'] == 'Sim, tinha']['Porcentagem (%)'].iloc[0]

            delta_value = kpi_value_after - kpi_value_before
            delta_color = "inverse" if delta_value < 0 else "normal" # 'inverse' para vermelho se for negativo (impacto negativo)

            st.metric(
                label=f"Mudança Percentual em '{selected_gap_pair_label}' (Resposta 'Sim' ou similar)",
                value=f"{kpi_value_after:.1f}%",
                delta=f"{delta_value:.1f} p.p.", # p.p. = pontos percentuais
                delta_color=delta_color
            )
            st.caption(f"Este KPI mostra a porcentagem de respondentes na amostra que se enquadram na categoria 'Sim' (ou similar) para '{selected_gap_pair_label}', antes e depois do rompimento, e a variação em pontos percentuais. Um delta negativo indica uma redução na ocorrência desta categoria.")

            # --- Resumo Automático (IA - Lógica Simples) ---
            st.markdown("---")
            st.subheader("Análise Qualitativa Observada")
            
            # Lógica simples para gerar um resumo baseado no delta
            if delta_value is not None:
                summary_text = f"Para a dimensão '{selected_gap_pair_label}', observa-se na amostra que a porcentagem de respondentes que afirmam 'Sim' (ou similar) foi de **{kpi_value_before:.1f}% antes** do rompimento e **{kpi_value_after:.1f}% depois**."
                
                if delta_value < -5: # Grande queda
                    summary_text += f" Houve uma **redução significativa de {abs(delta_value):.1f} pontos percentuais**, indicando um **impacto negativo considerável** nesta área para os respondentes da pesquisa."
                elif delta_value < 0: # Pequena queda
                    summary_text += f" Houve uma **redução de {abs(delta_value):.1f} pontos percentuais**, sugerindo um impacto negativo nesta área para os respondentes da pesquisa."
                elif delta_value > 5: # Grande aumento
                    summary_text += f" Houve um **aumento significativo de {delta_value:.1f} pontos percentuais**, o que pode indicar uma melhora ou um foco maior nesta área para os respondentes da pesquisa."
                elif delta_value > 0: # Pequeno aumento
                    summary_text += f" Houve um **aumento de {delta_value:.1f} pontos percentuais**, o que pode sugerir uma pequena melhora ou variação natural."
                else: # Nenhuma mudança
                    summary_text += " Não houve uma mudança perceptível na porcentagem de respondentes que afirmam 'Sim' (ou similar)."
                
                st.info(summary_text)
            else:
                st.info("Não foi possível gerar um resumo automático para esta dimensão, pois os dados para o KPI 'Sim' não estão completos.")

            # --- Botões de Download dos Dados Brutos ---
            st.markdown("---")
            st.subheader("Opções de Download dos Dados Brutos")
            
            download_col1, download_col2, download_col3 = st.columns(3)

            with download_col1:
                csv_combined = combined_counts.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Dados Comparativos (CSV)",
                    data=csv_combined,
                    file_name=f"{selected_gap_pair_label}_comparativo_amostra.csv",
                    mime="text/csv",
                    key="download_comparative_csv",
                    help="Baixa a tabela de porcentagens 'Antes' e 'Depois'."
                )
            with download_col2:
                csv_crosstab_counts = crosstab_gap_counts.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Tabela de Transição (CSV)",
                    data=csv_crosstab_counts,
                    file_name=f"{selected_gap_pair_label}_transicao_contagens_amostra.csv",
                    mime="text/csv",
                    key="download_crosstab_counts_csv",
                    help="Baixa a tabela de contagens de transição."
                )
            with download_col3:
                csv_crosstab_perc = crosstab_gap_perc.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Tabela de Impacto (CSV)",
                    data=csv_crosstab_perc,
                    file_name=f"{selected_gap_pair_label}_impacto_porcentagens_amostra.csv",
                    mime="text/csv",
                    key="download_crosstab_perc_csv",
                    help="Baixa a tabela de porcentagens de impacto."
                )
            st.info("💡 Dica: Para baixar o gráfico, clique com o botão direito sobre ele e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

        else:
            st.warning("Não há dados válidos na amostra para as questões selecionadas após remover valores em branco.")
    else:
        st.info("Por favor, selecione uma dimensão para visualizar a análise de lacunas.")
