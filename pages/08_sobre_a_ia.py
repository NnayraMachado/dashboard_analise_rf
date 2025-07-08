import streamlit as st

st.header("🤖 Sobre a Inteligência Artificial do Painel")

st.markdown("""
Este painel utiliza **Inteligência Artificial (IA)** para apoiar a análise, interpretação e comunicação dos dados de duas formas principais:
""")

st.markdown("---")

# 1. Principais formas de uso da IA
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Interpretação de Dados Estruturados")
    st.markdown("""
    - IA Gemini (Google) interpreta tabelas de dados quantitativos e categóricos.
    - Explica resultados (ex: _"Quantas mulheres negras há em Colatina?"_), **sempre considerando o contexto metodológico**.
    - Destaca padrões, curiosidades, limitações e fornece explicações acessíveis.
    - Contexto metodológico e limitações sempre considerados nas respostas.
    """)

with col2:
    st.subheader("2️⃣ Análise de Respostas Abertas")
    st.markdown("""
    - Processamento automatizado de respostas de texto livre.
    - IA identifica **sentimentos gerais, emoções e trechos-chave**.
    - Classifica sentimentos: “Muito Negativo”, “Negativo”, “Neutro”, “Positivo”, “Muito Positivo”.
    - Destaca exemplos de opiniões e sentimentos dos participantes.
    """)

st.markdown("---")

st.subheader("⚙️ Como funciona a IA aqui?")
st.markdown("""
- Utiliza modelos avançados (Gemini, Google Generative AI) para interpretação e resumo dos dados.
- Cada consulta inclui o contexto metodológico do levantamento e parâmetros relevantes.
- **Nenhum dado pessoal identificável é exibido ou utilizado para treinamento posterior.**
""")

st.info("🔎 **Dica:** O prompt enviado à IA inclui o resumo metodológico, detalhes da amostra e contexto do desastre.")

st.markdown("---")

st.warning("""
**Limitações e Boas Práticas**
- IA é uma ferramenta auxiliar — revise sempre em temas sensíveis, polêmicos ou jurídicos.
- Em caso de dúvidas ou dados ambíguos, priorize avaliação por especialistas humanos.
- Qualidade das análises depende da clareza e representatividade dos dados.
- As respostas da IA **não substituem análises estatísticas aprofundadas** ou revisão por pesquisadores.
""")

st.markdown("---")

st.info("💬 Para dúvidas ou sugestões sobre a IA do painel, entre em contato com a equipe técnica responsável pelo projeto.")

