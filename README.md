# dashboard_mineriarg
_Portal de datos sobre la minería en Argentina_

Este repositorio contiene el desarrollo de punta a punta de un **Portal de Inteligencia de Datos** enfocado en el análisis, evolución y distribución territorial de la actividad minera en la República Argentina. 

El proyecto integra procesos automatizados de ETL, análisis geoespacial y un dashboard web interactivo diseñado para facilitar la toma de decisiones y el análisis de la industria.

---

## ── Resumen

El portal resuelve la dispersión de datos públicos de la actividad minera. Consolida registros de empleo sectorial (abiertos por provincia, año y género), densidades empresariales por rubro y datos demográficos del Censo 2022. 

### Objetivos:
* **Evolución del empleo:** monitorear el crecimiento de puestos de trabajo directos según el sector minero.
* **Brecha de género:** analizar la proporción y distribución de género dentro de la fuerza laboral a lo largo de los años.
* **Análisis demográfico:** cruzar la actividad minera con la superficie, población y densidad de cada provincia.
* **Visualización geoespacial:** representar la concentración de la actividad en un mapa dinámico utilizando datos del Instituto Geográfico Nacional (IGN).

---

## ── Estructura de la arquitectura

El proyecto sigue un flujo lineal de datos dividido en tres capas principales:

1. **Capa de ETL:** el script `etl.py` lee los CSVs crudos, normaliza las inconsistencias en los nombres de las provincias, limpia registros duplicados y optimiza la geometría del mapa pesado del IGN (`provincias_web.geojson`) reduciendo su complejidad para la web.
2. **Capa de inteligencia de negocio:** el archivo `app.py` procesa los datos filtrados, calcula métricas en tiempo real utilizando la lógica de modelos relacionales estrella (estilo Power BI) y genera gráficos dinámicos con **Plotly**.
3. **Capa de despliegue:** integración continua mediante **GitHub**, servidor web en **Streamlit Cloud**.

---

## ── Guía de Usuario y Ejecución 

Si querés replicar este proyecto o ejecutarlo de forma local en tu computadora, seguí estos pasos:

### 1. Requisitos previos
Asegurate de tener instalado **Python 3.10 o superior** y un gestor de paquetes como `pip`.

### 2. Clonar el repositorio e instalar dependencias
Abrí tu terminal o consola de comando y ejecuta:

#### Clonar este repositorio
git clone [https://github.com/tu-usuario/dashboard-mineria.git](https://github.com/tu-usuario/dashboard-mineria.git)

#### Entrar a la carpeta del proyecto
cd dashboard-mineria

#### Instalar las librerías necesarias de forma automática
pip install -r requirements.txt

### 3. Ejecutar el Proceso ETL (Opcional)
Si modificaste los datos de origen o querés regenerar el mapa optimizado:
python etl.py

### 4. Lanzar el Dashboard Interactivo
Para encender el panel web local en tu navegador:
streamlit run app.py

Se abrirá automáticamente una pestaña en tu navegador web en la dirección http://localhost:8501 con el panel interactivo totalmente funcional.

── Stack usado 🛠️
* Lenguaje: Python 3.12
* Procesamiento de datos: Pandas
* Visualización dinámica: Plotly Express & Graph Objects
* Framework del Dashboard: Streamlit
* Control de versiones & servidor: GitHub & Streamlit Community Cloud
* Prototipado inicial: Power BI (Modelado de datos y diseño DAX)


```bash
# Clonar este repositorio
git clone
