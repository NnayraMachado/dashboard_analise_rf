import streamlit as st
import pandas as pd
import plotly.express as px

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()

    
df = st.session_state['df']
df_sentiment_filtered_by_main = st.session_state['df_sentiment_filtered_by_main']

st.header("Análise de Vulnerabilidade")

st.markdown("Explore como diferentes grupos demográficos foram impactados ou percebem a situação, identificando potenciais vulnerabilidades.")

vulnerability_vars = {
    'ID7': 'Raça/Cor',
    'ADAI_ID8': 'Gênero',
    'ID10': 'Pessoa com Deficiência',
    'PCT0': 'Povo/Comunidade Tradicional',
}

impact_vars = {
    # 'PCT5.1_Sentimento_Geral': 'Perdas/Modos de Vida (Sentimento Geral)',
    # 'PCT5.1_Sentimento_Emocao': 'Perdas/Modos de Vida (Emoção)',
    # 'PC1.1.8.1_Sentimento_Satisfacao': 'Sugestões Reparação (Satisfação)',
    # 'ADAI_PC2_Sentimento_Geral': 'Avaliação Participação (Sentimento Geral)',
    'ARF3.1': 'Perda de Renda (Comprovada)', 
    'DF1': 'Dívida Contraída/Aumentada',
    'SA1': 'Comprometimento Qualidade Alimentos',
    'CCS7': 'Aumento Gastos Saúde',
}
    
available_impact_vars = {k: v for k, v in impact_vars.items() if k in df.columns or k in df_sentiment_filtered_by_main.columns}

if not available_impact_vars:
    st.warning("Nenhuma variável de impacto encontrada para análise de vulnerabilidade.")
else:
    selected_v_var = st.selectbox(
        "Selecione a Variável Demográfica/Vulnerabilidade:",
        list(vulnerability_vars.keys()),
        format_func=lambda x: vulnerability_vars[x],
        key="v_var_selector"
    )

    selected_impact_var = st.selectbox(
        "Selecione a Variável de Impacto:",
        list(available_impact_vars.keys()),
        format_func=lambda x: available_impact_vars[x],
        key="impact_var_selector"
    )

    if selected_v_var and selected_impact_var:
        st.subheader(f"Impacto de '{vulnerability_vars.get(selected_v_var, selected_v_var)}' na '{impact_vars.get(selected_impact_var, selected_impact_var)}'")

        # Lógica de cruzamento (robusta)
        if selected_impact_var in df_sentiment_filtered_by_main.columns:  # Se a variável de impacto é de sentimento
            if selected_v_var in df.columns and 'ID' in df.columns and 'ID' in df_sentiment_filtered_by_main.columns:
                df_vulnerability_analysis = df_sentiment_filtered_by_main[[selected_impact_var, 'ID']].merge(
                    df[[selected_v_var, 'ID']], on='ID', how='inner'
                ).dropna()
            else:
                st.warning("Não foi possível cruzar a variável de sentimento com a demográfica. IDs ausentes ou variáveis não encontradas.")
                df_vulnerability_analysis = pd.DataFrame()
        elif selected_impact_var in df.columns:
            df_vulnerability_analysis = df[[selected_v_var, selected_impact_var]].dropna()
        else:
            st.warning("Variável de impacto não encontrada em nenhum dos DataFrames carregados.")
            df_vulnerability_analysis = pd.DataFrame()
        
        if not df_vulnerability_analysis.empty:
            crosstab_v = pd.crosstab(df_vulnerability_analysis[selected_v_var], df_vulnerability_analysis[selected_impact_var], normalize='index').mul(100).round(2)
            st.dataframe(crosstab_v, use_container_width=True)

            fig_v = px.bar(
                crosstab_v.reset_index().melt(id_vars=selected_v_var, var_name='Impacto', value_name='Porcentagem (%)'),
                x=selected_v_var,
                y='Porcentagem (%)',
                color='Impacto',
                barmode='group',
                title=f'Porcentagem de Respostas para "{impact_vars.get(selected_impact_var, selected_impact_var)}" por "{vulnerability_vars.get(selected_v_var, selected_v_var)}"',
                text_auto=True
            )
            fig_v.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_v, use_container_width=True)

            # --- Insights automáticos simples
            st.markdown("#### Insights de Vulnerabilidade (Exemplo):")
            if selected_v_var == 'ID7' and selected_impact_var == 'PCT5.1_Sentimento_Geral':
                if 'Muito Negativo' in crosstab_v.columns:
                    st.markdown(f"**Dados Concretos:** A análise mostra que entre os grupos raciais, **{crosstab_v['Muito Negativo'].idxmax()}** teve a maior porcentagem de sentimento 'Muito Negativo' sobre perdas e modos de vida, com **{crosstab_v['Muito Negativo'].max():.1f}%** dos respondentes desse grupo expressando esse sentimento. Em contraste, **{crosstab_v['Muito Negativo'].idxmin()}** teve a menor porcentagem, com **{crosstab_v['Muito Negativo'].min():.1f}%**.")

            if selected_v_var == 'ID10' and selected_impact_var == 'DF1':
                if 'Sim' in crosstab_v.columns:
                    pcd_sim_divida = crosstab_v.loc['Sim', 'Sim'] if 'Sim' in crosstab_v.index and 'Sim' in crosstab_v.columns else 0
                    nao_pcd_sim_divida = crosstab_v.loc['Não', 'Sim'] if 'Não' in crosstab_v.index and 'Sim' in crosstab_v.columns else 0
                    st.markdown(f"**Dados Concretos:** Entre os respondentes, **{pcd_sim_divida:.1f}%** das pessoas com deficiência reportaram ter contraído ou aumentado dívidas, enquanto para pessoas sem deficiência, essa porcentagem foi de **{nao_pcd_sim_divida:.1f}%**. Isso sugere uma potencial vulnerabilidade maior para pessoas com deficiência em relação ao endividamento.")

            st.markdown("---")
        else:
            st.warning("Não há dados válidos para esta combinação de variáveis com os filtros atuais.")
    else:
        st.info("Por favor, selecione as variáveis para a análise de vulnerabilidade.")
