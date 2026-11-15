# CLAUDE.md: `mlflow-tracking-demo`

Autor: Helio Castillo. Idioma de trabajo: español.

## 1. Qué es este proyecto

Un notebook que demuestra el **tracking de modelos en MLflow** para la práctica profesional de un Data Engineer (DE). Usa un caso de negocio **ficticio**: la plataforma e-learning de la Fundación Ayudinga (Panamá) y la pregunta *¿qué curso deberíamos recomendar a cada estudiante?*

Todos los datos son sintéticos. No usar ni inventar datos reales de la fundación.

## 2. Lo que el DE necesita (restricciones duras)

- Al DE **no le importa** si los datos son reales o sintéticos, ni qué algoritmo se use.
- Solo pide **un notebook que funcione** para hacer corridas y tracking del modelo en MLflow.
- El DE se encarga de la infraestructura (servidor de tracking, base de metadatos). El notebook solo debe **establecer el tracking server en el código**.
- El URI del servidor es un **placeholder**. Se lee de la variable de entorno `MLFLOW_TRACKING_URI`; si sigue siendo el placeholder, el notebook debe fallar con un mensaje claro.

Ante cualquier duda de alcance, prioriza lo anterior sobre la sofisticación del modelo.

## 3. Modo de trabajo

El autor quiere **construir, analizar y entrenar él mismo** el notebook. Por defecto:

- Guía, explica y revisa; propón estructura y señala errores.
- Escribe código completo **solo cuando se pida explícitamente**.
- Sé directo y crítico: separa **hechos**, **supuestos** e **hipótesis**, y ordena las recomendaciones por dependencia y riesgo.
- No amplíes el alcance sin consultarlo (ver sección 4).

## 4. Alcance

**Dentro:** una tabla de eventos de recomendación, 3 modelos comparados en MLflow, métricas de ranking, reproducibilidad.

**Fuera (decidido, no reabrir sin consultar):** rutas de aprendizaje, prerrequisitos, historial del estudiante, Model Registry, serving o despliegue, A/B, filtrado colaborativo, rankers dedicados.

## 5. Decisiones de diseño

El detalle completo y su justificación están en `docs/DECISIONES_DATOS.md`. **Léelo antes de proponer cambios.** Resumen:

| Tema | Decisión |
|---|---|
| Unidad de análisis | Una fila por recomendación mostrada (estudiante, curso) |
| Target | `completo_30d`: completó el curso en los 30 días posteriores |
| Tablas | `estudiantes`, `cursos`, `eventos`. Datos: 2,000 estudiantes, 60 cursos, 20 recomendaciones por estudiante (40,000 filas) |
| Planteamiento | Clasificación puntual P(`completo_30d`) por par; se ordena por estudiante |
| Modelos | Popularidad (logit sobre `course_id`), regresión logística, `HistGradientBoostingClassifier`. Solo `scikit-learn` |
| División | `GroupShuffleSplit` por `student_id`, 80/20, sin validación |
| Métricas | ROC AUC, log loss, Precision@5, NDCG@5, Coverage@5. **Primaria: NDCG@5**. K=5 |
| MLflow | Experimento `course-recommender-demo`; run padre `model-comparison` con hijos `popularity`, `logreg`, `hgb`; registro manual, sin `autolog` |

Detalles que no deben perderse:
- La variable `carga` (`duracion_horas / horas_semana`) interviene en el generador pero **no se entrega** como feature a ningún modelo.
- Los tres modelos reciben las mismas variables, salvo popularidad (solo `course_id`).
- Evaluación offline: "recomendar" significa ordenar los 20 cursos mostrados a cada estudiante de prueba y tomar los 5 primeros.

## 6. Estructura del repo

```
notebook.ipynb              # lo único que corre el DE
README.md
requirements.txt
CLAUDE.md
.gitignore                  # mlruns/, mlflow.db, .env, .ipynb_checkpoints/
data/                       # estudiantes.csv, cursos.csv, eventos.csv (fuente de verdad, versionada)
scripts/generate_data.py    # lo ejecuta solo el autor
docs/DECISIONES_DATOS.md
```

Los CSV son la **fuente de verdad**; el notebook los carga y los valida. `scripts/generate_data.py` los produce con una semilla fija.

## 7. Secciones del notebook

| # | Sección |
|---|---|
| 0 | Configuración: URI (variable de entorno con placeholder), `EXPERIMENT_NAME`, `SEED`, `K` |
| 1 | Conexión: imprime `mlflow.__version__` y comprueba el servidor (fail-fast) |
| 2 | Carga y validación: lee los CSV y ejecuta los `assert` |
| 3 | Preparación: `merge`, variables de cruce (`area_coincide`, `brecha_nivel`) y división |
| 4 | Entrenamiento: run padre y tres hijos |
| 5 | Selección: mejor modelo con `search_runs`, por `ndcg_at_5` |
| 6 | Recomendaciones: carga desde `runs:/<run_id>/model` y top-5 para 3 estudiantes |
| 7 | Reproducibilidad: reentrenar con la misma semilla y `assert` (con tolerancia) |

Cada sección lleva una celda de texto que explique qué hace y por qué, pensando en que el DE lo lee de corrido.

## 7. Convenciones

- Textos y comentarios en **español**; columnas en español sin tildes (`nivel_experiencia`); código en **inglés**.
- Una sola constante `SEED` para todo. Una sola constante `K=5`.
- Cada modelo es un `Pipeline` de `scikit-learn` con el preprocesamiento incluido.
- Registro **manual** en MLflow. Cada run registra: parámetros, las 5 métricas, tags (`model_family`, `data_hash`, `caso=ficticio`), artefactos y modelo con `signature` e `input_example`.
- Artefactos: `top5_muestra.csv` en todos los modelos; gráfico de importancia solo en logreg y boosting.
- Credenciales: **nunca** en el repo. Si el servidor exige autenticación, solo por variables de entorno.
- `mlflow` no se fija en `requirements.txt` hasta conocer la versión del servidor del DE.

## 8. Criterios de aceptación

1. "Restart & Run All" corre sin errores contra el servidor del DE.
2. Aparece un experimento con un run padre y tres hijos.
3. Cada hijo tiene sus 5 métricas, parámetros, tags, artefactos y modelo con signature.
4. Todos los `assert` (datos y reproducibilidad) pasan.
5. El modelo ganador se carga desde su run y genera recomendaciones.
6. El repo no contiene credenciales ni el URI real.
7. Hipótesis a verificar: el notebook corre en menos de unos 3 minutos.

## 9. Hipótesis a verificar (no darlas por ciertas)

- Orden esperado de rendimiento: popularidad < regresión logística ≤ boosting. Si el boosting gana por mucho, revisar el generador por una interacción no intencionada.
- NDCG@5 y AUC deberían coincidir en el orden de los modelos.
- Las magnitudes del generador son valores iniciales; hay que calibrarlas hasta tener una tasa de completación entre 25% y 35%.

## 10. Pendientes abiertos con el DE

- Versión de MLflow de su servidor (para fijar `mlflow` y revisar la API de `log_model`).
- Si el servidor proxea los artefactos o el cliente escribe directo al almacenamiento.
- Acceso del DE al repo privado antes de entregar.

## 11. Pruebas en local

Para probar sin el servidor del DE se puede apuntar a una base SQLite local:

```bash
pip install -r requirements.txt
python scripts/generate_data.py
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
jupyter notebook notebook.ipynb
```

`mlflow.db` y `mlruns/` están en `.gitignore`.
