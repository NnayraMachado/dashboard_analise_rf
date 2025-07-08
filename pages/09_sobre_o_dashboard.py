import streamlit as st

st.header("Sobre o Dashboard")

st.markdown("""
Este painel foi desenvolvido para facilitar a compreensão, análise e comunicação dos dados do **Registro Familiar (RF)**, coletados pela ADAI após o rompimento da Barragem de Fundão.
""")

st.markdown("---")

st.markdown("### 🚀 Principais funcionalidades")
st.markdown("""
- 📊 Visualização dinâmica de dados sociodemográficos
- 🔍 Cruzamento automático de variáveis
- 🗺️ Mapas interativos por município
- 🆚 Análises comparativas (antes vs. depois)
- 📥 Download em CSV/Excel
- 🤖 Interpretação automatizada dos dados com IA Gemini
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Metadados dos dados")
    st.markdown("""
    - **Fonte:** Registro Familiar (RF) – ADAI
    - **População-alvo:** Famílias atingidas
    - **Período de coleta:** Set-Out/2023
    - **Respondentes:** 624 núcleos (1.794 pessoas)
    - **Campos:** Identificação, sociodemográficos, saúde, trabalho, programas sociais, percepções
    """)

with col2:
    st.subheader("Métodos Estatísticos")
    st.markdown("""
    - Estatística descritiva
    - Tabelas de contingência
    - Comparação de grupos
    - Gráficos e mapas interativos
    - Análise automatizada de texto com IA
    """)

st.divider()

st.warning("""
**Limitações e recomendações**
- Resultados descritivos/exploratórios — análise detalhada recomendada.
- Não há ponderação amostral automática.
- Respostas abertas analisadas por IA; recomenda-se revisão humana.
- O painel depende da qualidade dos dados recebidos.
""")

st.info("> **Dica:** Para saber como funciona a IA do painel, acesse “Sobre a IA” no menu lateral.")

