# mlflow-tracking-demo

Notebook que demuestra **corridas y tracking de modelos en MLflow**. Para tener algo que entrenar y comparar usa un caso **ficticio**: la plataforma e-learning de la Fundación Ayudinga (Panamá) y la pregunta *¿qué curso recomendamos a cada estudiante?* Todos los datos son sintéticos.

> **Estado: terminado y probado en local.** *Restart & Run All* corre sin errores en unos 40 segundos contra un tracking store SQLite. Falta correrlo contra tu servidor (ver [Pendientes contigo](#pendientes-contigo)).

## En 1 minuto

| | |
|---|---|
| **Qué hace** | Entrena 3 modelos, los compara y registra todo en MLflow: 1 run padre, 3 runs hijos y 1 run de reproducibilidad |
| **Qué necesita de ti** | Un tracking server accesible y su URI en `MLFLOW_TRACKING_URI` |
| **Qué no toca** | Tu servidor, la base de metadatos y el almacenamiento de artefactos. No usa Model Registry ni despliega nada |
| **Qué ejecutar** | Solo `notebook.ipynb`. Los datos ya vienen en `data/` |
| **Dependencias** | Python ≥ 3.11 y `requirements.txt` (solo `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `mlflow` y Jupyter) |

## Cómo correrlo (3 pasos)

**1. Entorno**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

**2. Apuntar al servidor.** Copia la plantilla y pon tu URI:

```bash
cp .env.example .env        # Windows: copy .env.example .env
# editar .env:  MLFLOW_TRACKING_URI=http://<host>:<puerto>
```

Alternativa: define la variable de entorno `MLFLOW_TRACKING_URI` antes de abrir Jupyter. Si existe, tiene prioridad sobre el `.env`. Si el servidor exige autenticación, usa `MLFLOW_TRACKING_USERNAME` y `MLFLOW_TRACKING_PASSWORD` (o `MLFLOW_TRACKING_TOKEN`) de la misma forma. `.env` está en `.gitignore`.

**3. Ejecutar.** Abre `notebook.ipynb` desde la raíz del repo y usa **Restart & Run All**.

> **Prueba sin servidor:** `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`. Para ver los runs: `python -m mlflow ui --backend-store-uri sqlite:///mlflow.db` y abrir http://127.0.0.1:5000.

## Qué verás en MLflow

```
course-recommender-demo                 (experimento)
├── model-comparison                    (run padre: best_ndcg_at_5, tags best_model y best_run_id)
│   ├── popularity                      (run hijo)
│   ├── logreg                          (run hijo)
│   └── hgb                             (run hijo)
└── reproducibility-check-<ganador>     (run aparte, tag reproducibility_check=true)
```

Cada run hijo registra:

| Tipo | Contenido |
|---|---|
| Parámetros | `seed`, `test_size`, `k`, `n_train_estudiantes`, `n_test_estudiantes`, `model_name`, `features` e hiperparámetros (`model__*`) |
| Métricas | `roc_auc`, `log_loss`, `precision_at_5`, `ndcg_at_5` (**primaria**), `coverage_at_5` |
| Tags | `model_family`, `data_hash` (huella de los datos), `caso=ficticio` |
| Artefactos | `top5_muestra.csv` (todos) e `importancia_variables.png` (`logreg` y `hgb`) |
| Modelo | `model`: `Pipeline` de scikit-learn con `signature` e `input_example`; recibe datos crudos |

El registro es **manual** (sin `autolog`), para que sepas exactamente qué se escribe en tu servidor.

## Qué hace el notebook, sección por sección

| # | Sección | Qué hace | Si falla… |
|---|---|---|---|
| 0 | Configuración | Lee `.env`/variables de entorno y define `EXPERIMENT_NAME`, `SEED=42` y `K=5` | n/a |
| 1 | Conexión | Imprime la versión de MLflow, consulta el servidor y crea el experimento | Se detiene aquí si falta el URI o el servidor no responde |
| 2 | Carga y validación | Lee los 3 CSV y ejecuta `assert` (tamaños, nulos, llaves, vocabulario, tasa 25–35%) | Se detiene si los datos no cuadran o falta `data/` |
| 3 | Preparación | Une las tablas, crea las variables de cruce y divide 80/20 por estudiante | n/a |
| 4 | Entrenamiento | Run padre y 3 hijos con registro manual | Si no se pueden subir artefactos, falla aquí (ver pendientes) |
| 5 | Selección | Consulta al servidor con `search_runs` y elige el mejor por `ndcg_at_5` | n/a |
| 6 | Recomendaciones | Carga el ganador desde `runs:/<run_id>/model`, verifica sus predicciones y genera el top-5 para 3 estudiantes | Requiere poder **descargar** artefactos |
| 7 | Reproducibilidad | Reentrena el ganador y hace un `assert` de que las 5 métricas coinciden con las registradas | Se detiene si no se reproduce |

## Resultados de la prueba local

Ejecución completa con MLflow 3.17.2, scikit-learn 1.8.0, Python 3.13 y tracking store SQLite. Tardó 39 s.

| Modelo | ROC AUC | Log loss | Precision@5 | **NDCG@5** | Coverage@5 |
|---|---|---|---|---|---|
| `popularity` (baseline) | 0.642 | 0.585 | 0.411 | 0.452 | 0.47 |
| `logreg` | 0.722 | 0.546 | 0.481 | 0.556 | 0.80 |
| `hgb` (**ganador**) | 0.736 | 0.534 | 0.502 | **0.577** | 1.00 |

- Pasan todos los `assert` de datos y de reproducibilidad (las diferencias fueron exactamente 0).
- El modelo cargado desde MLflow da las mismas predicciones que el modelo en memoria.
- Se cumplen las hipótesis de diseño: popularidad < logreg ≤ hgb, y NDCG@5 y AUC ordenan igual los modelos.

Como los datos y la semilla son fijos, en tu servidor deberías obtener **las mismas métricas**. Si salen distintas, revisa las versiones de las librerías.

## Por qué está hecho así

| Decisión | Motivo |
|---|---|
| Datos sintéticos en CSV versionados | Pediste un notebook que funcione, no datos reales. Con los datos congelados el resultado no cambia entre versiones de `numpy` |
| URI por variable de entorno o `.env`, con fail-fast | El URI real y las credenciales nunca entran al repo. Si falta el URI, el error aparece en la celda 1 y no varias celdas después |
| Registro manual, sin `autolog` | Ves exactamente qué se registra y nada se duplica |
| Run padre + hijos | Agrupa una comparación completa y permite elegir el ganador con una sola consulta (`search_runs` filtrando por el padre) |
| Ganador elegido consultando al servidor | Demuestra que lo registrado alcanza para decidir, sin depender de la memoria del notebook |
| Modelo cargado desde `runs:/…` | Comprueba la ida y vuelta completa: subir, descargar y predecir |
| Modelos simples (solo scikit-learn) | El algoritmo no es el objetivo; con 3 modelos hay algo real que comparar |
| `Pipeline` con el preprocesamiento incluido | El modelo guardado recibe datos crudos; no hace falta replicar transformaciones |
| Serialización `skops` con tipos confiables explícitos | Es el formato por defecto de MLflow 3.x y es más seguro que pickle. `HistGradientBoosting` necesita declarar 3 tipos internos de scikit-learn (`SKOPS_TRUSTED_TYPES` en la sección 4) |

El detalle completo (unidad de análisis, generador de datos, métricas y limitaciones) está en [docs/DECISIONES_DATOS.md](docs/DECISIONES_DATOS.md).

## Pendientes contigo

1. **Versión de MLflow de tu servidor.** El cliente se probó con `mlflow==3.17.2`. Con un servidor 2.x puede haber incompatibilidades: MLflow 3 registra los modelos como *LoggedModel*, y los parámetros `name` y `skops_trusted_types` de `log_model` son de 3.x. Con tu versión se fija `requirements.txt` y se ajusta la sección 4 si hace falta.
2. **Artefactos: ¿proxy o escritura directa?** Si el servidor no proxea los artefactos (`--serve-artifacts`), el cliente escribe directo al almacenamiento (S3, GCS, …) y necesita credenciales de ese almacenamiento. Sin ellas, las métricas se registran pero `log_model` y `log_figure` fallan en la sección 4.
3. **Acceso al repo**, que es privado.

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `RuntimeError: MLFLOW_TRACKING_URI no está definida` en la sección 1 | Falta `.env` o la variable. Créala y **reinicia el kernel** (las variables se leen al arrancar) |
| `NameError: experiment` o `BEST_RUN_ID` en secciones posteriores | Se ejecutaron celdas después de un fallo en la sección 1. Corrige esa causa y usa *Restart & Run All* |
| `FileNotFoundError: Faltan archivos de datos` | El notebook se abrió fuera de la raíz del repo o se copió sin `data/` |
| Error al subir o descargar artefactos con métricas ya registradas | Configuración de artefactos del servidor (ver pendiente 2) |

## Limitaciones conocidas

- **Evaluación offline:** solo se conoce el resultado de los 20 cursos mostrados a cada estudiante. Para evaluar, "recomendar" significa ordenar esos 20 y tomar 5. La sección 6 sí puntúa los 60 cursos del catálogo, como se haría en producción.
- **Exposición aleatoria:** no se modela el sesgo de un recomendador previo.
- **Solo arranque en frío:** no se usa historial del estudiante.
- **Relaciones inventadas:** el generador produce señal para la demo; no son hallazgos sobre estudiantes reales.

## Estructura del repo

```
notebook.ipynb            # lo único que se ejecuta (incluye los outputs de la prueba local)
requirements.txt
.env.example              # plantilla de configuración: copiar como .env
data/                     # estudiantes.csv (2,000), cursos.csv (60), eventos.csv (40,000)
scripts/generate_data.py  # genera los CSV con semilla fija (lo ejecuta solo el autor)
docs/DECISIONES_DATOS.md  # decisiones de diseño e implementación y su justificación
docs/backlog/, docs/sprints/  # planificación del trabajo
```

No se versionan (`.gitignore`): `.env` (tu URI y credenciales), `mlflow.db` y `mlruns/` (pruebas locales) ni `.venv/`.

---
Autor: Helio Castillo
