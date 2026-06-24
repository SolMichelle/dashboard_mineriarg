# dashboard_mineriarg
_Portal de datos sobre la minería en Argentina_

Este repositorio contiene el desarrollo de punta a punta de un **Portal de Inteligencia de Datos** enfocado en el análisis, evolución y distribución territorial de la actividad minera en la República Argentina. 

El proyecto integra procesos automatizados de ETL, análisis geoespacial y un dashboard web interactivo diseñado para facilitar la toma de decisiones y el análisis de la industria.

---

##  Resumen

El portal resuelve la dispersión de datos públicos de la actividad minera. Consolida registros de empleo sectorial (abiertos por provincia, año y género), densidades empresariales por rubro y datos demográficos del Censo 2022. 

### Objetivos:
* **Evolución del empleo:** monitorear el comportamiento estructural de los puestos de trabajo directos según el rubro minero.
* **Brecha de género:** analizar la proporción y evolución de la inserción de mujeres dentro de la fuerza laboral a lo largo de las series temporales.
* **Impacto socio-laboral local:** cruzar la actividad con variables censales para medir qué porcentaje real de la población de cada provincia depende económicamente de la minería.
* **Visualización geoespacial:** representar la concentración de la fuerza de trabajo en un mapa dinámico utilizando cartografía oficial del Instituto Geográfico Nacional (IGN).

---

## Estructura de la arquitectura

El proyecto sigue un flujo lineal de datos dividido en tres capas principales:
* **Capa de ETL:** el script `etl.py` lee los CSVs crudos, normaliza las inconsistencias en los nombres de las provincias, transforma strings demográficos a tipo numérico entero y calcula promedios mensuales anualizados para neutralizar la duplicación de datos en métricas y mapas. Además, optimiza la geometría del mapa pesado del IGN (`provincias_web.geojson`) reduciendo su complejidad para la web.
* **Capa de inteligencia de negocio:** el archivo `app.py` procesa los datos filtrados, aplica agregaciones de control por valor máximo (`'max'`) para aislar variables macro (empresas nacionales), calcula en tiempo real métricas de negocio y genera gráficos dinámicos con Plotly (incluyendo el nuevo ranking de impacto local).
* **Capa de despliegue:** integración continua mediante GitHub, servidor web en Streamlit Cloud.

---

##  Guía de Usuario y Ejecución 

Si querés replicar este proyecto o ejecutarlo de forma local en tu computadora, seguí estos pasos:

### 1. Requisitos previos
Asegurate de tener instalado **Python 3.10 o superior** y un gestor de paquetes como `pip`.

### 2. Clonar el repositorio e instalar dependencias
Abrí tu terminal o consola de comando y ejecuta:

#### Clonar este repositorio
git clone [https://github.com/SolMichelle/dashboard_mineriarg.git](https://github.com/SolMichelle/dashboard_mineriarg.git)

#### Entrar a la carpeta del proyecto
cd dashboard_mineriarg

#### Instalar las librerías necesarias de forma automática
pip install -r requirements.txt

### 3. Ejecutar el Proceso ETL (Opcional)
Si modificaste los datos de origen o querés regenerar el mapa optimizado:
python etl.py

### 4. Lanzar el Dashboard Interactivo
Para encender el panel web local en tu navegador:
streamlit run app.py

Se abrirá automáticamente una pestaña en tu navegador web en la dirección http://localhost:8501 con el panel interactivo totalmente funcional.

---

### Stack usado 🛠️
* Lenguaje: Python 3.12
* Procesamiento de datos: Pandas
* Sistemas de información geográfica (GIS): GeoPandas
* Visualización dinámica: Plotly Express & Graph Objects
* Framework del Dashboard: Streamlit
* Control de versiones & servidor: GitHub & Streamlit Community Cloud
* Prototipado inicial: Power BI (Modelado de datos y diseño DAX)

