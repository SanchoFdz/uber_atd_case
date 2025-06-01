## Uber ATD Case
Santiago Fernández del Castillo Sodi

Para el puesto de Automation & Analytics Analyst

# Paso 0) Instalación de entorno
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

# Paso 1) Corre la aplicación

Una vez instalado, y en la raíz del repositorio.

- 1.1 Correr la aplicación streamlit escribiendo directo en la terminal
```
streamlit run streamlit_app.py
```

- 1.2 Esperarás unos segundos y podrás hacer click directo en Local URL

- 1.3 Toma un poco de tiempo, pero esto abrirá un streamlit

# Paso 2) Espera a la carga de datos

Una vez abierto streamlit, espera a que la rueda de load_data en la landing page deje de dar vueltas, eso significa que el app está lista para usarse.

# Paso 3) Uso

Lo ideal es seguir la ruta lógica que es formular hipótesis en Conversation Opener (y aplicar los filtros necesarios para tu análisis), seguir profundizando en las causas que podría explicar tu hipótesis en Root Causes Analysis y terminar pensando en mejoras con las ultimas 3 pestañas.


