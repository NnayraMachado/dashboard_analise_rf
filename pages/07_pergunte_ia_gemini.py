import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()
    
df = st.session_state['df']
st.header("💬 Pergunte à IA (Gemini)")

st.markdown("---")

# Configure API Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- MAPA DE SINÔNIMOS/COLUNAS PARA BUSCA AUTOMÁTICA ---
mapa_colunas = {
    "ID7": ["raça", "cor", "negro", "pardo", "branco", "indígena"],
    "ADAI_ID8": ["gênero", "sexo", "homem", "mulher", "masculino", "feminino"],
    "ADAI_CT4": ["território", "localidade", "município", "colatina", "baixo guandu"],
    "ID10": ["deficiência", "pcd"],
    "PCT0": ["povo tradicional", "comunidade tradicional", "quilombola", "povo", "indígena"],
    "Idade": ["idade", "faixa etária", "jovem", "idoso", "criança"],
    "ID11": ["escolaridade", "formação"],
    "ADAI_ID12": ["profissão", "trabalho", "ocupação"],
    "ID12": ["religião", "prática religiosa"],
    # Acrescente outros campos do seu interesse
}

# Funções auxiliares do seu painel:
def extrair_filtros(pergunta, mapa):
    """Procura sinônimos na pergunta e mapeia para colunas"""
    filtros = {}
    for campo, palavras in mapa.items():
        for palavra in palavras:
            if re.search(rf'\b{palavra}\b', pergunta, re.IGNORECASE):
                filtros[campo] = palavra
                break
    return filtros

def aplicar_filtros(df, filtros):
    """Aplica os filtros no DataFrame"""
    df_filtrado = df.copy()
    for coluna, valor in filtros.items():
        # Tratamento especial para colunas numéricas
        if pd.api.types.is_numeric_dtype(df_filtrado[coluna]):
            m = re.search(r'(maior|acima|mais de) (\d+)', valor)
            if m:
                df_filtrado = df_filtrado[df_filtrado[coluna] > int(m.group(2))]
            else:
                m = re.search(r'(menor|abaixo|menos de) (\d+)', valor)
                if m:
                    df_filtrado = df_filtrado[df_filtrado[coluna] < int(m.group(2))]
        else:
            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).str.contains(valor, case=False, na=False)]
    return df_filtrado

def explicar_para_ia(pergunta, resultado):
    """Chama a IA Gemini para explicar, usando apenas o resultado filtrado"""
    contexto_metodologico = """
NOTA METODOLÓGICA:
Este dashboard utiliza dados primários e secundários coletados pela ADAI nos territórios 9, 10, 13, 14, 15 e 16 do Espírito Santo, referentes ao impacto do rompimento da barragem de Fundão (Samarco, Vale, BHP Billiton). Foram entrevistadas 624 famílias (1.794 pessoas) em setembro/outubro de 2023, usando questionário estruturado, a partir de amostragem representativa e snowball. Os resultados devem ser interpretados no contexto da pesquisa social, considerando limitações próprias do método e em fase contínua de atualização e análise.
"""
    # Limita a amostra para IA não travar, mas ainda representativa
    if len(resultado) > 80:
        sample_df = resultado.sample(80, random_state=42)
    else:
        sample_df = resultado
    prompt = (
    f"{contexto_metodologico}\n\n"
    f"Pergunta do usuário: \"{pergunta}\"\n"
    f"Resultado filtrado (colunas e até 80 linhas):\n{sample_df.to_string(index=False)}\n\n"
    f"Explique para um público leigo o que esse resultado representa, **sempre considerando a nota metodológica acima**. Destaque padrões, diferenças ou curiosidades, mas NÃO invente nenhum valor que não esteja nos dados apresentados. NÃO faça generalizações fora do contexto do desastre da barragem de Fundão/ADAI."
    )
    model = genai.GenerativeModel('gemini-1.5-flash')
    resposta = model.generate_content(prompt)
    return resposta.text

# Inicializa o histórico de chat
if "chat_history_gemini" not in st.session_state:
    st.session_state.chat_history_gemini = []

MAX_INPUT_CHARS = 400  # limite de caracteres para o input do usuário

# Renderiza o histórico (perguntas e respostas)
for item in st.session_state.chat_history_gemini:
    with st.chat_message("user"):
        st.markdown(item["pergunta"])
    with st.chat_message("assistant"):
        st.markdown(item["resposta"])
        if "tabela" in item and item["tabela"] is not None:
            st.dataframe(item["tabela"])
        if "grafico" in item and item["grafico"] is not None:
            st.plotly_chart(item["grafico"], use_container_width=True)

# Orientações para o usuário (insira aqui)
st.subheader("📝 Orientações para Perguntar à IA Gemini")

st.info("""
**Como fazer perguntas para a IA?**

- Escreva dúvidas ou pedidos de informação de forma clara e objetiva.
- Exemplos:
    - _"Quantas mulheres negras moram em Colatina?"_
    - _"Qual a distribuição de idade entre os quilombolas?"_
    - _"Quantos respondentes se declararam indígenas em Baixo Guandu?"_
    - _"Como está a escolaridade dos moradores do território 14?"_

**Dicas importantes:**
- Utilize palavras-chave como: gênero, idade, raça/cor, município, escolaridade, trabalho, religião, etc.
- Seja específico sobre quem ou o quê você quer saber (ex: “em Baixo Guandu”, “entre os jovens”, “famílias chefiadas por mulheres”).
- Combine critérios, se desejar, mas evite perguntas muito amplas ou vagas.
- Limite-se a perguntas simples, de preferência com até dois filtros por vez, para melhores resultados.
- Caso a resposta pareça estranha, incompleta ou confusa, tente reformular sua pergunta de forma mais direta.

---

:warning: **Atenção!**
Esta função de perguntas automáticas para a IA **ainda está em desenvolvimento** e pode apresentar limitações, respostas incompletas ou erros de interpretação.  
**Recomenda-se sempre revisar as respostas da IA** e, em caso de dúvida, consultar a equipe técnica ou especialistas do projeto antes de tomar decisões com base nessas respostas.
""")

# Entrada do chat
user_input = st.chat_input("Digite sua pergunta para a IA...", max_chars=MAX_INPUT_CHARS, key="input_gemini")
if user_input:
    with st.spinner("Buscando resposta..."):
        filtros = extrair_filtros(user_input, mapa_colunas)
        if not filtros:
            resposta = "❗ Não consegui identificar filtros na pergunta. Tente usar termos como 'mulher', 'negro', 'Colatina', 'idade', etc."
            tabela = None
            grafico = None
        else:
            resultado = aplicar_filtros(df, filtros)
            resposta = f"Total de registros encontrados: **{len(resultado)}**"
            tabela = resultado if len(resultado) > 0 else None

            # Exemplo de gráfico automático (pode adaptar para outros tipos!)
            if len(filtros) == 1:  # só um filtro: exibe distribuição por gênero, raça ou município se possível
                coluna = list(filtros.keys())[0]
                if coluna in resultado.columns and resultado[coluna].nunique() < 10:
                    grafico = px.histogram(resultado, x=coluna, title=f"Distribuição de {coluna}", text_auto=True)
                else:
                    grafico = None
            else:
                grafico = None

            # IA só chama se houver registros
            if len(resultado) > 0:
                with st.spinner("IA explicando o resultado..."):
                    explicacao = explicar_para_ia(user_input, resultado)
                    resposta += "\n\n#### 🧠 Explicação da IA:\n" + explicacao
            else:
                resposta += "\n\nNenhum registro encontrado para os filtros aplicados."
        
        # Salva no histórico
        st.session_state.chat_history_gemini.append({
            "pergunta": user_input,
            "resposta": resposta,
            "tabela": tabela,
            "grafico": grafico
        })
        st.rerun()
