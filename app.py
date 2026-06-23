import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(layout="wide")

# 1. TÍTULO Y SUBTÍTULO
st.title("Portal de inteligencia de datos: Minería en Argentina")
st.subheader("Análisis de la evolución del empleo y distribución territorial")

# -------------------------------------------------------------------------
# Carga de Datos 
# -------------------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("datos_limpios.csv")

@st.cache_data
def load_geojson():
    # Reemplaza con el archivo GeoJSON optimizado
    return gpd.read_file("provincias_web.geojson") 

df_total = load_data()
geo_provincias = load_geojson()

# -------------------------------------------------------------------------
# 2. ETIQUETAS SEGMENTADORAS (Filtros en la barra lateral)
# -------------------------------------------------------------------------
st.sidebar.header("Filtros del panel")

anios = sorted(df_total['año'].unique())
anio_sel = st.sidebar.multiselect("Seleccionar año", anios, default=anios)

provincias = sorted(df_total['provincia'].unique())
prov_sel = st.sidebar.multiselect("Seleccionar provincia", provincias, default=provincias)

rubros = sorted(df_total['rubro'].unique())
rubro_sel = st.sidebar.multiselect("Seleccionar rubro", rubros, default=rubros)

# Aplicar filtros al dataset
df_filtrado = df_total[
    (df_total['año'].isin(anio_sel)) & 
    (df_total['provincia'].isin(prov_sel)) & 
    (df_total['rubro'].isin(rubro_sel))
]

# -------------------------------------------------------------------------
# 3. TRES KPIS
# -------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    # CORREGIDO PARA EVITAR MULTIPLICACIÓN:
    df_empresas_unicas = df_filtrado.drop_duplicates(subset=['año', 'rubro'])
    cant_empresas = df_empresas_unicas['empresa'].sum()
    
    st.metric(label="Cantidad de empresas", value=f"{cant_empresas:,}")

with col2:
    mediana_emp = df_filtrado['empleados'].median()
    st.metric(label="Mediana de empleadxs", value=f"{mediana_emp:.1f}")

with col3:
    total_empleados = df_filtrado['empleados'].sum()
    
    # cantidad de empresas únicas que calculamos en el KPI 1
    # condicional por si cant_empresas es 0 (para evitar error de división por cero)
    if cant_empresas > 0:
        promedio_por_empresa = total_empleados / cant_empresas
    else:
        promedio_por_empresa = 0.0
        
    st.metric(label="Promedio de empleadxs por empresa", value=f"{promedio_por_empresa:.1f}")

st.markdown("---")

# -------------------------------------------------------------------------
# 4. GRÁFICOS
# -------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.write("### Evolución de empleo por género")
    df_genero = df_filtrado.groupby(['año', 'genero'])['empleados'].sum().reset_index()
    fig_area = px.area(df_genero, x="año", y="empleados", color="genero", 
                    groupnorm='percent', title="Proporción de género")
    st.plotly_chart(fig_area, use_container_width=True)

with row1_col2:
    st.write("### Distribución de empresas por rubro")
    
    # CORREGIDO: filtra duplicados antes de agrupar para el Treemap
    df_tree_previo = df_filtrado.drop_duplicates(subset=['año', 'rubro'])
    df_tree = df_tree_previo.groupby('rubro')['empresa'].sum().reset_index(name='cant_empresas')
    
    fig_tree = px.treemap(df_tree, path=['rubro'], values='cant_empresas', 
                        title="Cantidad de empresas por rubro")
    st.plotly_chart(fig_tree, use_container_width=True)

# -------------------------------------------------------------------------
# GRÁFICO COMBINADO (Empleados vs Promedio por rubro)
# -------------------------------------------------------------------------
st.write("### Análisis de empleadxs por rubro")

df_rubro_base = df_filtrado.groupby(['rubro', 'año']).agg(
    total_empleados=('empleados', 'sum'),
    total_empresas=('empresa', 'nunique') # Corregido a nunique para mantener consistencia
).reset_index()

df_rubro = df_rubro_base.groupby('rubro').agg(
    total_empleados=('total_empleados', 'sum'),
    promedio_por_empresa=('total_empleados', lambda x: x.sum() / df_rubro_base.loc[x.index, 'total_empresas'].sum() if df_rubro_base.loc[x.index, 'total_empresas'].sum() > 0 else 0)
).reset_index()

fig_combinado = go.Figure()

# Barras (Eje Izquierdo - y1)
fig_combinado.add_trace(go.Bar(
    x=df_rubro['rubro'], 
    y=df_rubro['total_empleados'],
    name='Total empleadxs', 
    yaxis='y1',
    marker=dict(color='#1f77b4')
))

# Línea (Eje Derecho - y2)
fig_combinado.add_trace(go.Scatter(
    x=df_rubro['rubro'], 
    y=df_rubro['promedio_por_empresa'],
    name='Promedio por empresa', 
    yaxis='y2', 
    mode='lines+markers',
    line=dict(color='orange', width=3)
))

fig_combinado.update_layout(
    title="Empleadxs totales vs. Promedio por empresa según rubro",
    xaxis=dict(title="Rubros mineros"),
    yaxis=dict(
        title=dict(
            text="Cantidad de empleadxs totales",
            font=dict(color='#1f77b4')
        ),
        tickfont=dict(color='#1f77b4')
    ),
    yaxis2=dict(
        title=dict(
            text="Promedio de empleadxs por empresa",
            font=dict(color='orange')
        ),
        tickfont=dict(color='orange'),
        overlaying='y',
        side='right',
        anchor='x',
        position=1
    ),
    margin=dict(l=60, r=60, t=50, b=50),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_combinado, width='stretch')

st.markdown("---")

# -------------------------------------------------------------------------
# 5. MAPA INTERACTIVO 
# -------------------------------------------------------------------------
st.write("### Distribución geográfica de la actividad minera")

# Agrupación de datos para el mapa por provincia
df_mapa = df_filtrado.groupby('provincia').agg(
    total_empleados=('empleados', 'sum'),
    total_empresas=('empresa', 'sum')
).reset_index()

# mapa con Plotly Express
fig_mapa = px.choropleth_mapbox(
    df_mapa,
    geojson=geo_provincias,
    locations="provincia",          # Columna de DataFrame df_mapa
    featureidkey="properties.nam",  # Llave interna del GeoJSON del IGN para el nombre de la provincia
    color="total_empleados",        # Qué columna pintará las provincias
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=3,
    center={"lat": -38.416097, "lon": -63.616672}, # Centrado en Argentina
    opacity=0.6,
    labels={'total_empleados': 'Empleadxs totales'}
)

fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_mapa, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------------------
# 6. APARTADO PARA CONCLUSIONES
# -------------------------------------------------------------------------
st.write("## Conclusiones del análisis")
st.info("""
    🛠️ Metodología y desarrollo: el diseño previo en Power BI fue la guía fundamental para estructurar este portal en Streamlit, superando limitaciones de licencias para compartir los resultados y validando la consistencia de las métricas.

🏢 Estructura empresarial: se desmitifica que la minería sea solo de megaproyectos, el sector se sostiene sobre más de 236.000 empresas (principalmente PyMEs y contratistas) con un promedio nacional general de 30 empleadxs por firma.

🔍 Contraste de rubros: existe una marcada disparidad. El rubro "Rocas de Aplicación" concentra el mayor volumen con más de 82.000 empresas (promedio de 1 empleadx), mientras que "Metalíferos" y "Combustibles" reflejan estructuras más concentradas pero con el mayor volumen de empleo total y estabilidad laboral.

📍 Distribución territorial: la actividad laboral presenta una marcada desigualdad geográfica, concentrándose fuertemente en las provincias del sur, Santa Cruz, y de la región cordillerana, San Juan y NOA, debido a la localización de los yacimientos.

📈 Evolución histórica: los picos históricos de empleo ocurrieron en 2009 y 2012. Tras una fuerte crisis general en 2010, solo algunos rubros como "Servicios Mineros" lograron revertir la tendencia y superar desde 2023 sus récords históricos de empleabilidad.

⚖️ Brecha de género: históricamente masculinizado, el sector muestra un crecimiento sostenido de empleo femenino desde 2018, aunque la fuerza laboral de mujeres ronda apenas el 10% general desde 2020. La gran excepción es el Litio, que registra un crecimiento exponencial desde 2021 y lidera la industria con la menor brecha de género.
""")
