import streamlit as st
import pandas as pd
import plotly.express as px

from utils.session import ensure_session_data
ensure_session_data()

df = st.session_state['df']
st.header("Visualização por Mapa")

st.info("Este mapa exibe a distribuição espacial dos municípios onde há respondentes. O tamanho do círculo indica o número de respondentes. Passe o mouse sobre os pontos para mais detalhes.")

st.markdown("---")

# Posição central do ES
center = [-19.5, -40.5]

# --- Prepara DataFrame de municípios e total de respondentes
df_map_data = df.groupby('ADAI_CT4').size().reset_index(name='Total Respondentes')
df_map_data = df_map_data.rename(columns={'ADAI_CT4': 'nome'}) 

# Merge com lat/lon
lat_lon_df = pd.read_csv('data/municipios_es_lat_lon.csv', sep=';', encoding='utf-8')
df_map_data = df_map_data.merge(lat_lon_df, on='nome', how='left')

# Total de homens/mulheres por município
sexo_counts = (
    df[df['ADAI_ID8'].isin(['Homem', 'Mulher'])]
    .groupby(['ADAI_CT4', 'ADAI_ID8']).size().unstack(fill_value=0)
    .reset_index().rename(columns={'ADAI_CT4': 'nome'})
)
df_map_data = df_map_data.merge(sexo_counts, on='nome', how='left')

df_map_data['Pct_Homens'] = (df_map_data.get('Homem', 0) / df_map_data['Total Respondentes'] * 100).round(1)
df_map_data['Pct_Mulheres'] = (df_map_data.get('Mulher', 0) / df_map_data['Total Respondentes'] * 100).round(1)

# Profissão mais comum por município
profissao_pred = (
    df.groupby('ADAI_CT4')['ADAI_ID12']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ADAI_ID12': 'Profissao_Predominante'})
)
df_map_data = df_map_data.merge(profissao_pred, on='nome', how='left')

# Escolaridade mais comum
escolaridade_pred = (
    df.groupby('ADAI_CT4')['ID11']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID11': 'Escolaridade_Predominante'})
)
df_map_data = df_map_data.merge(escolaridade_pred, on='nome', how='left')

# Religião mais comum
religiao_pred = (
    df.groupby('ADAI_CT4')['ID12']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID12': 'Religiao_Predominante'})
)
df_map_data = df_map_data.merge(religiao_pred, on='nome', how='left')

# Povo tradicional: % de respondentes por município
povo_pct = (
    df[df['PCT0'] == 'Sim']
    .groupby('ADAI_CT4').size() / df.groupby('ADAI_CT4').size()
).mul(100).round(1).reset_index(name='Pct_Povo_Tradicional')
povo_pct = povo_pct.rename(columns={'ADAI_CT4': 'nome'})
df_map_data = df_map_data.merge(povo_pct, on='nome', how='left')

# Deficiência: % de respondentes com deficiência
if 'Deficiencia' in df.columns:
    def_pct = (
        df[df['Deficiencia'] == 'Sim']
        .groupby('ADAI_CT4').size() / df.groupby('ADAI_CT4').size()
    ).mul(100).round(1).reset_index(name='Pct_Deficiencia')
    def_pct = def_pct.rename(columns={'ADAI_CT4': 'nome'})
    df_map_data = df_map_data.merge(def_pct, on='nome', how='left')
else:
    df_map_data['Pct_Deficiencia'] = None

# Raça/cor: mais comum por município
raca_pred = (
    df.groupby('ADAI_CT4')['ID7']
    .agg(lambda x: x.value_counts().idxmax() if not x.value_counts().empty else None)
    .reset_index().rename(columns={'ADAI_CT4': 'nome', 'ID7': 'Raca_Predominante'})
)
df_map_data = df_map_data.merge(raca_pred, on='nome', how='left')

# --- Remover colunas duplicadas de 'nome'
df_map_data = df_map_data.loc[:, ~df_map_data.columns.duplicated()]

# ========== INTERATIVIDADE ==========

# Filtro de município (opcional, pode comentar se não quiser)
municipio_opcao = st.selectbox(
    "Filtrar município",
    options=['Todos'] + sorted(df_map_data['nome'].dropna().unique().tolist()),
    index=0
)

df_map_vis = df_map_data if municipio_opcao == 'Todos' else df_map_data[df_map_data['nome'] == municipio_opcao]

# ========== MAPA MELHORADO ==========

if 'lat' in df_map_vis.columns and 'lon' in df_map_vis.columns and not df_map_vis[['lat', 'lon']].isna().all().all():
    try:
        lat_center = df_map_vis["lat"].mean()
        lon_center = df_map_vis["lon"].mean()
        fig_map = px.scatter_mapbox(
            df_map_vis,
            lat="lat",
            lon="lon",
            size="Total Respondentes",
            size_max=60,  # Círculos ainda maiores
            color="Total Respondentes",
            color_continuous_scale=px.colors.sequential.Plasma,
            opacity=0.85,  # Pontos um pouco transparentes para destaque
            hover_name="nome",
            hover_data={
                "Total Respondentes": True,
                "Mulher": True,
                "Homem": True,
                "Pct_Mulheres": True,
                "Pct_Homens": True,
                "Profissao_Predominante": True,
                "Escolaridade_Predominante": True,
                "Religiao_Predominante": True,
                "Raca_Predominante": True,
                "lat": False, "lon": False
            },
            mapbox_style="carto-positron",
            zoom=6,
            center={"lat": lat_center, "lon": lon_center}
        )
        fig_map.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            height=600,
            title="<b>Total de Respondentes por Município</b>",
            coloraxis_colorbar=dict(
                title="Total<br>Respondentes"
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar o mapa Plotly: {e}")
else:
    st.warning("Não há coordenadas (lat/lon) dos municípios no DataFrame para plotar pontos no mapa. Exibindo apenas a tabela.")


# ========== TABELA INTERATIVA ==========

st.markdown("#### Detalhes por Município (clique nos cabeçalhos para ordenar)")
st.dataframe(
    df_map_vis[[
        'nome', 'Total Respondentes', 'Homem', 'Mulher', 'Pct_Mulheres',
        'Profissao_Predominante', 'Escolaridade_Predominante', 'Religiao_Predominante',
        'Raca_Predominante'
    ]], use_container_width=True, hide_index=True
)

st.download_button(
    "Baixar Tabela Municípios",
    df_map_vis.to_csv(index=False),
    file_name="municipios_respondentes.csv"
)
# Cole seus dados manualmente (pode expandir se quiser)
dados = {
    'CT2': [
        "05/10/2023", "09/10/2023", "27/09/2023", "10/10/2023", "22/09/2023",
        "16/10/2023", "06/10/2023", "18/10/2023", "22/09/2023", "28/09/2023",
        "02/10/2023", "20/10/2023", "29/09/2023", "04/10/2023", "27/09/2023",
        "03/10/2023", "19/09/2023", "19/09/2023", "17/10/2023", "28/09/2023",
    ],
    'ADAI_CT4': [
        "Colatina", "Colatina", "Linhares", "São Mateus", "Colatina",
        "Linhares", "Colatina", "Colatina", "Linhares", "Povoação",
        "Linhares", "Linhares", "Linhares", "Linhares", "São Mateus",
        "São Mateus", "Marilândia", "São Mateus", "Linhares", "São Mateus",
    ]
}

df = pd.DataFrame(dados)

# Padroniza e converte as datas
df['CT2'] = df['CT2'].astype(str).str.strip()
df['ADAI_CT4'] = df['ADAI_CT4'].astype(str).str.strip()
df['CT2'] = pd.to_datetime(df['CT2'], format='%d/%m/%Y', errors='coerce')
df['Mes_Ano'] = df['CT2'].dt.to_period('M').astype(str)

# Agrupa
df_race = (
    df.groupby(['Mes_Ano', 'ADAI_CT4'])
    .size()
    .reset_index(name='Total Respondentes')
    .rename(columns={'ADAI_CT4': 'Município'})
)

# Sem filtro de top 10 (mas com esses dados, não precisa)
st.markdown("### Bar Chart Race dos Municípios por Respondentes")
fig_race = px.bar(
    df_race, 
    x='Total Respondentes', 
    y='Município', 
    color='Município', 
    orientation='h',
    animation_frame='Mes_Ano',
    range_x=[0, df_race['Total Respondentes'].max() + 1],
    title="",
    labels={'Mes_Ano': 'Mês/Ano'}
)


fig_race.update_layout(height=500, xaxis_title="Total de Respondentes", yaxis_title="Município")
st.plotly_chart(fig_race, use_container_width=True)

# Exibe a tabela para conferência
st.write(df)
