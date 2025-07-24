import streamlit as st

# --- CSS Clean, minimalista ---
st.markdown("""
    <style>
    h1 {
        font-size: 2.1em;
        color: #264653;
        text-align: center;
        margin-bottom: 22px;
    }
    .card-minimal {
        background: #f9f9fb;
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 18px;
        border-left: 4px solid #b2bec3;
        box-shadow: 0 1px 5px rgba(120,130,140,0.07);
    }
    .section-title {
        font-size: 1.18em; color: #34495e;
        margin-bottom: 12px; margin-top: 8px;
        font-weight: 600;
        border-bottom: 1px solid #eee; padding-bottom: 2px;
    }
    ul { margin-top: 0; margin-bottom: 10px; }
    li { font-size: 1.03em; margin-bottom: 4px;}
    </style>
""", unsafe_allow_html=True)

st.header("Sobre o Dashboard")

st.markdown("""
<p style='text-align: center; font-size:1.08em; color:#333;'>
Este painel facilita a análise, visualização e comunicação dos dados do <b>Registro Familiar (RF)</b> coletados pela ADAI após o rompimento da Barragem de Fundão, trazendo informações de maneira transparente, ágil e segura.
</p>
""", unsafe_allow_html=True)

st.divider()

tab1, tab2 = st.tabs(["Sobre os Dados", "Sobre os Métodos"])

with tab1:
    st.markdown('<div class="card-minimal">', unsafe_allow_html=True)
    st.markdown('<span class="section-title">Metadados dos Dados</span>', unsafe_allow_html=True)
    st.markdown("""
    <ul>
        <li><b>Fonte:</b> Registro Familiar (RF) — ADAI</li>
        <li><b>População-alvo:</b> Famílias atingidas pelo desastre</li>
        <li><b>Período de Coleta:</b> Setembro-Outubro/2023</li>
        <li><b>Respondentes:</b> 624 núcleos (1.794 pessoas)</li>
        <li><b>Campos Abrangidos:</b> Identificação, sociodemografia, saúde, trabalho, programas sociais, percepções e outros.</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="card-minimal">', unsafe_allow_html=True)
    st.markdown('<span class="section-title">Principais Métodos Estatísticos e Analíticos</span>', unsafe_allow_html=True)
    st.markdown("""
    <ul>
        <li><b>Estatística descritiva:</b> Resumos, frequências e distribuição das variáveis.</li>
        <li><b>Tabelas de contingência:</b> Cruzamento entre variáveis para análises comparativas.</li>
        <li><b>Gráficos e mapas interativos:</b> Visualização dinâmica e exploratória.</li>
        <li><b>Análise de texto:</b> Processamento automatizado de respostas abertas com IA.</li>
        <li><b>Exportação de dados:</b> Download de tabelas em CSV/Excel.</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

st.markdown("""
<span class="section-title">Funcionalidades do Painel</span>
<ul>
    <li><b>Visualização dinâmica:</b> Dados filtráveis e interativos.</li>
    <li><b>Cruzamento de variáveis:</b> Relações entre recortes demográficos, sociais e territoriais.</li>
    <li><b>Análise por IA:</b> Interpretação automatizada e geração de insights com IA Gemini.</li>
    <li><b>Comparação de grupos:</b> Destaque de diferenças e semelhanças relevantes.</li>
</ul>
""", unsafe_allow_html=True)

st.divider()

st.subheader("Limitações e Recomendações")
st.warning("""
- Os resultados são descritivos/exploratórios. Para inferências avançadas, recomenda-se consulta a especialistas.
- Não há ponderação amostral automática neste painel.
- Respostas abertas são analisadas por IA; revisão humana é recomendada para decisões sensíveis.
- A qualidade das análises depende da integridade e clareza dos dados coletados.
""")

st.info("💡 Para saber mais sobre a IA deste painel, acesse a seção 'Sobre a IA' no menu lateral.")

