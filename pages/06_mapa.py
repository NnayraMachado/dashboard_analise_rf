import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import numpy as np
import unidecode # <--- IMPORTAÇÃO ADICIONADA AQUI!


# --- Função para padronizar nomes (ADICIONADA NOVAMENTE AQUI!) ---
def padroniza_nome(nome):
    """Padroniza nomes removendo acentos, espaços extras e convertendo para maiúsculas."""
    return unidecode.unidecode(str(nome)).strip().upper()


# --- Função para carregar CSS ---
def load_css_from_root(file_name="styles.css"):
    current_script_dir = os.path.dirname(__file__)
    root_dir = os.path.join(current_script_dir, '..')
    css_file_path = os.path.join(root_dir, file_name)
    try:
        with open(css_file_path, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Certifique-se de que ele está na pasta raiz do seu projeto.")

load_css_from_root()

from utils.session import ensure_session_data
ensure_session_data()

df = st.session_state.get('df')
question_labels = st.session_state.get('question_labels')

if df is None:
    st.error("Erro: Dados essenciais não foram carregados. Por favor, navegue para a página inicial ou de carregamento de dados.")
    st.stop()

# --- Pré-processamento de Dados para o Mapa ---
df['ADAI_CT4'] = df['ADAI_CT4'].astype(str)

# --- Adiciona 'Mes_Ano' ao DataFrame principal para filtragem temporal ---
if 'CT2' in df.columns:
    df['CT2'] = df['CT2'].astype(str).str.strip()
    df['CT2'] = pd.to_datetime(df['CT2'], format='%d/%m/%Y', errors='coerce')
    df['Mes_Ano'] = df['CT2'].dt.to_period('M').astype(str)
else:
    df['Mes_Ano'] = 'Total' # Ou um valor padrão se não houver data

# Prepara DataFrame de municípios e total de respondentes
df_map_data_base = df.groupby('ADAI_CT4').size().reset_index(name='Total Respondentes')
df_map_data_base = df_map_data_base.rename(columns={'ADAI_CT4': 'nome'})
# --- Padroniza nomes dos municípios no DataFrame base ---
df_map_data_base['nome_padrao'] = df_map_data_base['nome'].apply(padroniza_nome)


# Carrega e mescla com lat/lon
current_script_dir = os.path.dirname(__file__)
root_dir = os.path.join(current_script_dir, '..')
lat_lon_file_path = os.path.join(root_dir, 'data', 'municipios_es_lat_lon.csv')

try:
    lat_lon_df = pd.read_csv(lat_lon_file_path, sep=';', encoding='utf-8')
    lat_lon_df['nome'] = lat_lon_df['nome'].astype(str)
    # --- Padroniza nomes dos municípios no DF de lat/lon ---
    lat_lon_df['nome_padrao'] = lat_lon_df['nome'].apply(padroniza_nome)
    
    # Merge usando a coluna padronizada
    df_map_data_base = df_map_data_base.merge(lat_lon_df, on='nome_padrao', how='left', suffixes=('', '_latlon'))
    # Após o merge, manter a coluna 'lat' e 'lon' da lat_lon_df
    df_map_data_base['lat'] = df_map_data_base['lat'].fillna(df_map_data_base['lat_latlon'] if 'lat_latlon' in df_map_data_base.columns else np.nan)
    df_map_data_base['lon'] = df_map_data_base['lon'].fillna(df_map_data_base['lon_latlon'] if 'lon_latlon' in df_map_data_base.columns else np.nan)
    # Remover colunas duplicadas geradas pelo merge se elas não forem úteis
    df_map_data_base = df_map_data_base.drop(columns=[col for col in df_map_data_base.columns if col.endswith('_latlon')], errors='ignore')

except FileNotFoundError:
    st.error(f"Erro: Arquivo '{lat_lon_file_path}' não encontrado. O mapa pode não funcionar corretamente.")
    df_map_data_base['lat'] = None
    df_map_data_base['lon'] = None
except Exception as e:
    st.error(f"Erro ao carregar ou processar '{lat_lon_file_path}': {e}. O mapa pode não funcionar corretamente.")
    df_map_data_base['lat'] = None
    df_map_data_base['lon'] = None

# Total de homens/mulheres por município
sexo_counts = (
    df[df['ADAI_ID8'].isin(['Homem', 'Mulher'])]
    .groupby(['ADAI_CT4', 'ADAI_ID8']).size().unstack(fill_value=0)
    .reset_index().rename(columns={'ADAI_CT4': 'nome'})
)
sexo_counts['nome_padrao'] = sexo_counts['nome'].apply(padroniza_nome) # Padroniza aqui também
df_map_data_base = df_map_data_base.merge(sexo_counts, on='nome_padrao', how='left', suffixes=('', '_sexo'))

if 'Homem' not in df_map_data_base.columns or 'Homem_sexo' in df_map_data_base.columns:
    df_map_data_base['Homem'] = df_map_data_base.get('Homem_sexo', df_map_data_base.get('Homem', 0))
if 'Mulher' not in df_map_data_base.columns or 'Mulher_sexo' in df_map_data_base.columns:
    df_map_data_base['Mulher'] = df_map_data_base.get('Mulher_sexo', df_map_data_base.get('Mulher', 0))
df_map_data_base = df_map_data_base.drop(columns=[col for col in df_map_data_base.columns if col.endswith('_sexo')], errors='ignore')


df_map_data_base['Homem'] = pd.to_numeric(df_map_data_base['Homem'], errors='coerce').fillna(0)
df_map_data_base['Mulher'] = pd.to_numeric(df_map_data_base['Mulher'], errors='coerce').fillna(0)

df_map_data_base['Pct_Homens'] = (df_map_data_base['Homem'] / df_map_data_base['Total Respondentes'].replace(0, pd.NA) * 100).fillna(0).round(1)
df_map_data_base['Pct_Mulheres'] = (df_map_data_base['Mulher'] / df_map_data_base['Total Respondentes'].replace(0, pd.NA) * 100).fillna(0).round(1)

# Profissão mais comum por município (usa ADAI_ID12)
profissao_pred = (
    df.groupby('ADAI_CT4')['ADAI_ID12']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ADAI_ID12': 'Profissao_Predominante'})
)
profissao_pred['nome_padrao'] = profissao_pred['nome'].apply(padroniza_nome)
df_map_data_base = df_map_data_base.merge(profissao_pred[['nome_padrao', 'Profissao_Predominante']], on='nome_padrao', how='left')


# Escolaridade mais comum (usa ID11)
escolaridade_pred = (
    df.groupby('ADAI_CT4')['ID11']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID11': 'Escolaridade_Predominante'})
)
escolaridade_pred['nome_padrao'] = escolaridade_pred['nome'].apply(padroniza_nome)
df_map_data_base = df_map_data_base.merge(escolaridade_pred[['nome_padrao', 'Escolaridade_Predominante']], on='nome_padrao', how='left')

# Religião mais comum (usa ID12)
religiao_pred = (
    df.groupby('ADAI_CT4')['ID12']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID12': 'Religiao_Predominante'})
)
religiao_pred['nome_padrao'] = religiao_pred['nome'].apply(padroniza_nome)
df_map_data_base = df_map_data_base.merge(religiao_pred[['nome_padrao', 'Religiao_Predominante']], on='nome_padrao', how='left')


# Povo tradicional: % de respondentes por município
povo_pct = (
    df[df['PCT0'] == 'Sim']
    .groupby('ADAI_CT4').size() / df.groupby('ADAI_CT4').size()
).mul(100).round(1).reset_index(name='Pct_Povo_Tradicional')
# CORREÇÃO AQUI: Renomear 'ADAI_CT4' para 'nome'
povo_pct = povo_pct.rename(columns={'ADAI_CT4': 'nome'})
povo_pct['nome_padrao'] = povo_pct['nome'].apply(padroniza_nome)
df_map_data_base = df_map_data_base.merge(povo_pct[['nome_padrao', 'Pct_Povo_Tradicional']], on='nome_padrao', how='left')
df_map_data_base['Pct_Povo_Tradicional'] = df_map_data_base['Pct_Povo_Tradicional'].fillna(0)


# Deficiência: % de respondentes com deficiência (assumindo ID10 para Deficiência)
if 'ID10' in df.columns:
    def_pct_data = df[df['ID10'].isin(['Sim', 'sim'])]
    if not def_pct_data.empty:
        total_respondents_per_mun = df.groupby('ADAI_CT4').size()
        def_pct = (
            def_pct_data.groupby('ADAI_CT4').size() / total_respondents_per_mun
        ).mul(100).round(1).reset_index(name='Pct_Deficiencia')
        # CORREÇÃO AQUI: Renomear 'ADAI_CT4' para 'nome'
        def_pct = def_pct.rename(columns={'ADAI_CT4': 'nome'})
        def_pct['nome_padrao'] = def_pct['nome'].apply(padroniza_nome)
        df_map_data_base = df_map_data_base.merge(def_pct[['nome_padrao', 'Pct_Deficiencia']], on='nome_padrao', how='left')
    else:
        df_map_data_base['Pct_Deficiencia'] = 0
else:
    df_map_data_base['Pct_Deficiencia'] = 0
df_map_data_base['Pct_Deficiencia'] = df_map_data_base['Pct_Deficiencia'].fillna(0) # Garante fillna após merge


# Raça/cor: mais comum por município
raca_pred = (
    df.groupby('ADAI_CT4')['ID7']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID7': 'Raca_Predominante'})
)
raca_pred['nome_padrao'] = raca_pred['nome'].apply(padroniza_nome)
df_map_data_base = df_map_data_base.merge(raca_pred[['nome_padrao', 'Raca_Predominante']], on='nome_padrao', how='left')


# --- Remover colunas duplicadas de 'nome' (se ocorrerem) e garantir valores numéricos ---
# Removido df_map_data_base.loc[:,~df_map_data_base.columns.duplicated()] daqui
# Pois colunas com sufixo _latlon, _sexo etc. serao tratadas no merge/fillna

numeric_cols_for_map = ['Total Respondentes', 'Homem', 'Mulher', 'Pct_Homens', 'Pct_Mulheres', 'Pct_Povo_Tradicional', 'Pct_Deficiencia']
for col in numeric_cols_for_map:
    if col in df_map_data_base.columns:
        df_map_data_base[col] = pd.to_numeric(df_map_data_base[col], errors='coerce').fillna(0)
    else:
        df_map_data_base[col] = 0

# ========== TÍTULO DA PÁGINA E DESCRIÇÃO ==========
st.markdown("<h1 style='text-align: center; color: #264653; font-size: 2.5em;'>Visualização Geográfica dos Dados da Amostra</h1>", unsafe_allow_html=True)
st.markdown("""
<p class='intro-text-paragraph'>
Explore a distribuição espacial dos respondentes e de características demográficas importantes nos municípios da área de estudo. <br>
Os mapas exibem padrões observados **dentro da amostra de respondentes**, e não devem ser generalizados diretamente para toda a população ou para a totalidade dos municípios sem uma análise estatística inferencial adequada.
</p>
""", unsafe_allow_html=True)

# ========== FILTROS GLOBAIS: MUNICÍPIO E MÊS/ANO ==========
col_filter_mun, col_filter_mes_ano = st.columns(2)

with col_filter_mun:
    municipio_opcao = st.selectbox(
        "Filtrar por Município:",
        options=['Todos'] + sorted(df_map_data_base['nome'].dropna().unique().tolist()),
        index=0,
        key="map_municipio_filter"
    )

with col_filter_mes_ano:
    if 'Mes_Ano' in df.columns:
        all_mes_anos = sorted(df['Mes_Ano'].dropna().unique().tolist())
        selected_mes_ano = st.selectbox(
            "Filtrar por Mês/Ano:",
            options=['Todos'] + all_mes_anos,
            index=0,
            key="map_mes_ano_filter"
        )
    else:
        st.info("Coluna 'Mes_Ano' não disponível no DataFrame para filtro temporal.")
        selected_mes_ano = 'Todos'

# --- Aplica filtros globais ao DataFrame de base para o mapa ---
df_map_vis_filtered_temporal = df_map_data_base.copy() # Inicia com a base completa

if 'Mes_Ano' in df.columns and selected_mes_ano != 'Todos':
    df_filtered_by_mes_ano = df[df['Mes_Ano'] == selected_mes_ano]

    # Recalcula as contagens e predominâncias para o período selecionado
    df_respondents_mes_ano_temp = df_filtered_by_mes_ano.groupby('ADAI_CT4').size().reset_index(name='Total Respondentes_temp')
    df_respondents_mes_ano_temp['nome_padrao'] = df_respondents_mes_ano_temp['ADAI_CT4'].apply(padroniza_nome)
    
    sexo_counts_temporal_temp = (
        df_filtered_by_mes_ano[df_filtered_by_mes_ano['ADAI_ID8'].isin(['Homem', 'Mulher'])]
        .groupby(['ADAI_CT4', 'ADAI_ID8']).size().unstack(fill_value=0)
        .reset_index()
    )
    sexo_counts_temporal_temp['nome_padrao'] = sexo_counts_temporal_temp['ADAI_CT4'].apply(padroniza_nome)


    # Merge e atualização do df_map_vis_filtered_temporal
    # Usar df_map_data_base como base e mergear os dados temporais nele, substituindo as colunas
    
    # Resetar 'Total Respondentes' para 0 antes do merge, para que o fillna funcione corretamente
    df_map_vis_filtered_temporal['Total Respondentes'] = 0
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.merge(
        df_respondents_mes_ano_temp[['nome_padrao', 'Total Respondentes_temp']],
        on='nome_padrao',
        how='left'
    )
    df_map_vis_filtered_temporal['Total Respondentes'] = df_map_vis_filtered_temporal['Total Respondentes_temp'].fillna(0)
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.drop(columns=['Total Respondentes_temp'], errors='ignore')

    # Para Homem/Mulher
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.merge(
        sexo_counts_temporal_temp[['nome_padrao', 'Homem', 'Mulher']],
        on='nome_padrao',
        how='left',
        suffixes=('_base_temp', '_temp_calc')
    )
    # Atualiza as colunas de contagem e calcula as porcentagens com base nos novos totais
    df_map_vis_filtered_temporal['Homem'] = pd.to_numeric(df_map_vis_filtered_temporal['Homem_temp_calc'].fillna(0), errors='coerce')
    df_map_vis_filtered_temporal['Mulher'] = pd.to_numeric(df_map_vis_filtered_temporal['Mulher_temp_calc'].fillna(0), errors='coerce')
    df_map_vis_filtered_temporal['Pct_Homens'] = (df_map_vis_filtered_temporal['Homem'] / df_map_vis_filtered_temporal['Total Respondentes'].replace(0, pd.NA) * 100).fillna(0).round(1)
    df_map_vis_filtered_temporal['Pct_Mulheres'] = (df_map_vis_filtered_temporal['Mulher'] / df_map_vis_filtered_temporal['Total Respondentes'].replace(0, pd.NA) * 100).fillna(0).round(1)
    # Remover colunas temporárias
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.drop(columns=[col for col in df_map_vis_filtered_temporal.columns if col.endswith('_temp_calc') or col.endswith('_base_temp')], errors='ignore')

    # Repetir padrão para outras colunas predominantes e percentuais
    for col_orig, col_pred in [('ADAI_ID12', 'Profissao_Predominante'), ('ID11', 'Escolaridade_Predominante'),
                                ('ID12', 'Religiao_Predominante'), ('ID7', 'Raca_Predominante')]:
        temp_pred = (
            df_filtered_by_mes_ano.groupby('ADAI_CT4')[col_orig]
            .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
            .reset_index()
        )
        temp_pred['nome_padrao'] = temp_pred['ADAI_CT4'].apply(padroniza_nome)
        
        # Merge para atualizar a coluna de predominância
        df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.merge(
            temp_pred[['nome_padrao', col_orig]].rename(columns={col_orig: col_pred + '_temp'}),
            on='nome_padrao',
            how='left'
        )
        df_map_vis_filtered_temporal[col_pred] = df_map_vis_filtered_temporal[col_pred + '_temp'].fillna(df_map_vis_filtered_temporal[col_pred])
        df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.drop(columns=[col_pred + '_temp'], errors='ignore')

    # Para Pct_Povo_Tradicional e Pct_Deficiencia
    povo_pct_temporal_temp = (
        df_filtered_by_mes_ano[df_filtered_by_mes_ano['PCT0'] == 'Sim']
        .groupby('ADAI_CT4').size() / df_filtered_by_mes_ano.groupby('ADAI_CT4').size()
    ).mul(100).round(1).reset_index(name='Pct_Povo_Tradicional_temp')
    povo_pct_temporal_temp['nome_padrao'] = povo_pct_temporal_temp['ADAI_CT4'].apply(padroniza_nome)
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.merge(povo_pct_temporal_temp[['nome_padrao', 'Pct_Povo_Tradicional_temp']], on='nome_padrao', how='left')
    df_map_vis_filtered_temporal['Pct_Povo_Tradicional'] = df_map_vis_filtered_temporal['Pct_Povo_Tradicional_temp'].fillna(0)
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.drop(columns=['Pct_Povo_Tradicional_temp'], errors='ignore')


    if 'ID10' in df_filtered_by_mes_ano.columns:
        def_pct_data_temporal_temp = df_filtered_by_mes_ano[df_filtered_by_mes_ano['ID10'].isin(['Sim', 'sim'])]
        if not def_pct_data_temporal_temp.empty:
            total_respondents_per_mun_temporal_temp = df_filtered_by_mes_ano.groupby('ADAI_CT4').size()
            def_pct_temporal_temp = (
                def_pct_data_temporal_temp.groupby('ADAI_CT4').size() / total_respondents_per_mun_temporal_temp
            ).mul(100).round(1).reset_index(name='Pct_Deficiencia_temp')
            def_pct_temporal_temp['nome_padrao'] = def_pct_temporal_temp['ADAI_CT4'].apply(padroniza_nome)
            df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.merge(def_pct_temporal_temp[['nome_padrao', 'Pct_Deficiencia_temp']], on='nome_padrao', how='left')
            df_map_vis_filtered_temporal['Pct_Deficiencia'] = df_map_vis_filtered_temporal['Pct_Deficiencia_temp'].fillna(0)
            df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.drop(columns=['Pct_Deficiencia_temp'], errors='ignore')
        else:
            df_map_vis_filtered_temporal['Pct_Deficiencia'] = df_map_vis_filtered_temporal['Pct_Deficiencia'].fillna(0) # Mantém valor anterior se vazio no filtro
    else:
        df_map_vis_filtered_temporal['Pct_Deficiencia'] = df_map_vis_filtered_temporal['Pct_Deficiencia'].fillna(0) # Mantém valor anterior se coluna não existe

    # Limpar colunas duplicadas que podem surgir de merges (se algum suffix não for tratado acima)
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.loc[:,~df_map_vis_filtered_temporal.columns.duplicated()]
    # Remover colunas base que podem ter sido criadas por merges
    df_map_vis_filtered_temporal = df_map_vis_filtered_temporal.loc[:, ~df_map_vis_filtered_temporal.columns.str.endswith('_base')]


else: # Se o filtro é 'Todos' ou 'Mes_Ano' não existe, usa a base completa
    df_map_vis_filtered_temporal = df_map_data_base.copy()


df_map_vis = df_map_vis_filtered_temporal if municipio_opcao == 'Todos' else df_map_vis_filtered_temporal[df_map_vis_filtered_temporal['nome'] == municipio_opcao]

lat_center_map = df_map_vis["lat"].mean() if not df_map_vis["lat"].isna().all() else -19.5
lon_center_map = df_map_vis["lon"].mean() if not df_map_vis["lon"].isna().all() else -40.5
zoom_map = 8 if municipio_opcao != 'Todos' and not df_map_vis.empty else 6


# ========== TRÊS ABAS: MAPA DE RESPONDENTES, MAPA DE DENSIDADE, TABELA (agora 4 abas) ==========
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa de Respondentes", "📊 Mapa de Densidade Demográfica", "📋 Tabela Detalhada por Município", "📈 Análise Estatística Adicional"])


with tab1: # --- ABA 1: MAPA DE RESPONDENTES ---
    st.markdown("### Distribuição de Respondentes por Município")
    st.info("Este mapa exibe a localização de respondentes. O **tamanho do círculo** representa o total de respondentes na amostra. Cores mais claras indicam menos respondentes, cores mais escuras indicam mais. Passe o mouse sobre os pontos para mais detalhes.")

    if 'lat' in df_map_vis.columns and 'lon' in df_map_vis.columns and not df_map_vis[['lat', 'lon']].isna().all().all():
        try:
            fig_map_respondents = px.scatter_mapbox(
                df_map_vis,
                lat="lat",
                lon="lon",
                size="Total Respondentes",
                size_max=60,
                color="Total Respondentes",
                color_continuous_scale=px.colors.sequential.Plasma,
                opacity=0.85,
                hover_name="nome",
                hover_data={
                    "Total Respondentes": True,
                    "Homem": True, "Mulher": True,
                    "Pct_Mulheres": ":.1f}%", "Pct_Homens": ":.1f}%",
                    "Profissao_Predominante": True,
                    "Escolaridade_Predominante": True,
                    "Religiao_Predominante": True,
                    "Raca_Predominante": True,
                    "lat": False, "lon": False
                },
                mapbox_style="carto-positron",
                zoom=zoom_map,
                center={"lat": lat_center_map, "lon": lon_center_map}
            )
            fig_map_respondents.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0},
                height=600,
                title=f"<b>Total de Respondentes por Município na Amostra {f'(Mês/Ano: {selected_mes_ano})' if selected_mes_ano != 'Todos' else ''}</b>",
                coloraxis_colorbar=dict(title="Total<br>Respondentes")
            )
            st.plotly_chart(fig_map_respondents, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar o Mapa de Respondentes: {e}")
    else:
        st.warning("Não há coordenadas (lat/lon) dos municípios no DataFrame para plotar pontos no mapa. Por favor, verifique o arquivo 'municipios_es_lat_lon.csv'.")

with tab2: # --- ABA 2: MAPA DE DENSIDADE DEMOGRÁFICA ---
    st.markdown("### Mapa de Densidade por Característica Demográfica")
    st.info("""
    Este mapa exibe a **densidade de características demográficas** por município na amostra.
    Selecione a variável desejada abaixo para visualizar sua distribuição geográfica.
    **A cor de cada município** indica a porcentagem ou a categoria predominante da característica selecionada.
    """)

    geojson_file_path = os.path.join(root_dir, 'data', 'municipios_es.json')
    geojson_data = None
    try:
        with open(geojson_file_path, encoding='utf-8') as f:
            geojson_data = json.load(f)
            
       # === APLICAR PADRONIZAÇÃO NO GEOJSON AQUI (suporte a vários nomes de campo) ===
        if geojson_data and 'features' in geojson_data:
            possible_fields = ['NM_MUNICIP', 'NM_MUNICIPIO', 'NM_MUN', 'name']
            for feat in geojson_data['features']:
                # tenta cada campo até encontrar o nome do município
                raw_name = None
                for fld in possible_fields:
                    if fld in feat['properties']:
                        raw_name = feat['properties'][fld]
                        break
                # se não achar, marca como string vazia para evitar N/A_NOME
                feat['properties']['NM_MUNICIP_PADRAO'] = padroniza_nome(raw_name) if raw_name else ""
                
    except FileNotFoundError:
        st.error(f"Erro: Arquivo GeoJSON '{geojson_file_path}' não encontrado. O mapa de densidade não pode ser gerado.")
    except json.JSONDecodeError:
        st.error(f"Erro: Arquivo GeoJSON '{geojson_file_path}' não é um JSON válido.")

    if geojson_data:
        density_var_options = {
            'Total Respondentes': 'Total de Respondentes',
            'Homem': 'Homens (Contagem)',
            'Mulher': 'Mulheres (Contagem)',
            'Pct_Homens': '% de Homens',
            'Pct_Mulheres': '% de Mulheres',
            'Pct_Povo_Tradicional': '% Povo Tradicional',
            'Pct_Deficiencia': '% Pessoas com Deficiência',
            'Profissao_Predominante': 'Profissão Predominante',
            'Escolaridade_Predominante': 'Escolaridade Predominante',
            'Religiao_Predominante': 'Religião Predominante',
            'Raca_Predominante': 'Raça/Cor Predominante'
        }

        available_density_var_options = {k: v for k, v in density_var_options.items() if k in df_map_vis.columns}

        if not available_density_var_options:
            st.warning("Nenhuma variável demográfica calculada para exibir no mapa de densidade.")
        else:
            selected_density_var_code = st.selectbox(
                "Selecione a Variável para Densidade:",
                list(available_density_var_options.keys()),
                format_func=lambda x: available_density_var_options[x],
                key="density_var_selector"
            )

            if selected_density_var_code:
                # --- featureidkey correto e location padronizado ---
                #locations='nome_padrao' é a coluna do df_map_vis que tem o nome padronizado
                #featureidkey='properties.NM_MUNICIP_PADRAO' é a propriedade no GeoJSON que tem o nome padronizado
                geojson_feature_id_key = "properties.NM_MUNICIP_PADRAO"

                if selected_density_var_code in ['Total Respondentes', 'Homem', 'Mulher', 'Pct_Homens', 'Pct_Mulheres', 'Pct_Povo_Tradicional', 'Pct_Deficiencia']:
                    fig_density = px.choropleth_mapbox(
                        df_map_vis,
                        geojson=geojson_data,
                        locations='nome_padrao', # Usa a coluna padronizada do DataFrame
                        featureidkey=geojson_feature_id_key,
                        color=selected_density_var_code,
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=(df_map_vis[selected_density_var_code].min(), df_map_vis[selected_density_var_code].max()),
                        mapbox_style="carto-positron",
                        zoom=zoom_map,
                        center={"lat": lat_center_map, "lon": lon_center_map},
                        opacity=0.7,
                        hover_name="nome", # Mostra o nome original, amigável
                        hover_data={
                            selected_density_var_code: True,
                            "Total Respondentes": True,
                            "Homem": True, "Mulher": True,
                            "Pct_Mulheres": ":.1f}%", "Pct_Homens": ":.1f}%",
                            "Profissao_Predominante": True,
                            "Escolaridade_Predominante": True,
                            "Religiao_Predominante": True,
                            "Raca_Predominante": True,
                            "lat": False, "lon": False
                        }
                    )
                    fig_density.update_layout(
                        margin={"r":0,"t":40,"l":0,"b":0},
                        height=600,
                        title=f"<b>Densidade de {available_density_var_options[selected_density_var_code]} por Município na Amostra {f'(Mês/Ano: {selected_mes_ano})' if selected_mes_ano != 'Todos' else ''}</b>",
                        coloraxis_colorbar=dict(title=available_density_var_options[selected_density_var_code])
                    )
                else:
                    df_density_categorical = df_map_vis.dropna(subset=[selected_density_var_code])
                    if not df_density_categorical.empty:
                        fig_density = px.choropleth_mapbox(
                            df_density_categorical,
                            geojson=geojson_data,
                            locations='nome_padrao', # Usa a coluna padronizada do DataFrame
                            featureidkey=geojson_feature_id_key,
                            color=selected_density_var_code,
                            color_discrete_sequence=px.colors.qualitative.Plotly,
                            mapbox_style="carto-positron",
                            zoom=zoom_map,
                            center={"lat": lat_center_map, "lon": lon_center_map},
                            opacity=0.7,
                            hover_name="nome", # Mostra o nome original, amigável
                            hover_data={
                                selected_density_var_code: True,
                                "Total Respondentes": True,
                                "Homem": True, "Mulher": True,
                                "Pct_Mulheres": ":.1f}%", "Pct_Homens": ":.1f}%",
                                "Profissao_Predominante": True,
                                "Escolaridade_Predominante": True,
                                "Religiao_Predominante": True,
                                "Raca_Predominante": True,
                                "lat": False, "lon": False
                            }
                        )

                        fig_density.update_layout(
                            margin={"r":0,"t":40,"l":0,"b":0},
                            height=600,
                            title=f"<b>Predominância de {available_density_var_options[selected_density_var_code]} por Município na Amostra {f'(Mês/Ano: {selected_mes_ano})' if selected_mes_ano != 'Todos' else ''}</b>",
                            legend_title_text=available_density_var_options[selected_density_var_code]
                        )
                    else:
                        st.warning(f"Não há dados válidos para a variável '{available_density_var_options[selected_density_var_code]}' para gerar o mapa de densidade categórico.")
                        fig_density = None

                if fig_density:
                    st.plotly_chart(fig_density, use_container_width=True)
                    st.caption(f"Mapa: Exibe a distribuição geográfica de '{available_density_var_options[selected_density_var_code]}' na amostra. A cor indica a intensidade ou predominância da característica no município. Passe o mouse para detalhes.")
                else:
                    st.info("Selecione uma variável para visualizar o mapa de densidade, ou verifique se o arquivo GeoJSON foi carregado.")
            else:
                st.info("Selecione uma variável demográfica para visualizar o mapa de densidade.")
    else:
        st.warning("O arquivo GeoJSON dos municípios não foi carregado, o mapa de densidade não pode ser exibido.")

with tab3: # --- ABA 3: TABELA DETALHADA POR MUNICÍPIO ---
    st.markdown("### Detalhes Demográficos por Município")
    st.info("Esta tabela apresenta um resumo das principais características demográficas dos respondentes em cada município da amostra. Clique nos cabeçalhos para ordenar os dados.")

    cols_to_display_table = {
        'nome': 'Município',
        'Total Respondentes': 'Total Respondentes',
        'Homem': 'Homens (Contagem)',
        'Mulher': 'Mulheres (Contagem)',
        'Pct_Mulheres': '% Mulheres',
        'Pct_Homens': '% Homens',
        'Profissao_Predominante': 'Profissão Mais Comum',
        'Escolaridade_Predominante': 'Escolaridade Mais Comum',
        'Religiao_Predominante': 'Religião Mais Comum',
        'Raca_Predominante': 'Raça/Cor Mais Comum',
        'Pct_Povo_Tradicional': '% Povo Tradicional',
        'Pct_Deficiencia': '% PcD'
    }

    final_cols_for_table = {k: v for k, v in cols_to_display_table.items() if k in df_map_vis.columns}

    st.dataframe(
        df_map_vis[list(final_cols_for_table.keys())].rename(columns=final_cols_for_table),
        use_container_width=True, hide_index=True
    )
    st.caption("Dados da amostra, calculados por município.")

    st.download_button(
        label="📥 Baixar Tabela Detalhada por Município (CSV)",
        data=df_map_vis.to_csv(index=False, encoding='utf-8'),
        file_name="municipios_respondentes_detalhes_amostra.csv",
        key="download_map_data_csv"
    )

with tab4: # --- ABA 4: ANÁLISE ESTATÍSTICA ADICIONAL ---
    st.markdown("### Análise Estatística Adicional por Município")
    st.info("Explore as características estatísticas de variáveis numéricas dos municípios na amostra. Os cálculos são baseados nos dados visíveis após os filtros de Município e Mês/Ano.")

    statistical_vars_options = {
        'Total Respondentes': 'Total de Respondentes',
        'Homem': 'Homens (Contagem)',
        'Mulher': 'Mulheres (Contagem)',
        'Pct_Homens': '% de Homens',
        'Pct_Mulheres': '% de Mulheres',
        'Pct_Povo_Tradicional': '% Povo Tradicional',
        'Pct_Deficiencia': '% Pessoas com Deficiência'
    }
    
    available_statistical_vars = {k: v for k, v in statistical_vars_options.items() if k in df_map_vis.columns and pd.api.types.is_numeric_dtype(df_map_vis[k])}

    if not available_statistical_vars:
        st.warning("Nenhuma variável numérica disponível para análise estatística adicional. Verifique seus dados ou filtros.")
    else:
        selected_stats_var_code = st.selectbox(
            "Selecione a Variável Numérica para Análise Estatística:",
            list(available_statistical_vars.keys()),
            format_func=lambda x: available_statistical_vars[x],
            key="stats_var_selector"
        )

        if selected_stats_var_code:
            st.markdown(f"#### Estatísticas Descritivas para '{available_statistical_vars[selected_stats_var_code]}'")
            
            stats_data = df_map_vis[selected_stats_var_code].dropna()
            
            if not stats_data.empty:
                st.dataframe(stats_data.describe().to_frame(), use_container_width=True)
                st.caption("Estatísticas: Média, desvio padrão, mínimo, máximo e quartis da variável para os municípios visíveis na amostra.")

                st.divider() # <--- Adicione esta linha
                st.markdown(f"#### Boxplot de '{available_statistical_vars[selected_stats_var_code]}'")
                fig_boxplot = px.box(
                    df_map_vis,
                    y=selected_stats_var_code,
                    title=f"Boxplot da {available_statistical_vars[selected_stats_var_code]} por Município na Amostra",
                    points="all",
                    hover_data=['nome']
                )
                fig_boxplot.update_layout(title_x=0.5, yaxis_title=available_statistical_vars[selected_stats_var_code])
                st.plotly_chart(fig_boxplot, use_container_width=True)
                st.caption("Boxplot: A caixa representa o intervalo interquartil (IQR), a linha central é a mediana. Pontos fora da caixa e 'whiskers' são potenciais outliers.")

                st.divider() # <--- Adicione esta linha
                st.markdown(f"#### Identificação de Outliers para '{available_statistical_vars[selected_stats_var_code]}'")
                if len(stats_data) >= 4:
                    Q1 = stats_data.quantile(0.25)
                    Q3 = stats_data.quantile(0.75)
                    IQR = Q3 - Q1
                    upper_bound = Q3 + 1.5 * IQR
                    lower_bound = Q1 - 1.5 * IQR

                    outliers = df_map_vis[(df_map_vis[selected_stats_var_code] < lower_bound) | (df_map_vis[selected_stats_var_code] > upper_bound)]
                    
                    outliers = outliers[
                        (outliers[selected_stats_var_code] != 0) | ((outliers[selected_stats_var_code] == 0) & (lower_bound < 0))
                    ].dropna(subset=[selected_stats_var_code])

                    if not outliers.empty:
                        st.warning("Os seguintes municípios podem ser considerados outliers para esta variável:")
                        for index, row in outliers.iterrows():
                            st.write(f"- **{row['nome']}**: {row[selected_stats_var_code]:.1f}")
                        st.caption("Outliers: Municípios cujos valores para a variável selecionada estão significativamente fora da maioria da distribuição (método do Intervalo Interquartil - IQR).")
                    else:
                        st.info("Nenhum outlier identificado para esta variável nos municípios visíveis (método IQR).")
                else:
                    st.info("Dados insuficientes para calcular outliers (mínimo de 4 pontos necessários para quartis).")
                
                st.divider() # <--- Adicione esta linha
                st.markdown(f"#### Top 5 e Bottom 5 para '{available_statistical_vars[selected_stats_var_code]}'")
                df_sorted = df_map_vis.sort_values(by=selected_stats_var_code, ascending=False).dropna(subset=[selected_stats_var_code])
                df_sorted_asc = df_map_vis.sort_values(by=selected_stats_var_code, ascending=True).dropna(subset=[selected_stats_var_code])

                col_top5, col_bottom5 = st.columns(2)
                
                with col_top5:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #f0fff0; /* Verde bem clarinho para o topo */
                            padding: 15px;
                            border-radius: 10px;
                            border: 1px solid #d4edda; /* Borda sutil */
                            margin-bottom: 10px;
                        ">
                            <h5 style="color: #28a745; margin-top: 0px; margin-bottom: 10px;">🏆 Top 5 Municípios</h5>
                        """
                        , unsafe_allow_html=True
                    )
                    if not df_sorted.head(5).empty:
                         for i, (index, row) in enumerate(df_sorted.head(5).iterrows()):
                            st.markdown(f"<p style='margin-bottom: 5px; font-size: 1.05em;'><b>{i+1}. {row['nome']}</b>: <span style='color:green;font-weight:bold;'>{row[selected_stats_var_code]:.1f}</span></p>", unsafe_allow_html=True)
                    else:
                        st.info("Não há dados suficientes para exibir o Top 5.")
                    st.markdown("</div>", unsafe_allow_html=True) # Fecha a div do card Top 5

                with col_bottom5:
                     st.markdown(
                        f"""
                        <div style="
                            background-color: #fff0f0; /* Vermelho bem clarinho para o bottom */
                            padding: 15px;
                            border-radius: 10px;
                            border: 1px solid #f5c6cb; /* Borda sutil */
                            margin-bottom: 10px;
                        ">
                            <h5 style="color: #dc3545; margin-top: 0px; margin-bottom: 10px;">📉 5 Últimos Municípios</h5>
                        """
                        , unsafe_allow_html=True
                     )
                     if not df_sorted_asc.head(5).empty:
                        for i, (index, row) in enumerate(df_sorted_asc.head(5).iterrows()):
                            st.markdown(f"<p style='margin-bottom: 5px; font-size: 1.05em;'><b>{i+1}. {row['nome']}</b>: <span style='color:red;font-weight:bold;'>{row[selected_stats_var_code]:.1f}</span></p>", unsafe_allow_html=True)
                     else:
                       st.info("Não há dados suficientes para exibir o Bottom 5.")
                     st.markdown("</div>", unsafe_allow_html=True) # Fecha a div do card Bottom 5

                st.caption("Top/Bottom 5: Municípios com os maiores e menores valores para a variável selecionada. As caixas coloridas ajudam a visualizar rapidamente os grupos.")

                st.markdown("---")
                st.markdown("#### Comparação Detalhada entre Dois Municípios")
                
                all_mun_names = sorted(df_map_vis['nome'].dropna().unique().tolist())
                if len(all_mun_names) >= 2:
                    col_mun1, col_mun2 = st.columns(2)
                    with col_mun1:
                        mun_compare_1 = st.selectbox(
                            "Selecione o 1º Município:",
                            options=all_mun_names,
                            key="mun_compare_1"
                        )
                    with col_mun2:
                        options_mun2 = [m for m in all_mun_names if m != mun_compare_1]
                        if not options_mun2:
                            st.warning("Não há outro município para comparar.")
                            mun_compare_2 = None
                        else:
                            mun_compare_2 = st.selectbox(
                                "Selecione o 2º Município:",
                                options=options_mun2,
                                key="mun_compare_2"
                            )
                    
                    if mun_compare_1 and mun_compare_2:
                        data_mun1 = df_map_vis[df_map_vis['nome'] == mun_compare_1].iloc[0]
                        data_mun2 = df_map_vis[df_map_vis['nome'] == mun_compare_2].iloc[0]

                        compare_df = pd.DataFrame({
                            'Característica': [available_statistical_vars[selected_stats_var_code]],
                            mun_compare_1: [data_mun1[selected_stats_var_code]],
                            mun_compare_2: [data_mun2[selected_stats_var_code]]
                        }).set_index('Característica')
                        
                        st.dataframe(compare_df)

                        fig_compare = px.bar(
                            x=[mun_compare_1, mun_compare_2],
                            y=[data_mun1[selected_stats_var_code], data_mun2[selected_stats_var_code]],
                            labels={'x': 'Município', 'y': available_statistical_vars[selected_stats_var_code]},
                            title=f"Comparação de '{available_statistical_vars[selected_stats_var_code]}' entre {mun_compare_1} e {mun_compare_2}",
                            color_discrete_sequence=px.colors.qualitative.Plotly
                        )
                        fig_compare.update_layout(title_x=0.5)
                        st.plotly_chart(fig_compare, use_container_width=True)
                    else:
                        st.info("Selecione dois municípios para comparação.")
                else: 
                    st.info("Não há municípios suficientes para comparação (mínimo de 2) após os filtros aplicados.")

            else: 
                st.info("Não há dados válidos para a variável selecionada nos municípios visíveis para análise estatística.")
        else: 
            st.info("Por favor, selecione uma variável numérica para iniciar a análise estatística adicional.")

st.markdown("---") 

# ========== ANÁLISE TEMPORAL DO MUNICÍPIO SELECIONADO ==========
if municipio_opcao != 'Todos' and 'CT2' in df.columns and 'ADAI_CT4' in df.columns:
    st.markdown(f"<h2 style='text-align: center; color: #264653;'>Evolução Temporal de Respondentes em {municipio_opcao}</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <p class='intro-text-paragraph'>
    Este gráfico de linha mostra a evolução do número de respondentes ao longo do tempo para o município de **{municipio_opcao}**, com base na amostra.
    </p>
    """, unsafe_allow_html=True)

    df_temporal_mun = df[df['ADAI_CT4'] == municipio_opcao].dropna(subset=['Mes_Ano'])
    df_temporal_counts = df_temporal_mun.groupby('Mes_Ano').size().reset_index(name='Total Respondentes')

    if not df_temporal_counts.empty:
        fig_temporal_mun = px.line(
            df_temporal_counts,
            x='Mes_Ano',
            y='Total Respondentes',
            title=f'Respondentes por Mês/Ano em {municipio_opcao} na Amostra',
            labels={'Mes_Ano': 'Mês/Ano', 'Total Respondentes': 'Número de Respondentes'},
            markers=True,
            line_shape='linear',
            color_discrete_sequence=[px.colors.qualitative.Plotly[0]]
        )
        fig_temporal_mun.update_layout(
            xaxis_title="Mês/Ano",
            yaxis_title="Número de Respondentes",
            title_x=0.5,
            height=400
        )
        st.plotly_chart(fig_temporal_mun, use_container_width=True)
        st.caption(f"Gráfico de Linha: Exibe a contagem de respondentes do município de {municipio_opcao} em cada mês/ano na amostra.")

    else:
        st.info(f"Não há dados temporais para o município de {municipio_opcao} na amostra.")
elif municipio_opcao == 'Todos':
    st.markdown("---")
    st.info("Selecione um município específico no filtro acima para visualizar sua evolução temporal detalhada.")
