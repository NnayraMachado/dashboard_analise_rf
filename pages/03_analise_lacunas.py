import streamlit as st
import pandas as pd
import plotly.express as px

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()
    
df = st.session_state['df']
question_labels = st.session_state['question_labels']

st.header("Análise de Lacunas: Antes vs. Depois do Rompimento")

st.markdown("Compare a situação dos respondentes antes e depois do rompimento da barragem em áreas chave para identificar as principais lacunas e impactos.")

gap_analysis_pairs = {
    "Acesso a Programas Sociais (ID13/ID14)": ('ID13', 'ID14'),
    "Acesso à Água do Rio Doce (AQA1/AQA2)": ('AQA1', 'AQA2'),
    "Exercia Atividade Remunerada (AER1/ARF1.1)": ('AER1', 'ARF1.1'), 
}
available_gap_pairs = {k: v for k, v in gap_analysis_pairs.items() if v[0] in df.columns and v[1] in df.columns}

if not available_gap_pairs:
    st.warning("Nenhum par de perguntas 'Antes/Depois' encontrado para análise de lacunas.")
else:
    selected_gap_pair_label = st.selectbox(
        "Selecione a Dimensão para Análise de Lacunas:",
        list(available_gap_pairs.keys()),
        key="gap_pair_selector"
    )

    if selected_gap_pair_label:
        col_antes, col_depois = available_gap_pairs[selected_gap_pair_label]

        st.subheader(f"Comparativo: {question_labels.get(col_antes, col_antes)} vs. {question_labels.get(col_depois, col_depois)}")
        df_gap = df[[col_antes, col_depois]].dropna()

        if not df_gap.empty:
            counts_antes = df_gap[col_antes].value_counts(normalize=True).mul(100).round(2).reset_index()
            counts_antes.columns = ['Resposta', 'Porcentagem (%)']
            counts_antes['Período'] = 'Antes do Rompimento'

            counts_depois = df_gap[col_depois].value_counts(normalize=True).mul(100).round(2).reset_index()
            counts_depois.columns = ['Resposta', 'Porcentagem (%)']
            counts_depois['Período'] = 'Depois do Rompimento'

            combined_counts = pd.concat([counts_antes, counts_depois])

            fig_gap = px.bar(
                combined_counts,
                x='Resposta',
                y='Porcentagem (%)',
                color='Período',
                barmode='group',
                title=f'Comparativo de "{selected_gap_pair_label}" Antes e Depois do Rompimento',
                text_auto=True
            )
            fig_gap.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_gap, use_container_width=True)

            st.markdown("#### Tabela Comparativa (Porcentagens)")
            crosstab_gap = pd.crosstab(df_gap[col_antes], df_gap[col_depois], normalize='index').mul(100).round(2)
            st.dataframe(crosstab_gap, use_container_width=True)
            st.info("A tabela acima mostra a porcentagem de respondentes de uma categoria 'Antes' que caíram em cada categoria 'Depois'.")

            kpi_text = ""
            if 'Sim' in counts_antes['Resposta'].values and 'Sim' in counts_depois['Resposta'].values:
                perc_antes_sim = counts_antes[counts_antes['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
                perc_depois_sim = counts_depois[counts_depois['Resposta'] == 'Sim']['Porcentagem (%)'].iloc[0]
                kpi_text = (
                    f"**KPI:** A porcentagem de respondentes que afirmam '{selected_gap_pair_label}' (resposta 'Sim') mudou de **{perc_antes_sim:.1f}%** antes para **{perc_depois_sim:.1f}%** depois do rompimento. "
                    f"Isso representa uma **mudança de {perc_depois_sim - perc_antes_sim:.1f} pontos percentuais**."
                )
                st.markdown(kpi_text)

            # --- IA: Resumo Automático
            st.markdown("---")
