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
# 2. ETIQUETAS SEGMENTADORAS 
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
    # CORREGIDO PARA EVITAR MULTIPLICACIÓN
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
    colores_genero = {
        "Femenino": "#ff69b4",     
        "Masculino": "#4682b4"    
    }
    
    fig_area = px.area(
        df_genero, 
        x="año", 
        y="empleados", 
        color="genero", 
        groupnorm='percent', 
        title="Proporción de género",
        color_discrete_map=colores_genero
    )
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

# 1. Agrupar primero por Rubro y Año para respetar la naturaleza macro de las empresas
df_rubro_base = df_filtrado.groupby(['rubro', 'año']).agg(
    total_empleados=('empleados', 'sum'),
    total_empresas=('empresa', 'max') # 'max' toma el valor nacional real del año sin duplicar
).reset_index()

# 2. Consolida los totales históricos/filtrados por Rubro
df_rubro = df_rubro_base.groupby('rubro').agg(
    total_empleados=('total_empleados', 'sum'),
    total_empresas=('total_empresas', 'sum')
).reset_index()

# 3. Cálculo directo y seguro del promedio por empresa
df_rubro['promedio_por_empresa'] = df_rubro.apply(
    lambda r: r['total_empleados'] / r['total_empresas'] if r['total_empresas'] > 0 else 0, axis=1
)

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

# CORREGIDO: solo empleo por provincia
df_mapa = df_filtrado.groupby('provincia').agg(
    total_empleados=('empleados', 'sum')
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
# 5. MAPA INTERACTIVO Y PROPORCIÓN LOCAL
# -------------------------------------------------------------------------
st.write("### Impacto socio-económico en las provincias")
st.markdown("""
*Este gráfico analiza la intensidad de la actividad minera en relación con la población total de cada provincia (considerando datos del Censo 2022). 
Permite visualizar un ranking de qué provincias dependen más críticamente del empleo minero para su estructura socioeconómica local, independientemente de su tamaño absoluto.*
""")

# Agrupación de datos
df_impacto = df_filtrado.groupby(['provincia', 'Población total']).agg(
    total_empleados=('empleados', 'sum')
).reset_index()

# Calcular porcentaje local de empleo minero
df_impacto['porcentaje_local'] = (df_impacto['total_empleados'] / df_impacto['Población total']) * 100

# Ordenar de menor a mayor 
df_ranking = df_impacto.sort_values(by='porcentaje_local', ascending=True)

# Crear el gráfico
fig_ranking = px.bar(
    df_ranking,
    x='porcentaje_local',
    y='provincia',
    orientation='h',
    title="Porcentaje de la población provincial dedicada al empleo minero",
    labels={'porcentaje_local': '% de la población local', 'provincia': 'Provincia'},
    color='porcentaje_local',
    color_continuous_scale="Cividis"  
)

# Ajustes de diseño 
fig_ranking.update_layout(
    showlegend=False, 
    coloraxis_showscale=True, # barra de intensidad de color
    coloraxis_colorbar=dict(title="%"),
    margin=dict(l=50, r=20, t=40, b=40),
    height=500
)

st.plotly_chart(fig_ranking, use_container_width=True)

st.markdown("---")
# -------------------------------------------------------------------------
# 6. APARTADO PARA CONCLUSIONES
# -------------------------------------------------------------------------
st.write("## Conclusiones del análisis")
st.info("""
🛠️ Metodología y desarrollo: El diseño previo en Power BI fue la guía fundamental para estructurar este portal en Streamlit, superando limitaciones de licencias para compartir los resultados y validando la consistencia de las métricas.

🏢 Estructura empresarial: El tejido industrial minero se compone de un número acotado de grandes operadores (alrededor de mil empresas activas en el país), pero su cadena de valor está sostenida principalmente por PyMEs locales y empresas contratistas. Esto se refleja en que el promedio general de la industria ronda los 30 empleadxs por firma, demostrando que el sector tracciona una fuerte red de empleo mediano y familiar en las regiones donde se instala.

🔍 Contraste de rubros (Datos 2026): Metalíferos lidera el empleo masivo con casi 13.000 puestos. El modelo corporativo de mayor envergadura por empresa se concentra en Combustibles (más de 600 empleadxs/firma) y Litio (220 empleadxs/firma), mientras que Rocas de Aplicación equilibra el tablero aportando más de 5.000 empleos estables con estructuras medianas de casi 17 personas.

📍 Distribución territorial: La actividad laboral presenta una marcada desigualdad geográfica, concentrándose fuertemente en las provincias del sur, Santa Cruz, y de la región cordillerana, San Juan y NOA, debido a la localización de los yacimientos.

📈 Evolución histórica: Los picos históricos de empleo ocurrieron en 2009 y 2012. Tras una fuerte crisis general en 2010, el rubro Servicios Mineros (que hoy emplea a más de 8.000 personas) logró revertir la tendencia y superar desde 2023 sus récords históricos de empleabilidad.

⚖️ Brecha de género: Históricamente masculinizado, el sector muestra un crecimiento sostenido de empleo femenino desde 2018, aunque la fuerza laboral de mujeres ronda apenas el 10% general desde 2020. La gran excepción es el Litio (más de 5.000 empleados), que registra un crecimiento exponencial desde 2021 y lidera la industria con la menor brecha de género.
""")
