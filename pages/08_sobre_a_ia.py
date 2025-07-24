import streamlit as st

st.header("Sobre a Inteligência Artificial do Painel")

st.markdown("""
Este painel utiliza **Inteligência Artificial** para ampliar a análise, interpretação e comunicação dos dados — tornando o acesso à informação mais ágil, inclusivo e seguro.
""")

st.divider()

tab1, tab2 = st.tabs(["Análise de Dados Estruturados", "Análise de Textos Abertos"])

with tab1:
    st.subheader("Como funciona?")
    st.markdown("""
- A IA (Gemini, Google) interpreta tabelas e variáveis quantitativas/categóricas do questionário.
- Explica resultados como:  
  > *“Quantas mulheres negras há em Colatina?”*
- Traduz padrões, tendências e limitações em linguagem acessível.
- Sempre contextualiza com as premissas metodológicas da pesquisa.
    """)
    st.info("Ajuda a identificar padrões, vulnerabilidades, relações entre variáveis e pontos de atenção nos dados.")

with tab2:
    st.subheader("Como funciona?")
    st.markdown("""
- Leitura automatizada de respostas livres (opiniões e relatos).
- Identifica emoções, sentimentos predominantes e temas recorrentes.
- Classifica opiniões (de “Muito Negativo” a “Muito Positivo”).
- Destaca frases-chave e depoimentos ilustrativos.
    """)
    st.info("Oferece panorama do sentimento coletivo e evidencia nuances das experiências relatadas.")

st.divider()

st.subheader("Princípios de Uso e Privacidade")
st.markdown("""
- Os resultados são sempre apresentados com referência ao contexto metodológico.
- **Privacidade:** Nenhum dado pessoal identificável é exibido ou usado para treinar a IA.
- O processamento visa contextualizar os números com impacto humano – cada estatística representa vidas, histórias e desafios reais.
""")

st.divider()

st.subheader("Limitações e Recomendações")
st.warning("""
- A IA é um apoio à análise – recomenda-se revisão crítica, principalmente em temas sensíveis.
- Em caso de dúvidas, ambiguidades ou ausência de dados, consulte a equipe de pesquisa.
- As conclusões referem-se à amostra pesquisada; evite generalizações absolutas.
- Não substitui análises estatísticas avançadas ou validação por especialistas humanos.
""")

st.divider()

st.markdown("""
**Exemplos de perguntas para a IA:**
- “Qual a faixa etária predominante nos territórios pesquisados?”
- “O que dizem os relatos sobre saúde mental após o desastre?”
- “Como a escolaridade se relaciona com o gênero?”
""")

st.info("Dúvidas ou sugestões sobre a IA? Entre em contato com a equipe técnica responsável pelo projeto.")
