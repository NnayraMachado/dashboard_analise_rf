import streamlit as st

# --- Configurações Iniciais para um Visual Mais Profissional ---
# Podemos definir uma cor primária sutil se quisermos. Ex: #264653 (azul petróleo), #34495e (cinza azulado), #1a535c (verde escuro)
# No entanto, Streamlit não tem uma forma direta de mudar a cor do cabeçalho globalmente via Python.
# O controle é via CSS. Para este exemplo, manterei o padrão do Streamlit ou usarei HTML inline.

# Adicionar um pouco de CSS customizado para melhorar espaçamento e tipografia sutilmente
st.markdown(
    """
    <style>
    /* Estilo para o cabeçalho principal */
    h1 {
        font-size: 2.8em; /* Levemente maior */
        color: #264653; /* Uma cor mais sóbria */
        text-align: center;
        margin-bottom: 30px; /* Mais espaço abaixo do título principal */
    }
    /* Estilo para os subtítulos (h3) */
    h3 {
        color: #34495e; /* Outra cor sóbria */
        margin-top: 30px; /* Mais espaço acima */
        margin-bottom: 15px; /* Mais espaço abaixo */
        border-bottom: 1px solid #eee; /* Linha sutil abaixo dos subtítulos principais */
        padding-bottom: 5px;
    }
    /* Estilo para os subheaders (h2/h4) dentro das colunas */
    h2, h4 {
        color: #4a6572; /* Um tom de cinza azulado */
        margin-top: 20px;
        margin-bottom: 10px;
    }
    /* Parágrafos gerais */
    p {
        font-size: 1.05em; /* Levemente maior */
        line-height: 1.6; /* Melhorar legibilidade */
        margin-bottom: 10px;
    }
    /* Estilo para listas */
    ul {
        margin-bottom: 15px; /* Espaço abaixo das listas */
    }
    li {
        font-size: 1.05em;
        margin-bottom: 5px;
    }
    /* Estilo para os "cards" - seções Metadados e Métodos */
    .card {
        background-color: #f9f9f9; /* Fundo cinza bem clarinho */
        border-left: 5px solid #607d8b; /* Borda lateral discreta */
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1); /* Sombra sutil */
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.header("Sobre o Dashboard") # Este header pode ser centralizado ou estilizado com o CSS acima

st.markdown("""
<p style='text-align: center; font-size: 1.1em; color: #555;'>
Este painel foi desenvolvido para facilitar a compreensão, análise e comunicação dos dados do <b>Registro Familiar (RF)</b>, coletados pela ADAI após o rompimento da Barragem de Fundão.
</p>
""", unsafe_allow_html=True)


st.divider() # Um separador simples e elegante

st.markdown("### 🚀 Principais Funcionalidades") # Use um título um pouco menor e mais amigável
st.markdown("""
<ul>
    <li>📊 <strong>Visualização Dinâmica:</strong> Dados sociodemográficos com filtros interativos.</li>
    <li>🔍 <strong>Cruzamento de Variáveis:</strong> Análise aprofundada de relações entre dados.</li>
    <li>🗺️ <strong>Mapas Interativos:</strong> Explore a distribuição geográfica por município.</li>
    <li>🆚 <strong>Análises Comparativas:</strong> Compare cenários ou grupos específicos.</li>
    <li>📥 <strong>Exportação de Dados:</strong> Baixe tabelas em CSV/Excel para uso externo.</li>
    <li>🤖 <strong>Interpretação por IA:</strong> Análise automatizada e insights baseados em IA Gemini.</li>
</ul>
""", unsafe_allow_html=True) # Usando HTML para lista com bullet points mais controlados

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="card">
            <h4><i class="fas fa-database" style="margin-right: 10px;"></i>Metadados dos Dados</h4>
            <ul>
                <li><strong>Fonte:</strong> Registro Familiar (RF) – ADAI</li>
                <li><strong>População-alvo:</strong> Famílias atingidas</li>
                <li><strong>Período de Coleta:</strong> Set-Out/2023</li>
                <li><strong>Respondentes:</strong> 624 núcleos (1.794 pessoas)</li>
                <li><strong>Campos Abrangidos:</strong> Identificação, sociodemográficos, saúde, trabalho, programas sociais, percepções, entre outros.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )
    # Importante: para o ícone 'fas fa-database' funcionar, você precisaria adicionar o Font Awesome
    # link no seu Streamlit. Se não quiser essa complexidade, remova o <i> tag.
    # Ex: <i class="fas fa-database" style="margin-right: 10px;"></i>
    # Uma forma mais simples para ícones é usar emojis como ℹ️ ou 📋.

with col2:
    st.markdown(
        """
        <div class="card">
            <h4><i class="fas fa-chart-line" style="margin-right: 10px;"></i>Métodos Estatísticos</h4>
            <ul>
                <li><strong>Estatística Descritiva:</strong> Resumos e distribuições.</li>
                <li><strong>Tabelas de Contingência:</strong> Análise de frequências cruzadas.</li>
                <li><strong>Comparação de Grupos:</strong> Destaque de diferenças significativas.</li>
                <li><strong>Gráficos e Mapas Interativos:</strong> Visualizações dinâmicas e exploratórias.</li>
                <li><strong>Análise de Texto:</strong> Interpretação automatizada de respostas abertas com IA.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )
    # Similarmente, para o ícone 'fas fa-chart-line', se não tiver Font Awesome, remova o <i> tag.
    # Uma forma mais simples para ícones é usar emojis como 📈 ou 🔬.


st.divider()

st.warning("""
⚠️ **Limitações e Recomendações Importantes**

* Resultados descritivos/exploratórios — para análises inferenciais detalhadas, recomenda-se a consulta a um especialista.
* Não há ponderação amostral automática aplicada neste painel.
* Respostas abertas analisadas por IA; revisão humana é sempre recomendada para maior precisão.
* A precisão e a utilidade do painel dependem diretamente da qualidade e integridade dos dados recebidos.
""")

st.info("💡 **Dica:** Para entender melhor como a IA do painel funciona e seus princípios, acesse a seção 'Sobre a IA' no menu lateral.")
