import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

from utils.session import ensure_session_data
ensure_session_data()

df = st.session_state.get('df')
df_sentiment_filtered_by_main = st.session_state.get('df_sentiment_filtered_by_main')
question_labels = st.session_state.get('question_labels')

if df is None or df_sentiment_filtered_by_main is None or question_labels is None:
    st.error("Erro: Dados essenciais não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop() 

# --- Mapeamentos de Variáveis ---
vulnerability_vars = {
    'ID7': 'Raça/Cor',
    'ADAI_ID8': 'Gênero',
    'ID10': 'Pessoa com Deficiência (PcD)', 
    'PCT0': 'Povo/Comunidade Tradicional',
}

impact_vars = {
    'ARF3.1': 'Perda de Renda (Comprovada)', 
    'DF1': 'Dívida Contraída/Aumentada',
    'SA1': 'Comprometimento Qualidade Alimentos',
    'CCS7': 'Aumento Gastos Saúde',
}

# --- MAPEAMENTO DA SEMÂNTICA DAS RESPOSTAS PARA CORES DO DELTA ---
# Chave: Nome da Coluna de Impacto (do impact_vars)
# Valor: Dicionário onde a chave é a resposta (ex: 'Sim', 'Não', 'Não sei')
#        e o valor é "good" (verde) ou "bad" (vermelho) para a cor do delta
#        quando essa resposta tem uma alta porcentagem.
response_sentiment_map = {
    'ARF3.1': {'Sim': 'bad', 'Não': 'good', 'Não tenho como comprovar': 'bad'}, # Perda de Renda: Sim=bad, Não=good
    'DF1': {'Sim': 'bad', 'Não': 'good'}, # Dívida: Sim=bad, Não=good
    'SA1': {'Sim': 'bad', 'Não': 'good'}, # Qualidade Alimentos: Sim=bad (comprometimento), Não=good
    'CCS7': {'Sim': 'bad', 'Não': 'good'}, # Aumento Gastos Saúde: Sim=bad, Não=good
    # Adicione outros mapeamentos conforme suas variáveis de impacto e suas respostas
    # Ex: Para perguntas com respostas tipo Likert (muito bom, bom, regular, ruim, muito ruim)
    # 'PercepcaoGeral': {'Muito Bom': 'good', 'Bom': 'good', 'Regular': 'neutral', 'Ruim': 'bad', 'Muito Ruim': 'bad'}
}


available_impact_vars = {k: v for k, v in impact_vars.items() if k in df.columns or k in df_sentiment_filtered_by_main.columns}
available_vulnerability_vars = {k: v for k, v in vulnerability_vars.items() if k in df.columns}

# --- Título e Descrição da Página ---
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Análise de Vulnerabilidade e Impacto</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Esta seção explora como diferentes grupos demográficos podem ter sido impactados ou percebem a situação, permitindo a identificação de **potenciais vulnerabilidades**. <br>
Os dados são baseados em uma **amostra** de respondentes. As análises são **descritivas**, focando em padrões e associações **observadas nesta amostra**, e não devem ser generalizadas para toda a população sem métodos estatísticos inferenciais apropriados.
</p>
""", unsafe_allow_html=True)

if not available_impact_vars or not available_vulnerability_vars:
    st.warning("Não há variáveis de vulnerabilidade ou de impacto suficientes nos DataFrames carregados para realizar esta análise.")
else:
    col_sel_v, col_sel_impact = st.columns(2)
    with col_sel_v:
        selected_v_var = st.selectbox(
            "Selecione a Variável Demográfica (Grupos de Vulnerabilidade):", 
            list(available_vulnerability_vars.keys()),
            format_func=lambda x: available_vulnerability_vars[x],
            key="v_var_selector"
        )
    with col_sel_impact:
        selected_impact_var = st.selectbox(
            "Selecione a Variável de Impacto para Analisar:", 
            list(available_impact_vars.keys()),
            format_func=lambda x: available_impact_vars[x],
            key="impact_var_selector"
        )

    if selected_v_var and selected_impact_var:
        st.subheader(f"Impacto de '{vulnerability_vars.get(selected_v_var, selected_v_var)}' na '{impact_vars.get(selected_impact_var, selected_impact_var)}' na Amostra")

        df_vulnerability_analysis = pd.DataFrame() 
        
        with st.spinner("Combinando dados para análise..."):
            if selected_impact_var in df_sentiment_filtered_by_main.columns:
                if selected_v_var in df.columns and 'ID' in df.columns and 'ID' in df_sentiment_filtered_by_main.columns:
                    df_vulnerability_analysis = df_sentiment_filtered_by_main[[selected_impact_var, 'ID']].merge(
                        df[[selected_v_var, 'ID']], on='ID', how='inner'
                    ).dropna()
                else:
                    st.warning("Não foi possível cruzar a variável de sentimento com a demográfica. Verifique se 'ID' está presente em ambos os DataFrames ou se as variáveis estão disponíveis.")
            elif selected_impact_var in df.columns and selected_v_var in df.columns:
                df_vulnerability_analysis = df[[selected_v_var, selected_impact_var]].dropna().copy() 
            else:
                st.warning("Variáveis selecionadas não encontradas nos DataFrames carregados ou não podem ser combinadas.")
            
        if not df_vulnerability_analysis.empty:
            
            crosstab_v = pd.crosstab(
                df_vulnerability_analysis[selected_v_var],
                df_vulnerability_analysis[selected_impact_var],
                normalize='index' 
            ).mul(100).round(2)

            st.markdown("#### Tabela de Porcentagens de Impacto por Grupo Demográfico")
            st.dataframe(crosstab_v, use_container_width=True)
            st.caption(f"Tabela: Para cada grupo de '{vulnerability_vars.get(selected_v_var, selected_v_var)}' (linhas), mostra a porcentagem de respondentes na amostra que se enquadram em cada categoria de '{impact_vars.get(selected_impact_var, selected_impact_var)}' (colunas). Útil para ver a distribuição do impacto DENTRO de cada grupo.")

            # --- Gráfico de Barras Agrupadas ---
            st.subheader("Visualização por Grupo Demográfico e Impacto")
            fig_v = px.bar(
                crosstab_v.reset_index().melt(id_vars=selected_v_var, var_name='Categoria de Impacto', value_name='Porcentagem (%)'),
                x=selected_v_var,
                y='Porcentagem (%)',
                color='Categoria de Impacto',
                barmode='group',
                title=f'Porcentagem de Respostas para "{impact_vars.get(selected_impact_var, selected_impact_var)}" por "{vulnerability_vars.get(selected_v_var, selected_v_var)}" na Amostra',
                text_auto=True,
                color_discrete_sequence=px.colors.qualitative.Plotly 
            )
            fig_v.update_layout(
                xaxis={'categoryorder':'total descending', 'title': vulnerability_vars.get(selected_v_var, selected_v_var)},
                yaxis={'title': 'Porcentagem (%)'},
                title_x=0.5,
                font=dict(size=12)
            )
            fig_v.update_traces(textposition='outside')
            st.plotly_chart(fig_v, use_container_width=True)
            st.caption("Gráfico de Barras Agrupadas: Compara a porcentagem de cada categoria de impacto *entre* os diferentes grupos demográficos.")

            # --- Gráfico de Barras Empilhadas ---
            st.subheader("Composição do Impacto Dentro de Cada Grupo Demográfico")
            df_stack = crosstab_v.reset_index().melt(
                id_vars=selected_v_var,
                var_name='Categoria de Impacto',
                value_name='Porcentagem'
            )

            fig_stack = px.bar(
                df_stack,
                y=selected_v_var, 
                x='Porcentagem',
                color='Categoria de Impacto',
                orientation='h',
                text='Porcentagem',
                title=f'Distribuição dos Impactos de "{impact_vars.get(selected_impact_var, selected_impact_var)}" Dentro de Cada Grupo de "{vulnerability_vars.get(selected_v_var, selected_v_var)}" na Amostra',
                labels={selected_v_var: "Grupo Demográfico", "Porcentagem": "Porcentagem (%)"},
                color_discrete_sequence=px.colors.qualitative.Plotly 
            )
            fig_stack.update_layout(
                barmode='stack', 
                height=max(400, 50 * len(df_stack[selected_v_var].unique())), 
                xaxis_title="Porcentagem (%)",
                yaxis_title="Grupo Demográfico",
                legend_title="Categoria de Impacto",
                margin=dict(l=120, r=30, t=50, b=40),
                title_x=0.5, 
                font=dict(size=12)
            )
            fig_stack.update_traces(texttemplate='%{text:.1f}%', textposition='inside') 

            st.plotly_chart(fig_stack, use_container_width=True)
            st.caption("Gráfico de Barras Empilhadas (100%): Mostra a composição do impacto (categorias) *dentro* de cada grupo demográfico. Cada barra representa 100% dos respondentes do grupo.")


            # --- Destaques por Categoria de Impacto (insights) ---
            st.markdown("---")
            st.subheader("🎯 Destaques de Vulnerabilidade por Categoria de Impacto")
            st.write("Identifique os grupos demográficos mais impactados em cada categoria de resposta da variável de impacto selecionada.")

            # Definir categorias não informativas a serem ignoradas
            non_informative_responses = ["Não informado", "N/A", "Não se aplica", "Não sabe", "Outros", ""] # Adicione mais se necessário

            # --- Filtra as colunas de impacto (respostas) que são informativas ---
            impact_response_columns_filtered = [
                col for col in crosstab_v.columns 
                if col in df_vulnerability_analysis[selected_impact_var].unique() and col not in non_informative_responses
            ]

            if len(impact_response_columns_filtered) > 0:
                cols_for_metrics = st.columns(min(len(impact_response_columns_filtered), 3)) 

                for i, impacto_col in enumerate(impact_response_columns_filtered):
                    # Filtra a crosstab_v para as linhas (grupos) que são informativas
                    crosstab_v_filtered_rows = crosstab_v[
                        ~crosstab_v.index.isin(non_informative_responses)
                    ]
                    
                    if not crosstab_v_filtered_rows.empty and impacto_col in crosstab_v_filtered_rows.columns:
                        max_group = crosstab_v_filtered_rows[impacto_col].idxmax()
                        max_value = crosstab_v_filtered_rows[impacto_col].max()
                        
                        # --- Lógica da COR DO DELTA (semântica da resposta) ---
                        delta_color_value = "normal" # Padrão: verde (indica que é "bom" ter alta porcentagem nessa resposta)
                        
                        # Verifica se a CATEGORIA DE RESPOSTA é de natureza "negativa"
                        # Este mapeamento ou lógica precisa ser o mais preciso possível para suas respostas.
                        # Ex: Para a variável 'Perda de Renda (Comprovada)', a resposta 'Sim' é bad.
                        #     Para a variável 'Perda de Renda (Comprovada)', a resposta 'Não' é good.
                        
                        # Obtém o mapeamento para a variável de impacto atual
                        impact_semantic_for_color = response_sentiment_map.get(selected_impact_var, {})
                        
                        # Verifica a semântica da resposta específica (impacto_col)
                        if impact_semantic_for_color.get(impacto_col) == 'bad':
                            delta_color_value = "inverse" # Vermelho: alta % nesta resposta é "ruim"
                        elif impact_semantic_for_color.get(impacto_col) == 'good':
                            delta_color_value = "normal" # Verde: alta % nesta resposta é "bom"
                        # Se não estiver mapeado ou for neutro, usa 'normal' (verde) por padrão ou 'off' (cinza)

                        with cols_for_metrics[i % 3]: 
                            st.metric(
                                label=f"Maior % em '{impacto_col}'", 
                                value=f"{max_group}", # O grupo que teve o maior percentual
                                delta=f"{max_value:.1f}%", # O percentual em si
                                delta_color=delta_color_value # A cor baseada na semântica da resposta
                            )
                            st.caption(f"Para a categoria de resposta '{impacto_col}', o grupo '{max_group}' teve o maior percentual ({max_value:.1f}%) na amostra.")
                    else:
                        with cols_for_metrics[i % 3]: 
                            st.info(f"Dados insuficientes ou não informativos para '{impacto_col}'.")
            else:
                st.info("Não foi possível identificar categorias de resposta válidas para a variável de impacto selecionada para os destaques.")

            # --- Botões de Download ---
            st.markdown("---")
            st.subheader("Opções de Download dos Dados Brutos")
            
            download_col1, download_col2 = st.columns(2)
            with download_col1:
                csv_crosstab = crosstab_v.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Baixar Tabela de Porcentagens (CSV)",
                    data=csv_crosstab,
                    file_name=f"{selected_v_var}_x_{selected_impact_var}_vulnerabilidade_porcentagens_amostra.csv",
                    mime="text/csv",
                    key="download_crosstab_csv",
                    help="Baixa a tabela de porcentagens de impacto por grupo demográfico."
                )
            with download_col2:
                excel_buffer_cross = io.BytesIO()
                crosstab_v.to_excel(excel_buffer_cross, engine='xlsxwriter')
                excel_buffer_cross.seek(0)
                st.download_button(
                    label="📥 Baixar Tabela de Porcentagens (Excel)",
                    data=excel_buffer_cross.getvalue(),
                    file_name=f"{selected_v_var}_x_{selected_impact_var}_vulnerabilidade_porcentagens_amostra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_crosstab_excel",
                    help="Baixa a tabela de porcentagens de impacto por grupo demográfico."
                )
            st.info("💡 Dica: Para baixar os gráficos, clique com o botão direito sobre eles e selecione 'Salvar imagem como...' ou 'Baixar imagem'.")

        else:
            st.warning("Não há dados válidos na amostra para as variáveis demográficas e de impacto selecionadas após remover valores em branco.")
    else:
        st.info("Por favor, selecione as variáveis demográficas e de impacto para visualizar a análise de vulnerabilidade.")
