SISTEMA DE PIPELINE DE DATOS Y DASHBOARD DE DENSIDAD OPERATIVA - AGUAPACHÁ EVENTOS

Este proyecto implementa una solución integral de Análisis de Datos (End-to-End) para la optimización logística y comercial de Aguapachá Eventos, una agencia especializada en servicios musicales y logística de eventos. El sistema abarca desde la automatización de la carga de datos estructurados hasta el despliegue de tableros interactivos para la toma de decisiones estratégicas.

---

🛠️ Tecnologías y Herramientas Utilizadas
Python: Automatización de la ETL (Extracción, Transformación y Carga), gestión de datos maestros y carga masiva automatizada. (Permite seguir alimentando la Base de datos)
MySQL: Diseño e implementación del modelo de base de datos relacional y almacenamiento transaccional.
Power BI & DAX: Modelado multidimensional (Tablas de hechos y dimensiones), creación de una tabla de calendario analítico dinámico y diseño de interfaces de usuario (UI/UX).

---

📐 Arquitectura del Proyecto

1. Origen de Datos: Consolidación de registros analíticos e históricos operativos en formatos planos (Excel/CSV).

2. Procesamiento e Inserción (Python): Scripts automatizados que realizan la limpieza de los datos, validación de integridad referencial (datos duplicados, no permitidos e informes de errores), actualización de maestros y ejecución de cargas masivas seguras hacia el motor de base de datos.

3. Almacenamiento (SQL): Repositorio estructurado en MySQL optimizado para consultas rápidas sobre el histórico de contratos y servicios. (Allí se realizan vistas, procedimientos almacenados y funciones para optimizar procesos de consultas y unión entre tablas).

4. Capa de Inteligencia de Negocios (Power BI): Conexión directa a la base de datos, modelado relacional y cálculo de métricas avanzadas mediante lenguaje DAX.

---

📈 Tableros e Insights de Negocio

El reporte interactivo cuenta con dos enfoques de análisis críticos para la gerencia:

1. Panel de Control Comercial e Indicadores Clave (KPIs)
Permite monitorear los estados financieros y la evolución de las ventas en ventanas de tiempo dinámicas. (Toda esta información se puede obtener con fechas especificas, servicios o tipo de evento)

Ventas Totales: Control centralizado del volumen financiero.

Ticket Promedio: Monitoreo del valor medio de contratación por evento.

Evolución Mensual (MoM): Medición de crecimiento porcentual respecto al mes anterior.

Distribución de Mercado: Identificación visual de las zonas geográficas con mayor densidad de servicios mediante mapas calóricos de geolocalización.

2. Matriz de Densidad Operativa (Mapa de Calor Logístico)
Diseñado específicamente para mitigar cuellos de botella del personal y optimizar la disponibilidad del inventario técnico y musical por horas y días específicos.

Estructura Jerárquica: Permite desglosar las métricas desde la vista macro del día de la semana hasta la vista micro de las horas de inicio de los espectáculos.

Análisis de Picos de Demanda: Revela de manera inmediata que los Sábados concentran la mayor carga operativa histórica (con servicios líderes como Chirimía, registrando picos individuales de alta densidad). Esto permite planificar con precisión la contratación de personal de apoyo y la logística interna para los fines de semana.

---

📂 Estructura del Repositorio

BD: Contiene los scripts de inicialización, definición de tablas de la base de datos (DDL) y scripts de consultas estructuradas.

Python y datos: Incluye los desarrollos en Python encargados del pipeline de datos (creación de datos, carga masiva, sincronización de maestros y reseteo controlado de entornos), junto con las fuentes de datos utilizadas. Nota: La creación de datos es un script que genera un archivo de Excel con N cantidad de datos para luego ser cargado en MySQL (Tener en cuenta limite de datos de Excel)

Capturas informes: Contiene visuales de los reportes generados.

Aguapachá_Dash.pbix: Archivo fuente del proyecto de Power BI con el modelo DAX y diseño de interfaces implementado.
