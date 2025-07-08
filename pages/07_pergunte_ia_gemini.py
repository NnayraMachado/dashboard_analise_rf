import streamlit as st
import pandas as pd
import plotly.express as px

# Checa se o DataFrame principal foi carregado
from utils.session import ensure_session_data
ensure_session_data()

    
df = st.session_state['df']
st.header("Visualização por Mapa")

st.info("Este mapa exibe a distribuição espacial dos municípios onde há respondentes. O tamanho do círculo indica o número de respondentes.")
st.markdown("---")

# Posição central do ES
center = [-19.5, -40.5]

# --- Cria DataFrame de municípios e total de respondentes
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

# Set dos municípios com respostas
municipios_com_respostas = set(df_map_data['nome'])

# Função melhorada para popup: mostra mais detalhes e emojis
def make_popup(row):
    return folium.Popup(f"""
        <b>{row['nome']}</b><br>
        👤 <b>Total respondentes:</b> {row['Total Respondentes']}<br>
        👩 <b>Mulheres:</b> {row.get('Mulher', 0)} ({row.get('Pct_Mulheres', 0)}%)<br>
        👨 <b>Homens:</b> {row.get('Homem', 0)} ({row.get('Pct_Homens', 0)}%)<br>
        🧑‍🦱 <b>Raça predominante:</b> {row.get('Raca_Predominante', 'n/d')}<br>
        🎓 <b>Escolaridade predominante:</b> {row.get('Escolaridade_Predominante', 'n/d')}<br>
        💼 <b>Profissão predominante:</b> {row.get('Profissao_Predominante', 'n/d')}<br>
        🙏 <b>Religião predominante:</b> {row.get('Religiao_Predominante', 'n/d')}<br>
    """, max_width=350)

# --- Mapa Folium dos limites do ES
# (Aqui, estados_geojson deve ser carregado anteriormente!)
# m = folium.Map(location=center, zoom_start=7, tiles='cartodbpositron')
# for feature in estados_geojson['features']:
#     ...

# --- Mapa Plotly dos pontos
if 'lat' in df_map_data.columns and 'lon' in df_map_data.columns and not df_map_data[['lat', 'lon']].isna().all().all():
    try:
        lat_center = df_map_data["lat"].mean()
        lon_center = df_map_data["lon"].mean()
        fig_map = px.scatter_mapbox(
            df_map_data,
            lat="lat",
            lon="lon",
            size="Total Respondentes",
            color="Total Respondentes",
            color_continuous_scale=px.colors.sequential.Viridis,
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
            center={"lat": lat_center, "lon": lon_center},
            title="Total de Respondentes por Município (Mapa de Pontos)"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar o mapa Plotly: {e}")
else:
    st.warning("Não há coordenadas (lat/lon) dos municípios no DataFrame para plotar pontos no mapa. Exibindo apenas a tabela.")

# --- Exibe tabela e download
st.markdown("#### Detalhes por Município (Mapa)")
st.dataframe(df_map_data[['nome', 'Total Respondentes', 'Homem', 'Mulher', 'Pct_Mulheres', 'Profissao_Predominante',
                     'Escolaridade_Predominante', 'Religiao_Predominante', 'Pct_Povo_Tradicional',
                   ]], use_container_width=True)
st.download_button("Baixar Tabela Municípios", df_map_data.to_csv(index=False), file_name="municipios_respondentes.csv")
