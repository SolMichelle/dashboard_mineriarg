import os
import pandas as pd
import geopandas as gpd

def limpiar_texto_provincia(series):
    """Normaliza el texto de las provincias """
    return (series.astype(str)
            .str.normalize('NFKD')  # Remueve acentos
            .str.encode('ascii', errors='ignore')
            .str.decode('utf-8')
            .str.upper()            
            .str.replace(r'---.*', '', regex=True) 
            .str.strip())

def ejecutar_etl():
    print("Iniciando proceso ETL optimizado por granularidad...")

    # =========================================================================
    # 1. EXTRACCIÓN
    # =========================================================================
    mineria_1 = pd.read_csv("Empleo-rubro-genero-prov.csv")
    mineria_2 = pd.read_csv("empresas_cantidad_mineras.csv")
    df_poblacion = pd.read_csv("c2022_tp_est_c2.csv", encoding="latin1")
    
    # =========================================================================
    # 2. TRANSFORMACIÓN
    # =========================================================================
    
    # --- A) PROCESAR UNIVERSO EMPLEO  ---
    mineria_1.rename(columns={'Cantidad': 'empleados', 'provincia_zona': 'provincia'}, inplace=True)
    mineria_1['año'] = mineria_1['año_mes'].astype(str).str[:4].astype(int)
    
    # Mapeo y colapso de subzonas provinciales antes de anualizar
    reemplazos_zonas = {
        "Mendoza-Zona Este": "Mendoza", 
        "Mendoza-Zona Sur": "Mendoza",
        "Mendoza-Zona Centro": "Mendoza",
        "Tierra del Fuego, Antártida e Islas del Atlántico Sur (1)(3)": "Tierra del Fuego",
        "Ciudad Autónoma de Buenos Aires": "CABA",
        "Río Negro": "Rio Negro",
        "Neuquén": "Neuquen",
        "Entre Ríos": "Entre Rios",
        "Santiago del Estero": "Santiago Del Estero",
        "Tucumán": "Tucuman"
    }
    mineria_1['provincia'] = mineria_1['provincia'].replace(reemplazos_zonas)
    
    # Anualiza el empleo calculando el promedio mensual de trabajadores activos en el año
    df_empleo_anual = mineria_1.groupby(['año', 'provincia', 'rubro', 'genero'])['empleados'].mean().reset_index()
    # Redondea a enteros lógicos
    df_empleo_anual['empleados'] = df_empleo_anual['empleados'].round().astype(int)

    # --- B) PROCESAR UNIVERSO EMPRESAS ---
    mineria_2.rename(columns={'Cantidad': 'empresa'}, inplace=True)
    mineria_2['año'] = mineria_2['año_mes'].astype(str).str[:4].astype(int)
    
    # Anualiza la cantidad de empresas usando el promedio mensual del año (evita inflar x12)
    df_empresas_anual = mineria_2.groupby(['año', 'rubro'])['empresa'].mean().reset_index()
    df_empresas_anual['empresa'] = df_empresas_anual['empresa'].round().astype(int)

    # --- C) COMBINACIÓN CONTROLADA DE MINERÍA ---
    # Une manteniendo la granularidad micro del empleo como base principal
    df_mineria = pd.merge(
        df_empleo_anual, 
        df_empresas_anual, 
        on=['año', 'rubro'], 
        how='left'
    )

    # --- D) PROCESAR Y CORREGIR DATASET DE POBLACIÓN ---
    df_poblacion.columns = ['provincia', 'Superficie en km2', 'Población total', 'Densidad hab/km2']
    
    df_poblacion['Población total'] = (df_poblacion['Población total']
                                    .astype(str)
                                    .str.replace('.', '', regex=False)
                                    .str.strip())
    df_poblacion['Población total'] = pd.to_numeric(df_poblacion['Población total'], errors='coerce').fillna(0).astype(int)
    df_poblacion['Superficie en km2'] = (df_poblacion['Superficie en km2']
                                        .astype(str)
                                        .str.replace('.', '', regex=False)
                                        .str.strip())
    df_poblacion['Superficie en km2'] = pd.to_numeric(df_poblacion['Superficie en km2'], errors='coerce').fillna(0).astype(int)
    
    # Mapeo de inconsistencias de nombres comunes entre el Censo y el Dataset de Empleo
    reemplazos_poblacion = {
        "Mendoza-Zona Este": "Mendoza", 
        "Mendoza-Zona Sur": "Mendoza",
        "Mendoza-Zona Centro": "Mendoza",
        "Tierra del Fuego, Antártida e Islas del Atlántico Sur (1)(3)": "Tierra del Fuego",
        "Ciudad Autónoma de Buenos Aires": "CABA",
        "Río Negro": "Rio Negro",
        "Neuquén": "Neuquen",
        "Entre Ríos": "Entre Rios",
        "Santiago del Estero": "Santiago Del Estero",
        "Tucumán": "Tucuman"
    }
    df_poblacion['provincia'] = df_poblacion['provincia'].replace(reemplazos_poblacion)

    # Aplicar normalización estricta en ambos conjuntos
    df_mineria['provincia_match'] = limpiar_texto_provincia(df_mineria['provincia'])
    df_poblacion['provincia_match'] = limpiar_texto_provincia(df_poblacion['provincia'])

    # Extraer solo las columnas demográficas necesarias para no duplicar la columna 'provincia' original
    df_pob_clean = df_poblacion[['provincia_match', 'Superficie en km2', 'Población total', 'Densidad hab/km2']]

    # --- E) MERGE FINAL CON POBLACIÓN ---
    # Cruza únicamente por la clave normalizada 'provincia_match' para que aplique a todos los años
    df_consolidado = pd.merge(
        df_mineria, 
        df_pob_clean, 
        on='provincia_match', 
        how='left'
    )

    # Eliminar la columna de cruce auxiliar
    df_consolidado.drop(columns=['provincia_match'], errors='ignore', inplace=True)

    # Rellenar nulos remanentes por seguridad estructural
    df_consolidado['empleados'] = df_consolidado['empleados'].fillna(0).astype(int)
    df_consolidado['empresa'] = df_consolidado['empresa'].fillna(0).astype(int)
    
    # Limpiar densidad
    if 'Densidad hab/km2' in df_consolidado.columns:
        df_consolidado['Densidad hab/km2'] = df_consolidado['Densidad hab/km2'].astype(str).str.replace(',', '.').str.strip()

    # =========================================================================
    # --- PROCESAR Y OPTIMIZAR GEOJSON ---
    # =========================================================================
    print("Optimizando mapa GeoJSON...")
    os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"
    
    if os.path.exists("provincia.geojson"):
        geo_original = gpd.read_file("provincia.geojson")
        
        # Reducimos peso coordinando con la tolerancia web
        geo_original["geometry"] = geo_original["geometry"].simplify(0.01, preserve_topology=True)
        
        # Normalizamos la propiedad del nombre dentro del GeoJSON para que coincida con la app de Streamlit
        if 'nam' in geo_original.columns:
            geo_original['nam'] = geo_original['nam'].str.strip()
            
        geo_original.to_file("provincias_web.geojson", driver="GeoJSON")
        print("Mapa optimizado generado como 'provincias_web.geojson'")
    else:
        print("Aviso: No se encontró 'provincia.geojson'. Saltando optimización de mapa.")

    # =========================================================================
    # 3. ALMACENAMIENTO DEL DATASET
    # =========================================================================
    df_consolidado.to_csv("datos_limpios.csv", index=False)
    print("ETL finalizado con éxito. ¡Archivo 'datos_limpios.csv' generado de forma consistente!")

if __name__ == "__main__":
    ejecutar_etl()
