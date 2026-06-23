import os
import pandas as pd
import geopandas as gpd

def ejecutar_etl():
    print("Iniciando proceso ETL...")

    # 1. EXTRACCIÓN
    # Cargamos los archivos de minería
    mineria_1 = pd.read_csv("Empleo-rubro-genero-prov.csv")
    mineria_2 = pd.read_csv("empresas_cantidad_mineras.csv")
    
    # Cargamos el de población
    df_poblacion = pd.read_csv("c2022_tp_est_c2.csv", encoding="latin1")
    
    # 2. TRANSFORMACIÓN
    
    # --- PROCESAR PRIMER CSV (Empleo) ---
    # Renombrar "Cantidad" para saber que se refiere a empleados
    mineria_1.rename(columns={'Cantidad': 'empleados', 'provincia_zona': 'provincia'}, inplace=True)
    
    # Extraer el año de la columna año_mes 
    mineria_1['año'] = mineria_1['año_mes'].str[:4].astype(int)
    
    # --- PROCESAR SEGUNDO CSV (Empresas) ---
    # Renombrar "Cantidad" para saber que se refiere a empresas
    mineria_2.rename(columns={'Cantidad': 'empresa'}, inplace=True)
    mineria_2['año'] = mineria_2['año_mes'].str[:4].astype(int)
    
    # Como el segundo CSV no tiene provincia, agrupamos el total de empresas por año y rubro
    # (O si asumes que es el total país, nos servirá para métricas generales)
    df_empresas_agrupado = mineria_2.groupby(['año', 'rubro'])['empresa'].sum().reset_index()

    # --- COMBINAR LOS DATOS DE MINERÍA  ---
    # En lugar de concat, merge para que cada fila de empleo tenga su rubro y año emparejado con la cantidad de empresas
    df_mineria = pd.merge(
        mineria_1, 
        df_empresas_agrupado, 
        on=['año', 'rubro'], 
        how='left'
    )

    # --- PROCESAR CSV DE POBLACIÓN ---
    df_poblacion.columns = ['provincia', 'Superficie en km2', 'Población total','Densidad hab/km2']
    df_poblacion['año'] = 2022  # año del censo
    
    # Estandarizar nombres de Provincias 
    reemplazos_provincias = {
        "Neuquen": "Neuquén",
        "Cordoba": "Córdoba",
        "Entre Rios": "Entre Ríos",
        "Mendoza-Zona Este": "Mendoza", 
        "Mendoza-Zona Sur": "Mendoza",
    }
    df_mineria['provincia'] = df_mineria['provincia'].replace(reemplazos_provincias).str.strip()
    df_poblacion['provincia'] = df_poblacion['provincia'].replace(reemplazos_provincias).str.strip()

    # --- MERGE FINAL CON POBLACIÓN ---
    df_consolidado = pd.merge(
        df_mineria, 
        df_poblacion, 
        on=['provincia', 'año'], 
        how='left'
    )

    # Rellenamos nulos por si acaso
    df_consolidado['empleados'] = df_consolidado['empleados'].fillna(0).astype(int)
    df_consolidado['empresa'] = df_consolidado['empresa'].fillna(0).astype(int)

    # Quitar columnas temporales
    df_consolidado.drop(columns=['año_mes'], errors='ignore', inplace=True)

    # =========================================================================
    # --- PROCESAR Y OPTIMIZAR GEOJSON ---
    # =========================================================================
    print("Optimizando mapa GeoJSON...")
    
    # 1. Que la librería del sistema elimine temporalmente el límite de tamaño
    os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"
    
    # 2. Leer el archivo pesado original (ajusta el nombre si es necesario)
    geo_original = gpd.read_file("provincia.geojson")
    
    # 3. Simplificar las geometrías 
    geo_original["geometry"] = geo_original["geometry"].simplify(0.01, preserve_topology=True)
    
    # 4. Guardar nuevo mapa 
    geo_original.to_file("provincias_web.geojson", driver="GeoJSON")
    print("Mapa optimizado generado como 'provincias_web.geojson'")

    # 3. ALMACENAMIENTO
    df_consolidado.to_csv("datos_limpios.csv", index=False)
    print("ETL finalizado con éxito. ¡Archivo 'datos_limpios.csv' generado!")

if __name__ == "__main__":
    ejecutar_etl()