import streamlit as st
from PIL import Image


st.set_page_config(page_title="Painel Geral", page_icon="📊", layout="wide")

st.markdown("<br>", unsafe_allow_html=True)  # Espaço extra

st.markdown("<span style='font-size:38px; font-weight:bold'>Painel Geral do Sistema</span>", unsafe_allow_html=True)
st.markdown("<span style='font-size:24px'><b>👋 Bem-vindo(a) ao Sistema de Análise do Registro Familiar (RF)!</b></span>", unsafe_allow_html=True)

st.info("Pronto para transformar dados em conhecimento? Explore os recursos do menu ao lado!")

st.markdown("""
Este sistema permite analisar, visualizar e interpretar dados de questionários aplicados em campo, fornecendo <b>insights</b> para pesquisadores, gestores e comunidades.
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #f7f7fa; border-radius: 10px; padding: 20px 25px; margin-bottom:15px; border:1px solid #ededed;">
<b>🚀 Dicas rápidas:</b>
<ul>
     <li>📊 <span style="color:#3498db;">Para começar</span>: acesse qualquer análise no menu lateral.</li>
        <li>🗂️ <span style="color:#c77d0a;">Depois de carregar os dados</span>: navegue por todos os tipos de análise disponíveis.</li>
        <li>🏠 <span style="color:#18bc9c;">Volte para esta tela</span>: clicando em <b>Painel Geral</b> no menu lateral.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

with st.expander("💡 Como usar o sistema?"):
    st.markdown("""
        1. Clique em “Carregar e Filtrar Dados” para importar seu arquivo.
        2. Navegue pelos tipos de análise disponíveis no menu lateral.
        3. Use a opção “Pergunte à IA” para obter insights automatizados dos dados.
        4. Para ajuda, acesse “Sobre o Dashboard”.
    """, unsafe_allow_html=True)

st.caption("Para dúvidas sobre o funcionamento do sistema, consulte a seção 'Informações' no menu.")



st.markdown("""
    <style>
    .footer {
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
    }
    </style>
    <div class="footer">
        © 2024 ADAI. Desenvolvido por Gi-ADAI. 
    </div>
""", unsafe_allow_html=True)

