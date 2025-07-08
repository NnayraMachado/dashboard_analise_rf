import streamlit as st

st.header("Sobre o Dashboard")

st.markdown("""
## O que é este painel?

Este painel foi desenvolvido para facilitar a compreensão, análise e comunicação dos dados do **Registro Familiar (RF)**, coletados pela ADAI após o rompimento da Barragem de Fundão. Ele permite que gestores, pesquisadores e comunidades explorem informações de maneira interativa, transparente e acessível.

### Principais funcionalidades

- Visualização dinâmica de dados sociodemográficos, percepções e condições das famílias atingidas.
- Cruzamento automático de variáveis para identificar padrões e vulnerabilidades.
- Visualização espacial dos dados em mapas interativos por município.
- Análises comparativas (antes vs. depois) para detectar mudanças importantes.
- Download fácil das tabelas em formatos CSV e Excel.
- Interpretação automatizada dos dados com IA Gemini (Google).

---

### Metadados dos dados

- **Fonte:** Registro Familiar (RF) – ADAI, com apoio nos territórios assessorados do Espírito Santo.
- **População-alvo:** Famílias atingidas pelo desastre em [municípios], com amostragem representativa.
- **Período de coleta:** Setembro a outubro de 2023.
- **Número de respondentes:** 624 núcleos familiares (1.794 pessoas).
- **Principais campos:** Identificação, dados sociodemográficos, saúde, trabalho, acesso a programas sociais, percepções, sentimentos e impactos do desastre.

---

### Métodos estatísticos e matemáticos aplicados

- Estatística descritiva: frequências, médias, desvios-padrão, etc.
- Tabelas de contingência: cruzamento automático de variáveis categóricas.
- Comparação de grupos: filtros por território, idade, raça/cor, gênero, etc.
- Visualização: gráficos de barras, pizza, histogramas, mapas de calor, mapas interativos.
- Análise automatizada de texto: classificação de sentimentos, emoções e resumo de respostas abertas usando IA.

---

### Limitações e recomendações

- Os resultados apresentados são descritivos/exploratórios — recomenda-se análise detalhada por especialistas para decisões finais.
- Não há ponderação amostral automática (salvo ajuste manual).
- Respostas abertas são analisadas por algoritmos de IA; recomenda-se revisão humana em temas sensíveis.
- O painel depende da qualidade e completude dos dados recebidos.

> **Dica:** Para saber como funciona a IA do painel e seus limites, acesse “Sobre a IA” no menu lateral.
""")
