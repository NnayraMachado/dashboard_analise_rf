import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Painel Geral", page_icon="📊", layout="wide")

# --- Logo institucional (opcional) ---
# logo = "logo_adai.png"
# st.image(logo, width=110)

# --- Título central ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<span style='font-size:38px; font-weight:bold'>Painel Geral do Sistema</span>", unsafe_allow_html=True)
st.markdown("<span style='font-size:24px'><b>👋 Bem-vindo(a) ao Sistema de Análise do Registro Familiar (RF)!</b></span>", unsafe_allow_html=True)

# --- Missão / contexto institucional ---
st.markdown("""
<p style='font-size:1.07em; color:#444; margin-bottom:16px;'>
Este painel foi criado para fortalecer a <b>transparência, participação social e o uso ético dos dados</b> referentes às famílias atingidas, apoiando decisões e novas pesquisas.
</p>
""", unsafe_allow_html=True)

# --- Status de carregamento de dados (dinâmico) ---
if "df" in st.session_state:
    st.success("✔️ Dados carregados. Pronto para análise!")
else:
    st.warning("⚠️ Nenhum dado carregado. Acesse 'Carregar e Filtrar Dados' para começar.")

# --- Chamada para experimentar IA ---
st.markdown("💡 <b>Novo:</b> Experimente o recurso ‘Pergunte à IA’ para interpretar os dados de modo automatizado, poético e explicativo.", unsafe_allow_html=True)

# --- Introdução curta ---
st.markdown("""
Este sistema permite analisar, visualizar e interpretar dados de questionários aplicados em campo, fornecendo <b>insights</b> para pesquisadores, gestores e comunidades.
""", unsafe_allow_html=True)

# --- Dicas rápidas (em cartão clean) ---
st.markdown("""
<div style="background-color: #f7f7fa; border-radius: 10px; padding: 18px 25px; margin-bottom:15px; border:1px solid #ededed;">
<b>🚀 Dicas rápidas:</b>
<ul style="margin-top:8px;">
     <li>📊 <span style="color:#3498db;">Para começar</span>: acesse qualquer análise no menu lateral.</li>
     <li>🗂️ <span style="color:#c77d0a;">Depois de carregar os dados</span>: navegue por todos os tipos de análise disponíveis.</li>
     <li>🏠 <span style="color:#18bc9c;">Volte para esta tela</span>: clicando em <b>Painel Geral</b> no menu lateral.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# --- Links úteis / Ajuda ---
st.markdown("""
<div style="margin-top:10px; font-size:0.98em;">
📚 <a href="https://github.com/adai-ufes" target="_blank">Acesse a documentação técnica</a> &nbsp;|&nbsp;
✉️ <a href="mailto:contato@adai.org.br">Fale com a equipe</a>
</div>
""", unsafe_allow_html=True)

# --- Expander: Como usar o sistema? ---
with st.expander("💡 Como usar o sistema?"):
    st.markdown("""
        1. Clique em <b>Carregar e Filtrar Dados</b> para importar seu arquivo.
        2. Navegue pelos tipos de análise disponíveis no menu lateral.
        3. Use a opção <b>Pergunte à IA</b> para obter insights automatizados dos dados.
        4. Para ajuda, acesse <b>Sobre o Dashboard</b>.
    """, unsafe_allow_html=True)

# --- Mini roadmap dos recursos (opcional) ---
with st.expander("🗺️ Recursos disponíveis neste painel"):
    st.markdown("""
    - Visualização dinâmica de dados sociodemográficos
    - Cruzamento de variáveis
    - Mapas interativos por município
    - Análises comparativas e por grupos
    - Exportação de dados (.csv)
    - Interpretação por IA Gemini (Google)
    """)

# --- Selo de segurança/confidencialidade ---
st.markdown("""
<div style="color:#7f8c8d; font-size:0.97em; margin-top:10px; margin-bottom:18px;">
🔒 <b>Seus dados estão seguros:</b> Nenhuma informação pessoal identificável é compartilhada ou armazenada fora do painel.
</div>
""", unsafe_allow_html=True)

st.caption("Para dúvidas sobre o funcionamento do sistema, consulte a seção 'Informações' no menu.")

# --- Rodapé minimalista, dinâmico com ano ---
ano = datetime.now().year
st.markdown(f"""
    <style>
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100vw;
        background-color: #F9F9F9;
        color: #777;
        text-align: center;
        font-size: 0.95em;
        padding: 8px 0;
        z-index: 9999;
        border-top: 1px solid #e0e0e0;
    }}
    </style>
    <div class="footer">
        © {ano} ADAI. Desenvolvido por Gi-ADAI.
    </div>
""", unsafe_allow_html=True)
