import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go



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
        if selected_impact_var in df_sentiment_filtered_by_main.columns:
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
            crosstab_v = pd.crosstab(
                df_vulnerability_analysis[selected_v_var],
                df_vulnerability_analysis[selected_impact_var],
                normalize='index'
            ).mul(100).round(2)
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

            # Top 2 grupos para o impacto mais marcante (badge colorido acima do gráfico)


            # Transformar crosstab para formato 'long' para stacked bar
            df_stack = crosstab_v.reset_index().melt(
                id_vars=selected_v_var,
                var_name='Impacto',
                value_name='Porcentagem'
            )

            # Reordenar para visualização (opcional: ordene os grupos do maior total para o menor)
            group_totals = df_stack.groupby(selected_v_var)['Porcentagem'].sum().sort_values(ascending=False)
            group_order = group_totals.index.tolist()
            df_stack[selected_v_var] = pd.Categorical(df_stack[selected_v_var], categories=group_order, ordered=True)
            df_stack = df_stack.sort_values(selected_v_var)

            fig_stack = px.bar(
                df_stack,
                y=selected_v_var,
                x='Porcentagem',
                color='Impacto',
                orientation='h',
                text='Porcentagem',
                title=f'Distribuição dos Impactos por Grupo ({vulnerability_vars.get(selected_v_var, selected_v_var)})',
                labels={selected_v_var: "Grupo", "Porcentagem": "Porcentagem (%)"}
            )
            fig_stack.update_layout(
                barmode='stack',
                height=500 + 20*len(group_order),
                xaxis_title="Porcentagem (%)",
                yaxis_title="Grupo",
                legend_title="Categoria de Impacto",
                margin=dict(l=120, r=30, t=50, b=40),
            )
            fig_stack.update_traces(texttemplate='%{text:.1f}%', textposition='inside')

            st.plotly_chart(fig_stack, use_container_width=True)

            # Destaque opcional
            if st.checkbox("Mostrar destaque do maior impacto", key="checkbox_destaque"):
                st.markdown("### 🎯 <span style='color:#1f77b4'>Destaques por Categoria de Impacto</span>", unsafe_allow_html=True)
                for impacto in crosstab_v.columns:
                    max_group = crosstab_v[impacto].idxmax()
                    max_value = crosstab_v[impacto].max()
                    st.markdown(
                        f"""
                        <div style='background: #f6fafd; border-radius: 8px; padding: 8px 15px; margin-bottom: 10px; border-left: 6px solid #1f77b4'>
                            <span style='font-weight:bold; color:#1f77b4;'>Para {impacto}</span>:<br>
                            <span style='font-size:1.1em; font-weight: bold;'>{max_group}</span> 
                            <span style='font-size:1em; color:#333;'>foi o mais afetado</span>
                            <span style='font-weight:bold; color:#1f77b4;'>({max_value:.1f}%)</span>.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

