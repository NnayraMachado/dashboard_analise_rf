# ==============================================================================
# ---------- PARTE 1/3: CONFIGURAÇÃO, CARREGAMENTO E UTILITÁRIOS ----------
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re
import numpy as np
import unidecode
import os
from io import StringIO
from datetime import datetime, timezone
import json
import warnings

# --- CONFIGURAÇÕES INICIAIS E ESTILO ---
st.set_page_config(layout="wide", page_title="ADAI - Análise com IA")
st.markdown("""<style>...</style>""", unsafe_allow_html=True)  # CSS omitido por brevidade

st.header("💬 Pergunte à IA (Gemini)")
st.markdown("---")

# ---- CONFIGURAÇÃO DA API GEMINI ----
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Erro na configuração da API do Gemini: {e}")
    st.stop()

# --- CARREGAMENTO E ESTADO DA SESSÃO ---
@st.cache_data
def carregar_dados(caminho_arquivo):
    """
    Lê CSV com cabeçalho separado por ';' e retorna DataFrame.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
            cabecalho_str = f.readline()
            nomes_colunas = [col.strip() for col in cabecalho_str.strip().split(';')]
            resto_do_arquivo = StringIO(f.read())
            df = pd.read_csv(resto_do_arquivo, sep=';', names=nomes_colunas, low_memory=False)
        return df
    except Exception as e:
        st.error(f"ERRO CRÍTICO ao carregar o arquivo CSV: {e}")
        return None

if "df" not in st.session_state:
    caminho_do_arquivo_csv = os.path.join("data", "questionario.csv")
    st.session_state["df"] = carregar_dados(caminho_do_arquivo_csv)
df = st.session_state.get("df")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# --- DICIONÁRIOS ---
mapa_colunas = {
    "ID7": {
        "sinonimos_coluna": ["raça", "cor", "etnia"],
        "categorias": {
            "negra": ["PRETA", "PARDA"],
            "preta": ["PRETA"],
            "parda": ["PARDA"],
            "branca": ["BRANCA"],
            "indígena": ["INDÍGENA"],
            "amarela": ["AMARELA"]
        }
    },
    "ADAI_ID8": {
        "sinonimos_coluna": ["gênero", "sexo"],
        "categorias": {"mulher": ["FEMININO"], "homem": ["MASCULINO"]}
    },
    "ADAI_CT4": {
        "sinonimos_coluna": ["território", "localidade", "município", "cidade", "onde"],
        "categorias": {
            "colatina": ["COLATINA"],
            "baixo guandu": ["BAIXO GUANDU"],
            "linhares": ["LINHARES"],
            "sao mateus": ["SÃO MATEUS"]
        }
    },
    "ID11": {
        "sinonimos_coluna": ["escolaridade", "estudo", "nível superior"],
        "categorias": {"superior": ["ENSINO SUPERIOR COMPLETO", "SUPERIOR INCOMPLETO"]}
    },
    "ID12": {
        "sinonimos_coluna": ["profissão", "trabalho", "ocupação", "pescadores", "pescadora"],
        "categorias": {"pescadora": ["PESCADOR(A)"]}
    },
}

dicionario_de_dados = {
    "ID1": "Nome completo/nome social",
    "ID3": "Data de nascimento",
    "ID6.1": "CPF",
    "ID7": "Cor/Raça",
    "ADAI_ID8": "Gênero",
    "ADAI_CT4": "Município Principal",
    "ID11": "Nível de Escolaridade",
    "ID12": "Ocupação Principal",
}

mapa_colunas_tematico = {
    "Perfil Demográfico": ["ADAI_ID8", "ID7"],
    "Localização": ["ADAI_CT4"],
    "Educação e Trabalho": ["ID11", "ID12"],
}

# --- UTILITÁRIOS ---
def extrair_filtros_e_variaveis(pergunta, mapa):
    filtros, variaveis_interesse = {}, []
    pergunta_normalizada = unidecode.unidecode(pergunta).lower()
    for col, info in mapa.items():
        if "sinonimos_coluna" in info:
            for sinonimo in info["sinonimos_coluna"]:
                if re.search(rf'\b{unidecode.unidecode(sinonimo).lower()}\b', pergunta_normalizada):
                    if col not in variaveis_interesse:
                        variaveis_interesse.append(col)
        if "categorias" in info:
            for termo, valores_df in info["categorias"].items():
                if re.search(rf'\b{unidecode.unidecode(termo).lower()}\b', pergunta_normalizada):
                    if col not in filtros:
                        filtros[col] = []
                    filtros[col].extend(valores_df)
    return filtros, variaveis_interesse

def aplicar_filtros(df_original, filtros):
    if df_original is None:
        return pd.DataFrame()
    df_filtrado = df_original.copy()
    for coluna, valores in filtros.items():
        if coluna in df_filtrado.columns:
            df_filtrado[coluna] = (
                df_filtrado[coluna].fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )
            df_filtrado = df_filtrado[df_filtrado[coluna].isin(valores)]
    return df_filtrado

def formatar_filtros_para_prompt(filtros):
    partes = []
    for coluna, valores in filtros.items():
        rotulo = dicionario_de_dados.get(coluna, coluna)
        valores_legiveis = ", ".join(valores)
        partes.append(f"{rotulo} igual a {valores_legiveis}")
    return "; ".join(partes) if partes else "nenhum filtro aplicado"

def avaliar_forca_amostra(total_original, total_filtrado):
    if not isinstance(total_original, (int, float)) or total_original <= 0:
        return "Tamanho da base original desconhecido, dificultando avaliação da representatividade.", "incerto"
    if total_filtrado == 0:
        return "Não há registros após a aplicação dos filtros.", "nenhuma"
    proporcao = total_filtrado / total_original
    if total_filtrado < 10:
        return (
            "A amostra é muito pequena (menos de 10 registros); qualquer inferência terá baixa robustez e alta incerteza.",
            "baixa"
        )
    if proporcao < 0.01:
        return (
            f"A amostra representa menos de 1% da base original ({total_filtrado} de {total_original}); pode não ser representativa sem verificação adicional.",
            "moderada-baixa"
        )
    return "A amostra tem tamanho razoável para uma primeira interpretação, mas deve-se manter cautela ao generalizar.", "moderada"

def gerar_sugestao_se_dado_fraco(filtros, nivel_confianca):
    if nivel_confianca in ("nenhuma", "baixa", "moderada-baixa"):
        if not filtros:
            return "Talvez você possa esclarecer melhor o que quer saber — por exemplo: 'Quantas mulheres negras moram em Colatina com escolaridade superior?'"
        else:
            partes = [dicionario_de_dados.get(c, c) for c in filtros.keys()]
            return (
                f"A filtragem atual ({', '.join(partes)}) produziu poucos dados confiáveis. "
                "Você poderia tentar expandir o escopo, por exemplo: remover um dos filtros ou perguntar sobre um grupo mais amplo?"
            )
    return None

def inferir_tipo_coluna(serie: pd.Series):
    if pd.api.types.is_numeric_dtype(serie):
        return "numérica"
    # tentativa de detectar data, com suprimir warning para formatos ambíguos
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Could not infer format")
        try:
            # tentar converter alguns exemplos; se não lançar erro, consideramos data
            pd.to_datetime(serie.dropna().unique()[:5], errors="raise", infer_datetime_format=True)
            return "data"
        except Exception:
            pass
    unique = serie.dropna().astype(str).str.strip().str.upper().unique()
    if len(unique) <= 20:
        return "categórica"
    if serie.dtype == object:
        return "texto livre"
    return "desconhecida"

def descrever_base_dados(df):
    total = df.shape[0]
    linhas = [f"A base contém {total} registros."]

    temas = {}
    usado = set()
    for tema, cols in mapa_colunas_tematico.items():
        presentes = [c for c in cols if c in df.columns]
        if presentes:
            temas[tema] = presentes
            usado.update(presentes)
    outros = [c for c in df.columns if c not in usado]
    if outros:
        temas["Outros / Não categorizados"] = outros

    detalhes = []
    for tema, cols in temas.items():
        linhas.append(f"**{tema}:** {', '.join([dicionario_de_dados.get(c, c) for c in cols])}.")
        for c in cols:
            serie = df[c].fillna("").astype(str)
            tipo = inferir_tipo_coluna(serie)
            missing_pct = 100 * (serie == "").sum() / max(len(serie), 1)
            exemplo = ""
            if tipo == "categórica":
                top = serie.str.upper().value_counts().head(3)
                exemplo = ", ".join([f"{idx} ({cnt})" for idx, cnt in top.items()])
            elif tipo == "numérica":
                try:
                    num = pd.to_numeric(serie.str.replace(",", ".").replace("", np.nan), errors="coerce")
                    exemplo = f"média {num.mean():.2f}, mediana {num.median():.2f}, desvio {num.std():.2f}"
                except Exception:
                    exemplo = "valores numéricos não totalmente consistentes"
            elif tipo == "data":
                exemplo = "formato de data detectado"
            elif tipo == "texto livre":
                exemplo = "texto variado, sem categorização clara"
            detalhes.append(f"- {dicionario_de_dados.get(c, c)} ({c}): tipo presumido {tipo}, {missing_pct:.1f}% faltando; exemplo: {exemplo}.")
    linhas.append("\nDetalhes por coluna:\n" + "\n".join(detalhes))
    linhas.append("\nSugestões iniciais de exploração: por exemplo, 'Qual a distribuição de gênero por município?', 'Quais municípios têm maior proporção de pessoas com ensino superior?', 'Existem interseções como mulheres negras com ensino superior em determinada localidade?'")
    return "\n".join(linhas)

def detectar_intencao_resumo_base(pergunta: str):
    p = unidecode.unidecode(pergunta.lower())
    palavras_chave = [
        "que tipo de dados", "quais dados temos", "o que tem na base",
        "que informações", "descrição da base", "quais colunas", "quais campos", "entender a base"
    ]
    return any(kw in p for kw in palavras_chave)
# ==============================================================================
# ---------- PARTE 2/3: INTERAÇÃO COM IA, ANÁLISE, RESUMO DE TEMA E LOGGING ----------
# ==============================================================================

def analisar_e_explicar_com_ia(pergunta, df_filtrado, filtros, variaveis, mapa_de_sinonimos, tom="acessível e empático"):
    model = genai.GenerativeModel("gemini-1.5-flash")
    total_registros = len(df_filtrado)
    total_original = st.session_state.get("df").shape[0] if st.session_state.get("df") is not None else None

    amostra_dados_str = "Nenhum dado encontrado com os filtros aplicados."
    if not df_filtrado.empty:
        colunas_relevantes = list(filtros.keys()) + [v for v in variaveis if v not in filtros]
        colunas_existentes = [c for c in colunas_relevantes if c in df_filtrado.columns]
        amostra_dados_str = df_filtrado[colunas_existentes].head(5).to_string()

    filtros_legiveis = formatar_filtros_para_prompt(filtros)
    observacao_amostra, nivel_confianca = avaliar_forca_amostra(total_original or 0, total_registros)
    sugestao_se_precisa = gerar_sugestao_se_dado_fraco(filtros, nivel_confianca)

    prompt_detalhado = f"""
Você é um analista de dados com experiência em comunicação acessível, sensibilidade social e consciência da validade estatística. A tarefa é interpretar a pergunta do usuário levando em conta os dados disponíveis, explicar claramente o que pode e o que não pode ser afirmado com base na amostra, e também trazer uma leitura empática — quais sentimentos ou preocupações podem emergir desses números para as pessoas afetadas.

Pergunta do usuário: "{pergunta}"

Contexto dos dados:
- Tamanho da base original: {total_original if total_original is not None else 'desconhecido'} registros.
- Filtros aplicados: {filtros_legiveis}.
- Tamanho após filtragem: {total_registros} registros.
- Avaliação da amostra: {observacao_amostra} (nível de confiança estimado: {nivel_confianca}).
{"Sugestão de refinamento: " + sugestao_se_precisa if sugestao_se_precisa else ""}

Amostra dos dados (até 5 registros):

Instruções para a resposta:
1. Comece com o número de registros resultantes e explique em termos humanos o que eles representam (ex: 'mulheres negras' = gênero FEMININO e cor PRETA ou PARDA).
2. Declare explicitamente o que pode ser afirmado com razoável confiança e o que é incerto ou sujeito a erro por causa do tamanho/representatividade da amostra. Use expressões como 'há sinais de', 'os dados sugerem', 'não é possível afirmar com confiança', etc.
3. Traga uma leitura empática: que sentimentos, desafios ou impactos sociais podem surgir a partir desses dados para as pessoas envolvidas.
4. Se os dados forem fracos ou ambíguos, sugira como reformular a pergunta para melhorar a análise.
5. Mantenha o tom {tom}.
6. Termine com a ressalva obrigatória:
"Importante: esta análise reflete os dados da amostra fornecida e não pode ser generalizada para toda a população atingida sem um estudo estatístico mais aprofundado."
"""

    try:
        resposta_ia = model.generate_content(prompt_detalhado).text

        colunas_tabela = list(filtros.keys()) + variaveis
        colunas_tabela_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
        tabela_para_mostrar = df_filtrado[colunas_tabela_existentes] if colunas_tabela_existentes else df_filtrado

        # Log da consulta (CSV e JSON)
        try:
            log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pergunta": pergunta,
                "filtros": filtros_legiveis,
                "variaveis": ",".join(variaveis) if variaveis else "",
                "total_original": total_original,
                "total_filtrado": total_registros,
                "nivel_confianca": nivel_confianca,
                "resposta_resumida": resposta_ia[:500].replace("\n", " ")
            }
            os.makedirs("logs", exist_ok=True)

            # CSV
            log_path_csv = os.path.join("logs", "historico_perguntas.csv")
            log_df = pd.DataFrame([log])
            if os.path.exists(log_path_csv):
                log_df.to_csv(log_path_csv, mode="a", header=False, index=False)
            else:
                log_df.to_csv(log_path_csv, mode="w", header=True, index=False)

            # JSON acumulativo
            log_path_json = os.path.join("logs", "historico_perguntas.json")
            if os.path.exists(log_path_json):
                try:
                    with open(log_path_json, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []
            else:
                existing = []
            existing.append(log)
            with open(log_path_json, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # não impede resposta

        return resposta_ia, tabela_para_mostrar.head(100), None
    except Exception as e:
        return f"Desculpe, a IA encontrou um erro: {e}.", pd.DataFrame(), None


def process_user_input(user_input, df_completo, tom="acessível e empático"):
    if df_completo is None:
        return "Erro: Os dados não puderam ser carregados.", None, None

    if detectar_intencao_resumo_base(user_input):
        descricao = descrever_base_dados(df_completo)
        prompt_base = f"""
Você é um analista de dados com experiência em comunicar de forma clara e sensível. 
O usuário perguntou: "{user_input}".
Forneça um resumo estruturado da base de dados disponível. Abaixo há uma descrição automática como ponto de partida; reescreva de forma mais natural e acessível, adicionando uma nota técnica separada para quem quiser detalhes mais profundos. Inclua sugestões de próximas perguntas e destaque limitações importantes como dados faltantes ou representatividade.

Ponto de partida (gerado automaticamente):
{descricao}

Ressalva final: "Antes de generalizar para fora da amostra, é necessário validar e limpar os dados, pois podem haver vieses ou lacunas."
"""
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            resposta_ia = model.generate_content(prompt_base).text
        except Exception as e:
            resposta_ia = f"Desculpe, a IA encontrou um erro ao descrever a base: {e}."
        return resposta_ia, df_completo.head(100), None

    filtros, variaveis = extrair_filtros_e_variaveis(user_input, mapa_colunas)
    df_filtrado = aplicar_filtros(df_completo.copy(), filtros)
    return analisar_e_explicar_com_ia(user_input, df_filtrado, filtros, variaveis, mapa_colunas, tom=tom)


def gerar_resumo_tema_com_ia(tema_escolhido, df, tom="acessível e empático"):
    modelo = genai.GenerativeModel("gemini-1.5-flash")
    colunas_do_tema = mapa_colunas_tematico.get(tema_escolhido, [])
    cols = [c for c in colunas_do_tema if c in df.columns]
    if not cols:
        return f"Não há colunas disponíveis para o tema '{tema_escolhido}'.", pd.DataFrame(), None

    subset = df[cols].copy()
    for c in subset.columns:
        subset[c] = subset[c].fillna("").astype(str).str.strip().str.upper()

    descricoes = []
    for c in subset.columns:
        serie = subset[c]
        tipo = inferir_tipo_coluna(serie)
        missing_pct = 100 * (serie == "").sum() / max(len(serie), 1)
        if tipo == "categórica":
            top = serie.value_counts().head(3).to_dict()
            top_str = ", ".join([f"{k} ({v})" for k, v in top.items()])
            descricoes.append(f"{dicionario_de_dados.get(c, c)}: categórica, top valores: {top_str}, {missing_pct:.1f}% faltando.")
        elif tipo == "numérica":
            try:
                num = pd.to_numeric(serie.str.replace(",", ".").replace("", np.nan), errors="coerce")
                descricoes.append(f"{dicionario_de_dados.get(c, c)}: numérica, média {num.mean():.2f}, mediana {num.median():.2f}, {missing_pct:.1f}% faltando.")
            except Exception:
                descricoes.append(f"{dicionario_de_dados.get(c, c)}: numérica com inconsistências, {missing_pct:.1f}% faltando.")
        else:
            descricoes.append(f"{dicionario_de_dados.get(c, c)}: tipo {tipo}, {missing_pct:.1f}% faltando.")

    contexto_breve = "\n".join(descricoes[:5])

    prompt_tema = f"""
Você é um analista de dados com sensibilidade social e capacidade de comunicar para públicos técnicos e leigos. O usuário está explorando o tema '{tema_escolhido}'. Com base nos dados desse subconjunto, interprete os padrões possíveis, indique o que pode ser dito com confiança e o que é incerto, e traga uma leitura empática sobre o que esses padrões podem significar para as pessoas. Use linguagem dual: um parágrafo breve para leigos e, abaixo, uma nota técnica. Também sugira uma próxima pergunta útil para aprofundar.

Contexto estatístico rápido (pré-análise):
{contexto_breve}

Amostra de até 5 registros do tema:

Instruções:
1. Diga quais são os sinais mais evidentes nos dados do tema.
2. Declare limitações e incertezas (ex: categorias com muitas lacunas, poucas observações).
3. Traga leitura empática (sentimentos, preocupações, resiliência, etc.).
4. Sugira uma pergunta de seguimento para exploração mais profunda.
5. Use tom {tom}.
6. Termine com a ressalva: "Esta interpretação se baseia na amostra disponível e requer validação antes de generalizar."
"""

    try:
        resposta = modelo.generate_content(prompt_tema).text
        return resposta, subset.head(100), None
    except Exception as e:
        return f"Erro ao gerar interpretação do tema: {e}.", subset.head(100), None
# ==============================================================================
# ---------- PARTE 3/3: INTERFACE, CONTROLE DE HISTÓRICO E FLUXO ----------
# ==============================================================================

from datetime import timezone  # caso não esteja no topo já

# Sidebar: controle do histórico
with st.sidebar.expander("Controle do Histórico", expanded=True):
    mostrar_hist = st.checkbox("Mostrar histórico de perguntas/respostas", value=False, key="mostrar_hist")
    if st.button("Limpar histórico"):
        st.session_state.chat_history = []
        st.success("Histórico limpo.")
    if st.session_state.chat_history:
        histórico_df = pd.DataFrame([
            {
                "pergunta": item.get("pergunta", ""),
                "resposta": item.get("resposta", "").replace("\n", " "),
                "timestamp": item.get("timestamp", "")
            }
            for item in st.session_state.chat_history
        ])
        st.download_button(
            label="Exportar histórico (CSV)",
            data=histórico_df.to_csv(index=False),
            file_name="historico_perguntas.csv",
            mime="text/csv"
        )
        st.download_button(
            label="Exportar histórico (JSON)",
            data=json.dumps([
                {"pergunta": item.get("pergunta", ""), "resposta": item.get("resposta", "")}
                for item in st.session_state.chat_history
            ], ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="historico_perguntas.json",
            mime="application/json"
        )

# Interface principal
st.markdown("Faça uma pergunta específica sobre os dados, explore por tema, ou peça para descrever a base. Escolha o tom da resposta para tornar a IA mais técnica ou mais acessível.")

tom_selecionado = st.radio("Tom da resposta:", ["Neutro e técnico", "Acessível e empático", "Formal e objetivo"], index=1)
tom_map = {
    "Neutro e técnico": "neutro e técnico",
    "Acessível e empático": "acessível e empático",
    "Formal e objetivo": "formal e objetivo"
}
tom_para_prompt = tom_map[tom_selecionado]

# Perguntas rápidas
gemini_quick_questions = [
    "Quantas mulheres negras vivem em Colatina?",
    "Quantas mulheres pescadoras de Linhares têm ensino superior?",
    "Qual a profissão mais comum entre as mulheres pardas?",
    "Que tipo de dados temos disponíveis?"
]
st.markdown('<div class="gemini-quick-row">', unsafe_allow_html=True)
for q in gemini_quick_questions:
    if st.button(q, key=f"quick_{q}", help="Pergunta sugerida", disabled=st.session_state.processing):
        st.session_state.user_input = q
        st.session_state.processing = True
        st.session_state.chat_history.append({
            "pergunta": q,
            "is_placeholder": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Expander: exploração por tema com interpretação da IA
with st.expander("📂 Explorar Resumo Visual e Interpretativo por Tema", expanded=False):
    if df is not None and not df.empty:
        tema_escolhido = st.selectbox("Escolha um tema:", list(mapa_colunas_tematico.keys()), key="sb_temas")
        if tema_escolhido:
            st.markdown(f"**Resumo visual e interpretação do tema: {tema_escolhido}**")
            colunas_do_tema = mapa_colunas_tematico.get(tema_escolhido, [])
            subset_vis = df[[c for c in colunas_do_tema if c in df.columns]].copy()
            for c in subset_vis.columns:
                subset_vis[c] = subset_vis[c].fillna("").astype(str).str.strip().str.upper()
            if not subset_vis.empty:
                for c in subset_vis.columns:
                    counts = subset_vis[c].value_counts().reset_index()
                    counts.columns = [c, "contagem"]
                    st.subheader(dicionario_de_dados.get(c, c))
                    fig = px.bar(
                        counts,
                        x=c,
                        y="contagem",
                        title=f"Distribuição de {dicionario_de_dados.get(c, c)}",
                        labels={c: dicionario_de_dados.get(c, c), "contagem": "Quantidade"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                resposta_tema, tabela_tema, _ = gerar_resumo_tema_com_ia(tema_escolhido, df, tom=tom_para_prompt)
                st.markdown("**Interpretação da IA sobre o tema:**")
                st.markdown(resposta_tema)
                if tabela_tema is not None and not tabela_tema.empty:
                    st.markdown("**Amostra de dados do tema:**")
                    st.dataframe(tabela_tema, use_container_width=True)
            else:
                st.info("Não há dados suficientes para esse tema no momento.")

st.markdown("---")

# Fluxo de entrada e processamento (robusto)
if prompt := st.chat_input("Sua pergunta...", disabled=st.session_state.processing):
    st.session_state.user_input = prompt
    st.session_state.processing = True
    st.session_state.chat_history.append({
        "pergunta": prompt,
        "is_placeholder": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

if st.session_state.processing and st.session_state.chat_history:
    last_item = st.session_state.chat_history[-1]
    if last_item.get("is_placeholder"):
        with st.spinner("Analisando e consultando a IA..."):
            resposta, tabela, grafico = process_user_input(last_item["pergunta"], df, tom=tom_para_prompt)
        last_item.update({
            "resposta": resposta,
            "tabela": tabela,
            "grafico": grafico,
            "is_placeholder": False
        })
        st.session_state.processing = False

# Renderização da última interação (sempre visível) com tabela resumida e gráfico
if st.session_state.chat_history:
    last_item = st.session_state.chat_history[-1]
    if not last_item.get("is_placeholder"):
        with st.chat_message("user"):
            st.markdown(f"**Pergunta:** {last_item['pergunta']}")
        with st.chat_message("assistant"):
            st.markdown(last_item.get("resposta", ""), unsafe_allow_html=True)

            # se houver tabela filtrada, construir resumo útil
            if last_item.get("tabela") is not None and not last_item["tabela"].empty:
                df_filtrado = last_item["tabela"]

                with st.expander("Dados Detalhados (Tabela)"):
                    # Mostrar contagens agregadas das combinações relevantes
                    # Se existirem colunas categóricas, agrupar e mostrar top
                    try:
                        # Combinações e contagem
                        agrupamento = (
                            df_filtrado
                            .groupby(list(df_filtrado.columns))
                            .size()
                            .reset_index(name="contagem")
                            .sort_values("contagem", ascending=False)
                        )
                        # Se muitas linhas, mostrar apenas top 15
                        limite = 15
                        st.markdown("**Resumo agregado das observações:**")
                        st.dataframe(agrupamento.head(limite), use_container_width=True)

                        # Gráfico: top combinações como string concatenada
                        if not agrupamento.empty:
                            agrupamento["combo"] = agrupamento[df_filtrado.columns].astype(str).agg(" | ".join, axis=1)
                            top_para_grafico = agrupamento.head(10).copy()
                            fig = px.bar(
                                top_para_grafico,
                                x="combo",
                                y="contagem",
                                title="Top combinações de atributos",
                                labels={"combo": "Combinação", "contagem": "Quantidade"}
                            )
                            fig.update_layout(xaxis_tickangle=45, margin=dict(t=40, b=120))
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        # fallback: mostra a tabela bruta se algo falhar
                        st.dataframe(df_filtrado, use_container_width=True)

# Renderização do histórico completo (opcional)
if st.session_state.get("mostrar_hist"):
    for item in st.session_state.chat_history[:-1]:  # já mostrou o último acima
        with st.chat_message("user"):
            st.markdown(f"**Pergunta:** {item['pergunta']}")
        with st.chat_message("assistant"):
            if item.get("is_placeholder"):
                with st.spinner("Analisando e consultando a IA..."):
                    pass
            else:
                st.markdown(item.get("resposta", ""), unsafe_allow_html=True)
                if item.get("tabela") is not None and not item["tabela"].empty:
                    with st.expander("Dados Detalhados (Tabela)"):
                        st.dataframe(item["tabela"], use_container_width=True)

