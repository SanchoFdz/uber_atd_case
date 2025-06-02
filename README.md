## Uber ATD Case
Santiago Fernández del Castillo Sodi

Para el puesto de Automation & Analytics Analyst


# Estructura de las distintas tareas 

Debajo, como subtitulos, se detalla y comenta levemente la creación de las tres tareas y la presentación:

- Task 1 - SQL Query
- Task 2 - Streamlit App
- Task 3 - Modeling (Bonus)
- Task 4 - Business Case Presentation

* * * * *

## Task 1 - SQL Query

[Se generó una carpeta con el query y el pdf]([/guides/content/editing-an-existing-page#modifying-front-matter](https://github.com/SanchoFdz/uber_atd_case/tree/dev/task_1_sql))

- El query está ligeramente comentado
- El pdf contiene detalles sobre como se integraría este query en un workflow con las mejores prácticas

* * * * *

## Task 2 - Streamlit App

Debajo una guía de como instalar el entorno, inicializar la aplicación y navegarla (solo una vista muy high level de las posibilidades):

- src y pages contiene todo el código que genera la aplicación.
- assets y data contiene lo necesario para ejecutar la aplicación. Esta preprocesa automáticamente los datos y genera tablas intermedias para reducir latencia en usos futuros de la aplicación.
- **IMPORTANTE** para evitar subir archivos confidenciales (además de muy pesados), no se incluye la base de datos en el repo, por ello, antes de empezar, dirigete al folder data, crea un folder dentro de data llamado "raw" y arrastra el archivo **BC_A&A_with_ATD.csv**. Al correr el app, automáticamente se generarán todas las vistas y tablas intermedias necesarias.

### Paso 0) Instalación de entorno
Este proyecto utiliza conda . Para instalar las dependencias necesarias, deberás seguir las siguientes instrucciones una vez clonado el repositorio y situado en la raíz del repo:

- 0.1. Crear un entorno conda
```
conda create -n nombre_del_entorno python=3.10
```

- 0.2. Activar el entorno
```
conda activate nombre_del_entorno
```

- 0.3. Instalar las dependencias
```
pip install -r requirements.txt
```

### Paso 1) Corre la aplicación

Una vez instalado, y en la raíz del repositorio.

- 1.1 Correr la aplicación streamlit escribiendo directo en la terminal
```
streamlit run streamlit_app.py
```

- 1.2 Esperarás unos segundos y podrás hacer click directo en Local URL

- 1.3 Toma un poco de tiempo, pero esto abrirá un streamlit

### Paso 2) Espera a la carga de datos

Una vez abierto streamlit, espera a que la rueda de load_data en la landing page deje de dar vueltas, eso significa que el app está lista para usarse.

### Paso 3) Uso

Lo ideal es seguir la ruta lógica que es formular hipótesis en Conversation Opener (y aplicar los filtros necesarios para tu análisis), seguir profundizando en las causas que podría explicar tu hipótesis en Root Causes Analysis y terminar pensando en mejoras con las ultimas 3 pestañas.

* * * * *

## Task 3 - Modeling (Bonus)

Aunque no es el modelo más robusto, se entrenó un pequeño modelo para integrar sus resultados en el dashboard y poder utilizarlo como futuro modelo baseline:

- [Documentación de la implementación](https://github.com/SanchoFdz/uber_atd_case/blob/dev/Task%203%20-%20Modelling.pdf)
- [Notebook de exploración de datos general](https://github.com/SanchoFdz/uber_atd_case/blob/dev/notebooks/01_eda.ipynb)
- [Notebook de exploración de features](https://github.com/SanchoFdz/uber_atd_case/blob/dev/notebooks/02_0_explore_features.ipynb)
- [Notebook con GridSearch para definición del modelo](https://github.com/SanchoFdz/uber_atd_case/blob/dev/notebooks/03_exploration_of_models.ipynb)
- [Notebook con pipeline de generación de features y entrenamiento del modelo](https://github.com/SanchoFdz/uber_atd_case/blob/dev/notebooks/03_01_pipeline_and_save_model.ipynb)
- [Modelo como archivo Pickle](https://github.com/SanchoFdz/uber_atd_case/blob/dev/models/xgb_model.pkl)

* * * * *

## Task 4 - Business Case Presentation

Para presentar la aplicación y justificar su desarrollo se hizo un estudio del caso que cubre los elementos que debe cubrir un estudio de caso. Se puede consultar la presentación directamente como:

- [Pdf](.)
- [Editable de Canva](https://www.canva.com/design/DAGpKEbrpvk/uY3T6ReVhykgWvocFNFeOw/view?utm_content=DAGpKEbrpvk&utm_campaign=share_your_design&utm_medium=link2&utm_source=shareyourdesignpanel)





