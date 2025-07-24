import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re
import numpy as np
import unidecode

# --- EXEMPLO de DataFrame (substitua pelo seu carregamento real) ---
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame({
        "ID7": ["NEGRA", "BRANCO", "PARDA", "PARDA", "BRANCO", "NEGRA"],
        "ADAI_ID8": ["MULHER", "HOMEM", "MULHER", "MULHER", "HOMEM", "MULHER"],
        "Idade": [35, 42, 20, 64, 28, 50],
        "ADAI_CT4": ["COLATINA", "BAIXO GUANDU", "COLATINA", "LINHARES", "COLATINA", "BAIXO GUANDU"]
    })
df = st.session_state['df']

# --- ESTILO Gemini (apenas CSS, sem JS) ---
st.markdown("""
    <style>
    .gemini-actions-row {
        display: flex; gap: 10px; align-items: center; margin-top: 8px; margin-bottom: 4px;
    }
    .gemini-quick-row {
        display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;
    }
    .gemini-quick-btn {
        background: #f0f2f5; border: none; border-radius: 22px;
        padding: 4px 16px; font-size: 1em; color: #4a6572;
        cursor: pointer; transition: background 0.2s;
    }
    .gemini-quick-btn:hover { background: #e0e2e5;}
    .gemini-actions-btn {
        background: #fff;
        border: 1px solid #dedede;
        color: #264653;
        border-radius: 20px;
        font-size: 1em;
        padding: 5px 15px;
        margin-right: 2px;
        transition: background 0.18s, border 0.18s;
        cursor: pointer;
    }
    .gemini-actions-btn:hover { background: #e7ebf3; border: 1px solid #b2bec3;}
    </style>
""", unsafe_allow_html=True)

st.header("💬 Pergunte à IA (Gemini)")
st.markdown("---")

# ---- GEMINI API CONFIG ----
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# --- MAP OF SYNONYMS/COLUMNS AND THEIR CATEGORIES FOR AUTO-SEARCH ---
mapa_colunas = {
    "ID7": {
        "sinonimos_coluna": ["raça", "cor", "etnia"],
        "categorias": {
            "negra": ["Preta", "Negra", "AFRODESCENDENTE"], 
            "preta": ["Preta", "Negra", "AFRODESCENDENTE"],
            "parda": ["Parda", "Morena"], 
            "morena": ["Parda", "Morena"],
            "branco": ["Branca", "Branco"],
            "indígena": ["Indígena", "Povo Indígena"],
            "amarela": ["Amarela", "Asiática"],
            "nao declarado": ["Não Declarado", "Ignorado", "Outros", "NAO DECLARADO", "N/A", "NULL", "nan"],
            "outros": ["Outros"]
        },
        "tipo": "categorica"
    },
    "ADAI_ID8": {
        "sinonimos_coluna": ["gênero", "sexo"],
        "categorias": {
            "homem": ["Homem", "Masculino"],
            "mulher": ["Mulher", "Feminino"],
            "nao binario": ["Não binário", "Outros"],
            "outros": ["Não binário", "Outros", "Prefiro não dizer", "Não declarado", "NAO DECLARADO", "N/A", "NULL", "nan"]
        },
        "tipo": "categorica"
    },
    "ADAI_CT4": {
        "sinonimos_coluna": ["território", "localidade", "município", "cidade", "onde"],
        "categorias": { 
            "colatina": ["COLATINA"], 
            "baixo guandu": ["BAIXO GUANDU"],
            "linhares": ["LINHARES"],
            "sao mateus": ["SÃO MATEUS"],
            "conceicao da barra": ["CONCEIÇÃO DA BARRA"],
            "regencia": ["REGÊNCIA"],
            "povoacao": ["POVOAÇÃO"],
            "nao informado": ["Não Informado", "NAO INFORMADO", "N/A", "NULL", "nan"]
        },
        "tipo": "categorica"
    },
    "ID10": {
        "sinonimos_coluna": ["deficiência", "pcd", "pessoa com deficiência"],
        "categorias": {
            "sim": ["Sim", "SIM"],
            "nao": ["Não", "NÃO"],
            "nao declarado": ["Não declarado", "NAO DECLARADO", "N/A", "NULL", "nan"]
        },
        "tipo": "categorica"
    },
    "PCT0": {
        "sinonimos_coluna": ["povo tradicional", "comunidade tradicional", "quilombola", "povo", "indigena"],
        "categorias": {
            "sim": ["Sim", "SIM"],
            "nao": ["Não", "NÃO"],
            "nao declarado": ["Não declarado", "NAO DECLARADO", "N/A", "NULL", "nan"]
        },
        "tipo": "categorica"
    },
    "Idade": { 
        "sinonimos_coluna": ["idade", "faixa etária", "jovem", "idoso", "criança", "idade dos respondentes"],
        "tipo": "numerica"
    },
    "ID11": {
        "sinonimos_coluna": ["escolaridade", "formação educacional", "nivel de ensino"],
        "categorias": { 
            "fundamental": ["ENSINO FUNDAMENTAL INCOMPLETO", "ENSINO FUNDAMENTAL COMPLETO"],
            "medio": ["ENSINO MÉDIO INCOMPLETO", "ENSINO MÉDIO COMPLETO"],
            "superior": ["ENSINO SUPERIOR INCOMPLETO", "ENSINO SUPERIOR COMPLETO", "PÓS-GRADUAÇÃO"],
            "analfabeto": ["ANALFABETO"],
            "nao declarado": ["Não declarado", "NAO DECLARADO", "N/A", "NULL", "nan"],
        },
        "tipo": "categorica"
    },
    "ADAI_ID12": { 
        "sinonimos_coluna": ["profissão", "trabalho", "ocupação"],
        "tipo": "categorica" 
    },
    "ID12": { 
        "sinonimos_coluna": ["religião", "prática religiosa", "crença"],
        "tipo": "categorica"
    },
}

def preprocess_dataframe(df_input):
    df_processed = df_input.copy()
    for col_name, info in mapa_colunas.items():
        if col_name in df_processed.columns:
            if info["tipo"] == "categorica" or info["tipo"] == "texto_aberto":
                df_processed[col_name] = df_processed[col_name].astype(str).str.strip().str.upper()
                df_processed[col_name] = df_processed[col_name].replace(['NAN', 'N/A', 'NULL', ''], 'NÃO DECLARADO')
            elif info["tipo"] == "numerica":
                df_processed[col_name] = pd.to_numeric(df_processed[col_name], errors='coerce')
    return df_processed

df = preprocess_dataframe(df)


def extrair_filtros_e_variaveis(pergunta, mapa_colunas):
    filtros = {}
    variaveis_interesse = []
    
    pergunta_normalizada = unidecode.unidecode(pergunta).lower()

    for coluna_df, info_coluna in mapa_colunas.items():
        for sinonimo_coluna in info_coluna["sinonimos_coluna"]:
            if re.search(rf'\b{unidecode.unidecode(sinonimo_coluna).lower()}\b', pergunta_normalizada) and \
               ("qual a" in pergunta_normalizada or "mostre" in pergunta_normalizada or "distribuicao" in pergunta_normalizada or "analise" in pergunta_normalizada or "como esta" in pergunta_normalizada or "quais os" in pergunta_normalizada or "lista de" in pergunta_normalizada):
                if coluna_df not in variaveis_interesse:
                    variaveis_interesse.append(coluna_df)
                
        if info_coluna["tipo"] == "categorica" and "categorias" in info_coluna:
            for termo_pergunta, valores_df in info_coluna["categorias"].items():
                if re.search(rf'\b{unidecode.unidecode(termo_pergunta).lower()}\b', pergunta_normalizada):
                    if coluna_df not in filtros:
                        filtros[coluna_df] = []
                    filtros[coluna_df].extend(valores_df)
                    filtros[coluna_df] = list(set(filtros[coluna_df]))
                    
                    if coluna_df not in variaveis_interesse:
                        variaveis_interesse.append(coluna_df)

        if info_coluna["tipo"] == "numerica":
            m = re.search(r'(?:maior|acima|mais de|superior a|maiores de|superiores a)\s*(\d+)', pergunta_normalizada)
            if m:
                filtros[coluna_df] = {'operador': '>', 'valor': int(m.group(1))}
                if coluna_df not in variaveis_interesse: variaveis_interesse.append(coluna_df)
            else:
                m = re.search(r'(?:menor|abaixo|menos de|inferior a|menores de|inferiores a)\s*(\d+)', pergunta_normalizada)
                if m:
                    filtros[coluna_df] = {'operador': '<', 'valor': int(m.group(1))}
                    if coluna_df not in variaveis_interesse: variaveis_interesse.append(coluna_df)
                else:
                    m = re.search(r'entre\s*(\d+)\s*e\s*(\d+)', pergunta_normalizada)
                    if m:
                        filtros[coluna_df] = {'operador': 'between', 'min': int(m.group(1)), 'max': int(m.group(2))}
                        if coluna_df not in variaveis_interesse: variaveis_interesse.append(coluna_df)
    
    if ("quantos" in pergunta_normalizada or "numero de" in pergunta_normalizada) and not variaveis_interesse and filtros:
        variaveis_interesse = ['Total de Respondentes']

    if any(keyword in pergunta_normalizada for keyword in ["tipo de dados", "quais dados", "temos acesso", "colunas disponiveis", "variaveis disponiveis", "informacoes disponiveis", "o que posso perguntar"]):
        variaveis_interesse = ['Dados Disponíveis']
        filtros = {} 

    return filtros, variaveis_interesse


def aplicar_filtros(df_original, filtros):
    df_filtrado = df_original.copy()
    
    for coluna, condicao in filtros.items():
        if coluna not in df_filtrado.columns:
            st.warning(f"Atenção: A coluna '{coluna}' não foi encontrada nos dados. O filtro não será aplicado.")
            continue

        if isinstance(condicao, dict):
            valor_num = condicao.get('valor')
            operador = condicao.get('operador')
            
            coluna_numerica = pd.to_numeric(df_filtrado[coluna], errors='coerce') 
            
            if operador == '>':
                df_filtrado = df_filtrado[coluna_numerica > valor_num]
            elif operador == '<':
                df_filtrado = df_filtrado[coluna_numerica < valor_num]
            elif operador == 'between':
                min_val = condicao.get('min')
                max_val = condicao.get('max')
                df_filtrado = df_filtrado[(coluna_numerica >= min_val) & (coluna_numerica <= max_val)]
        else:
            valores_para_filtrar = [str(v).upper() for v in condicao]
            
            df_filtrado = df_filtrado[df_filtrado[coluna].isin(valores_para_filtrar)]
            
    return df_filtrado


def analisar_e_explicar_com_ia(pergunta, df_filtrado_final, filtros_aplicados, variaveis_interesse, mapa_colunas):
    total_registros_filtrados = len(df_filtrado_final)
    
    resposta_python = []
    tabela_para_exibir = None
    grafico_para_exibir = None

    if 'Dados Disponíveis' in variaveis_interesse:
        data_summary_text = ""
        for col_name, info in mapa_colunas.items():
            if col_name in df.columns:
                data_summary_text += f"- **{info['sinonimos_coluna'][0].capitalize()}** (coluna '{col_name}'): "
                if info['tipo'] == 'categorica':
                    top_categories = df[col_name].value_counts(dropna=False).nlargest(3).index.tolist()
                    data_summary_text += f"Variável categórica com opções como: {', '.join(top_categories)}. \n"
                elif info['tipo'] == 'numerica':
                    data_summary_text += f"Variável numérica (ex: idade, valores). \n"
                elif info['tipo'] == 'texto_aberto':
                    data_summary_text += f"Campo de texto livre (depoimentos, descrições). \n"
        
        contexto_metodologico = """
NOTA METODOLÓGICA FUNDAMENTAL:
Este dashboard utiliza dados primários e secundários coletados pela ADAI nos territórios 9, 10, 13, 14, 15 e 16 do Espírito Santo, referentes ao impacto do rompimento da barragem de Fundão (Samarco, Vale, BHP Billiton). Foram entrevistadas 624 famílias (1.794 pessoas) em setembro/outubro de 2023, usando questionário estruturado, a partir de amostragem representativa e snowball. Os resultados devem ser interpretados no contexto da pesquisa social, considerando limitações próprias do método e em fase contínua de atualização e análise. É fundamental reconhecer que cada número representa uma vida, uma história e uma jornada de resiliência.
"""
        prompt_ia_data_summary = f"""
        {contexto_metodologico}
        Você é a 'irmã IA' do dashboard, focada em ajudar a compreender os dados da ADAI.
        O usuário perguntou: "{pergunta}"
        Forneça uma resposta clara e concisa sobre os tipos de dados disponíveis, com uma linguagem acolhedora e informativa. Mencione as principais categorias e colunas que podem ser exploradas. Não invente dados.
        Use uma introdução empática e conclua convidando o usuário a explorar mais.
        \n\n--- Resumo de Dados Gerado pelo Sistema ---\n{data_summary_text}\n--- Fim do Resumo ---\n
        Baseado no resumo acima, explique os tipos de dados disponíveis com um tom acolhedor e poético, conectando a informação à complexidade da vida das pessoas atingidas.
        """
        model = genai.GenerativeModel('gemini-1.5-flash')
        try:
            resposta_ia = model.generate_content(prompt_ia_data_summary).text
        except Exception as e:
            resposta_ia = f"Desculpe, a IA encontrou um erro ao gerar a explicação sobre os dados: {e}."
        
        return resposta_ia, None, None

    if total_registros_filtrados > 0:
        if len(variaveis_interesse) == 1 and variaveis_interesse[0] != 'Total de Respondentes':
            coluna_principal = variaveis_interesse[0]
            if coluna_principal in df_filtrado_final.columns:
                info_col = mapa_colunas.get(coluna_principal, {"tipo": "texto_aberto"})

                if info_col["tipo"] == "categorica":
                    contagem = df_filtrado_final[coluna_principal].value_counts(normalize=False, dropna=False).reset_index()
                    contagem.columns = [coluna_principal, 'Contagem']
                    contagem['% do Total'] = (contagem['Contagem'] / total_registros_filtrados * 100).round(1)
                    tabela_para_exibir = contagem.sort_values(by='Contagem', ascending=False)
                    resposta_python.append(f"A seguir, você verá a distribuição dos respondentes por **{coluna_principal}**:")
                    
                    if contagem.shape[0] < 15 and contagem['Contagem'].sum() > 0:
                        grafico_para_exibir = px.bar(
                            tabela_para_exibir, 
                            x='Contagem', 
                            y=coluna_principal, 
                            orientation='h', 
                            title=f"Distribuição de '{coluna_principal}'",
                            text='Contagem',
                            color='Contagem',
                            color_continuous_scale=px.colors.sequential.Plasma,
                            labels={'Contagem': 'Número de Respondentes', coluna_principal: coluna_principal}
                        )
                        grafico_para_exibir.update_layout(yaxis={'categoryorder':'total ascending'})
                        resposta_python.append("Um gráfico de barras foi gerado para visualizar essa distribuição.")

                elif info_col["tipo"] == "numerica":
                    tabela_para_exibir = df_filtrado_final[coluna_principal].describe().to_frame().T.round(2)
                    resposta_python.append(f"As estatísticas descritivas para **{coluna_principal}** são as seguintes:")
                    
                    if not df_filtrado_final[coluna_principal].dropna().empty:
                        grafico_para_exibir = px.histogram(df_filtrado_final.dropna(subset=[coluna_principal]), x=coluna_principal, title=f"Distribuição de {coluna_principal}", nbins=10)
                        grafico_para_exibir.update_layout(bargap=0.1)
                        resposta_python.append("Um histograma foi gerado para mostrar a distribuição dos valores.")

        elif len(variaveis_interesse) >= 2: 
            var1 = variaveis_interesse[0]
            var2 = variaveis_interesse[1]
            info_var1 = mapa_colunas.get(var1)
            info_var2 = mapa_colunas.get(var2)

            if info_var1 and info_var1["tipo"] == "categorica" and \
               info_var2 and info_var2["tipo"] == "categorica" and \
               var1 in df_filtrado_final.columns and var2 in df_filtrado_final.columns:
                
                tabela_cruzada = pd.crosstab(df_filtrado_final[var1], df_filtrado_final[var2], dropna=False)
                tabela_para_exibir = tabela_cruzada.copy()
                resposta_python.append(f"A seguir, uma tabela cruzando **{var1}** por **{var2}** para os respondentes:")

                if tabela_cruzada.shape[0] < 10 and tabela_cruzada.shape[1] < 10:
                    df_plot = tabela_cruzada.stack().reset_index(name='Contagem')
                    df_plot.columns = [var1, var2, 'Contagem']
                    grafico_para_exibir = px.bar(
                        df_plot, 
                        x=var1, 
                        y='Contagem', 
                        color=var2, 
                        barmode='group',
                        title=f"Cruzamento de '{var1}' por '{var2}'",
                        labels={'Contagem': 'Número de Respondentes', var1: var1, var2: var2}
                    )
                    resposta_python.append("Um gráfico de barras agrupadas também foi gerado para esta análise.")
    
    if total_registros_filtrados > 80:
        sample_df_for_ia = df_filtrado_final.sample(80, random_state=42)
    else:
        sample_df_for_ia = df_filtrado_final
    
    if total_registros_filtrados == 0:
        df_string_for_ia = "Nenhum registro encontrado para esta consulta."
    else:
        df_string_for_ia = sample_df_for_ia.to_string(index=False, max_rows=50)


    contexto_metodologico = """
NOTA METODOLÓGICA FUNDAMENTAL:
Este dashboard utiliza dados primários e secundários coletados pela ADAI nos territórios 9, 10, 13, 14, 15 e 16 do Espírito Santo, referentes ao impacto do rompimento da barragem de Fundão (Samarco, Vale, BHP Billiton). Foram entrevistadas 624 famílias (1.794 pessoas) em setembro/outubro de 2023, usando questionário estruturado, a partir de amostragem representativa e snowball. Os resultados devem ser interpretados no contexto da pesquisa social, considerando limitações próprias do método e em fase contínua de atualização e análise. É fundamental reconhecer que cada número representa uma vida, uma história e uma jornada de resiliência.
"""
    
    prompt_ia = f"""
{contexto_metodologico}

Apresento os dados brutos filtrados e, se aplicável, uma tabela e/ou um gráfico gerados com base na pergunta do usuário. 
Sua missão é ir além da análise de dados pura, conectando os fatos à experiência humana e tocando as emoções do usuário, mantendo a precisão analítica. 
Você é a 'irmã IA' do dashboard, programada para falar de forma poética, analítica e sentimental sobre a situação das famílias atingidas pelo desastre.

--- Informações para sua análise ---
Pergunta do usuário: "{pergunta}"
Dados filtrados para análise (amostra de até 80 linhas):
{df_string_for_ia}
Total de registros encontrados após filtros: {total_registros_filtrados}
Variáveis de interesse identificadas: {', '.join(variaveis_interesse) if variaveis_interesse else 'Nenhuma específica, focar na contagem geral ou filtro.'}
Filtros aplicados (Colunas -> Valores): {filtros_aplicados}
Comentários da lógica Python sobre a apresentação: {' '.join(resposta_python) if resposta_python else 'Nenhuma tabela ou gráfico automático foi gerado diretamente.'}
--- Fim das Informações ---

**Instruções para sua Resposta (prioridade):**
1.  **Narrativa de Impacto (Gatilho Emocional):** Comece sua resposta com uma frase ou parágrafo que transmita um sentimento, conectando a pergunta aos desafios ou realidades das famílias. Use uma linguagem empática e descritiva. Exemplo: 'Ao explorarmos a realidade dos [filtros aplicados, se houver], somos convidados a vislumbrar as jornadas de resiliência que permeiam cada número...' Se a pergunta for sobre uma emoção (ex: 'dor', 'esperança' nos depoimentos), responda a essa emoção.
2.  **Contextualização Emocional dos Dados:** Ao apresentar qualquer número ou estatística, contextualize-o com o impacto humano. Em vez de apenas 'X pessoas', diga 'X indivíduos, cada um com sua história e seu pedaço de céu perdido'. Se o resultado for 0, diga que 'não encontramos registros que pudessem contar a história de...'
3.  **Análise Estatística e Interpretação (Clara e Acessível):** Traduza os números (contagens, porcentagens, médias, correlações - se você conseguir inferir) em insights compreensíveis. Explique o 'porquê' e o 'o quê' dos padrões. Use um tom analítico, mas acessível.
4.  **Estilo de Escrita Envolvente (Poético/Dramático):** Adapte sua linguagem para ser mais poética, dramática ou introspectiva conforme o contexto. Use metáforas (ex: "cicatrizes na paisagem", "tecelãs de um novo amanhã"), analogias, e um ritmo que convide à reflexão e empatia.
5.  **Tratamento de Dados Ausentes/Não Declarados:** Se houver valores 'NÃO DECLARADO' relevantes nos dados filtrados ou na análise, mencione a presença desses dados ausentes e o que isso pode significar para a completude do panorama, sem culpabilizar. Exemplo: 'É importante notar que [X]% dos dados não foram declarados, representando talvez um silêncio que também fala sobre desafios ou privacidade.'
6.  **Menção à Nota Metodológica:** Em algum ponto da sua explicação, reforce a importância da Nota Metodológica (que está acima) para a interpretação dos resultados.
7.  **Sugestão de Próximos Passos (Aprofundamento):** Ao final, sugira uma ou duas perguntas adicionais que o usuário poderia fazer para aprofundar a compreensão, mostrando a capacidade do dashboard.
8.  **Restrições:**
    * **NÃO invente dados, valores ou estatísticas** que não possam ser inferidos diretamente da 'Dados filtrados para análise' ou das 'Informações da lógica Python'. Se não puder inferir, diga que a informação não está clara nos dados disponíveis.
    * **NÃO faça generalizações** fora do contexto da 'amostra pesquisada' e do desastre da barragem de Fundão/ADAI.
    * Mantenha a resposta **concisa, mas completa**, em um tom de relatório empático.
"""
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        resposta_ia = model.generate_content(prompt_ia).text
    except Exception as e:
        resposta_ia = f"Desculpe, a IA encontrou um erro ao gerar a explicação: {e}. Por favor, tente novamente ou reformule sua pergunta."

    return resposta_ia, tabela_para_exibir, grafico_para_exibir

# Exemplo de uso, só para visual do chat:
def process_user_input(user_input):
    # TROQUE AQUI pelo seu processamento real!
    resposta = f"Esta é uma resposta fictícia para: **{user_input}**"
    tabela = pd.DataFrame({"Exemplo": [1,2,3], "Valor": [10,20,30]})
    grafico = px.bar(tabela, x="Exemplo", y="Valor")
    return resposta, tabela, grafico

# ---- Sessão State Inicial ----
if "chat_history_gemini" not in st.session_state:
    st.session_state.chat_history_gemini = []
if "show_orientations" not in st.session_state:
    st.session_state.show_orientations = True

# ---- Funções rápidas para ações ----
def clear_chat_history():
    st.session_state.chat_history_gemini = []
    st.session_state.show_orientations = True

def set_show_orientations(val):
    st.session_state.show_orientations = val

def handle_action(action):
    if action == "Mostrar Orientações":
        set_show_orientations(True)
    elif action == "Esconder Orientações":
        set_show_orientations(False)
    elif action == "Reiniciar Chat":
        clear_chat_history()
        st.rerun()
    # Você pode adicionar outras ações aqui (ex: exportar conversa)

# ---- Quick Suggestions (Perguntas Sugeridas ao estilo Gemini) ----
gemini_quick_questions = [
    "Quantas mulheres negras vivem em Colatina?",
    "Qual a distribuição de idade entre os quilombolas?",
    "Como está a escolaridade dos moradores do território 14?",
    "Como a raça/cor se relaciona com o gênero dos respondentes?",
    "Quais são os dados disponíveis?",
]

# ---- Chat History ----
for item in st.session_state.chat_history_gemini:
    with st.chat_message("user"):
        st.markdown(item["pergunta"])
    with st.chat_message("assistant"):
        st.markdown(item["resposta"])
        if "tabela" in item and item["tabela"] is not None:
            st.markdown("##### Dados Detalhados:")
            st.dataframe(item["tabela"], use_container_width=True)
            # Download da tabela
            csv = item["tabela"].to_csv(index=False).encode()
            st.download_button("⬇️ Baixar Tabela (CSV)", data=csv, file_name="analise_IA.csv", mime="text/csv", key=f"dl_{hash(item['pergunta'])}")
        if "grafico" in item and item["grafico"] is not None:
            st.markdown("##### Visualização Gráfica:")
            st.plotly_chart(item["grafico"], use_container_width=True)

# ---- Orientações (Expander moderno e colapsável) ----
if st.session_state.show_orientations:
    with st.expander("💡 Orientações para Perguntar à IA Gemini", expanded=True):
        st.markdown("""
        **Como fazer perguntas para a IA?**
        - Escreva dúvidas ou pedidos de informação de forma clara e objetiva.
        - Exemplos:
            - _"Quantas mulheres negras moram em Colatina?"_
            - _"Qual o número de pessoas com deficiência na faixa etária entre 40 e 60 anos?"_
            - _"Qual a escolaridade por município?"_
        - Utilize palavras-chave: gênero, idade, raça/cor, município, escolaridade, etc.
        - Combine critérios para análises mais profundas.

        ---
        :warning: **Atenção!**  
        Esta função de perguntas automáticas para a IA **ainda está em desenvolvimento** e pode apresentar limitações, respostas incompletas ou erros de interpretação.  
        **Recomenda-se sempre revisar as respostas da IA**.
        """)
        st.button("Esconder Orientações", on_click=lambda: set_show_orientations(False), key="hide_orientations_btn")

# ------------- QUICK SUGGESTIONS (Gemini Style) -------------
gemini_quick_questions = [
    "Quantas mulheres negras vivem em Colatina?",
    "Qual a distribuição de idade entre os quilombolas?",
    "Como está a escolaridade dos moradores do território 14?",
    "Como a raça/cor se relaciona com o gênero dos respondentes?",
    "Quais são os dados disponíveis?",
]
st.markdown('<div class="gemini-quick-row">', unsafe_allow_html=True)
for i, q in enumerate(gemini_quick_questions):
    if st.button(q, key=f"quick_{i}", help="Pergunta sugerida"):
        user_input = q
        st.session_state.show_orientations = False
        # PROCESSAMENTO
        resposta, tabela, grafico = process_user_input(user_input)  # Troque por sua função real!
        st.session_state.chat_history_gemini.append({
            "pergunta": user_input,
            "resposta": resposta,
            "tabela": tabela,
            "grafico": grafico
        })
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ------------- INPUT DE CHAT E MENU DE AÇÕES ACOPLADO (Gemini Style) -------------
col1, col2 = st.columns([6,1])
with col1:
    user_input = st.chat_input("Digite sua pergunta para a IA...", max_chars=400, key="input_gemini")
with col2:
    # Menu ações sempre ao lado do chat, nunca bloqueia
    actions = []
    if not st.session_state.show_orientations:
        actions.append("💡 Mostrar Orientações")
    if st.session_state.show_orientations:
        actions.append("❌ Esconder Orientações")
    actions.append("🔄 Reiniciar Chat")
    action = st.selectbox("Ações", ["Mais opções..."]+actions, label_visibility="collapsed", key="gemini_actions_select")
    if action == "💡 Mostrar Orientações":
        set_show_orientations(True)
        st.experimental_rerun()
    elif action == "❌ Esconder Orientações":
        set_show_orientations(False)
        st.experimental_rerun()
    elif action == "🔄 Reiniciar Chat":
        clear_chat_history()
        st.experimental_rerun()

# ------------- PROCESSAMENTO DA PERGUNTA DO USUÁRIO -------------
if user_input:
    st.session_state.show_orientations = False
    # COLOQUE SUA LÓGICA REAL ABAIXO!
    resposta, tabela, grafico = process_user_input(user_input)  # Troque por sua função real!
    st.session_state.chat_history_gemini.append({
        "pergunta": user_input,
        "resposta": resposta,
        "tabela": tabela,
        "grafico": grafico
    })
    st.rerun()

# ------------- EXPORTAR HISTÓRICO -------------
if st.session_state.chat_history_gemini:
    chat_export = "\n\n".join([f"Usuário: {h['pergunta']}\nIA: {h['resposta']}" for h in st.session_state.chat_history_gemini])
    st.download_button("Exportar histórico de chat (.txt)", data=chat_export, file_name="chat_gemini.txt", mime="text/plain")

# ============== FIM =============
