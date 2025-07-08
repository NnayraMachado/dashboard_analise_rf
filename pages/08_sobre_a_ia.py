import streamlit as st

st.header("Sobre a Inteligência Artificial do Painel")

st.markdown("""
Este painel utiliza **Inteligência Artificial (IA)** para apoiar a análise, a interpretação e a comunicação dos dados de duas formas principais:

### 1. Interpretação de Dados Estruturados via IA Gemini
- A IA Gemini, da Google, interpreta tabelas de dados quantitativos e categóricos filtrados pelo usuário.
- Ao fazer perguntas (por exemplo, "Quantas mulheres negras há em Colatina?"), a IA explica os resultados encontrados pelo Pandas, **sempre considerando o contexto metodológico da pesquisa**.
- A IA destaca padrões, curiosidades, possíveis limitações e fornece explicações acessíveis para públicos não especialistas.
- O contexto metodológico e as limitações do estudo são levados em conta nas respostas.

### 2. Análise Automatizada de Respostas Abertas (Sentimentos, Emoções e Justificativas)
- As respostas de texto livre dos questionários passam por um processamento automatizado com IA, que identifica **sentimentos gerais, emoções e trechos-chave**.
- O modelo classifica sentimentos em categorias como “Muito Negativo”, “Negativo”, “Neutro”, “Positivo” e “Muito Positivo”, além de mapear emoções predominantes.
- Trechos exemplares das respostas podem ser destacados para ilustrar sentimentos e opiniões dos participantes.

### Como funciona a IA aqui?
- O painel utiliza modelos avançados de linguagem natural (Gemini, Google Generative AI), treinados para interpretação de dados e sumarização de informações.
- O prompt enviado à IA inclui, além da tabela de dados, um resumo metodológico do contexto do levantamento (registro do rompimento da Barragem de Fundão, detalhes amostrais, municípios, período, etc.).
- Nenhum dado pessoal identificável é exibido ou utilizado para treinamento posterior.

### Limitações e Boas Práticas
- A IA é uma **ferramenta auxiliar**: sempre revise as interpretações, especialmente em temas sensíveis, polêmicos ou juridicamente relevantes.
- Em caso de dúvidas ou dados ambíguos, priorize a avaliação por especialistas humanos.
- A qualidade das análises depende da clareza, abrangência e representatividade dos dados coletados.
- As respostas da IA não substituem análises estatísticas aprofundadas ou revisão por pesquisadores.

---

**Para sugestões ou dúvidas sobre a IA do painel, consulte a equipe técnica responsável pelo projeto.**
""")
