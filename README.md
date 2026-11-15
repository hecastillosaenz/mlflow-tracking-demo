# mlflow-tracking-demo

Notebook que demuestra **corridas y tracking de modelos en MLflow**, usando un caso ficticio: la plataforma e-learning de la Fundación Ayudinga (Panamá) y la pregunta *¿qué curso recomendamos a cada estudiante?*

> **Estado:** en desarrollo. Datos y generador listos; el notebook se está construyendo. La sección de resultados se completará al terminar.

## En 1 minuto (para el DE)

| | |
|---|---|
| **Qué hace** | Entrena 3 modelos, los compara y registra todo en MLflow: 1 run padre + 3 runs hijos |
| **Qué necesita de tu infraestructura** | Solo un tracking server accesible. El notebook se conecta con `MLFLOW_TRACKING_URI` |
| **Qué no toca** | Servidor, base de metadatos y almacenamiento de artefactos son tuyos. No usa Model Registry |
| **Qué ejecutar** | Solo `notebook.ipynb`. Los datos ya vienen en `data/` |
| **Datos** | 100% sintéticos, sin datos reales de la fundación |

## Por qué está hecho así

- **Datos sintéticos y fijos (CSV versionados).** Pediste un notebook que funcione, no datos reales. Los CSV congelados evitan que el resultado cambie entre versiones de `numpy`. Los produce `scripts/generate_data.py` con semilla fija.
- **Registro manual, sin `autolog`.** Verás exactamente qué se registra y nada se duplica.
- **URI por variable de entorno.** Ninguna credencial ni URI real vive en el repo. Si la variable falta o sigue siendo el placeholder, el notebook falla en la celda 1 con un mensaje claro.
- **Modelos simples (solo `scikit-learn`).** El algoritmo no es el objetivo; sirve para tener algo que comparar y registrar.

## Cómo correrlo

```bash
python -m venv .venv
# activar el entorno (Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Define el URI **antes** de abrir Jupyter (si no, el kernel no lo verá):

```bash
# Linux/Mac/Git Bash
export MLFLOW_TRACKING_URI=http://<URI_DEL_SERVIDOR>
# PowerShell
$env:MLFLOW_TRACKING_URI = "http://<URI_DEL_SERVIDOR>"

jupyter notebook notebook.ipynb
```

Requiere **Python 3.11 o superior** (por `numpy 2.3` y `scikit-learn 1.8`).

**Prueba local sin servidor:** `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`, y para ver los runs: `mlflow ui --backend-store-uri sqlite:///mlflow.db`.

## Qué verás en MLflow

| Elemento | Valor |
|---|---|
| Experimento | `course-recommender-demo` |
| Run padre | `model-comparison` (al cierre: `best_ndcg_at_5` y nombre del ganador) |
| Runs hijos (anidados) | `popularity`, `logreg`, `hgb` |
| Parámetros | `seed`, `test_size`, `k`, `n_train_estudiantes`, `n_test_estudiantes` e hiperparámetros del modelo |
| Métricas | `roc_auc`, `log_loss`, `precision_at_5`, `ndcg_at_5`, `coverage_at_5` |
| Tags | `model_family`, `data_hash`, `caso=ficticio` |
| Artefactos | `top5_muestra.csv` (todos); gráfico de importancia de variables (`logreg` y `hgb`) |
| Modelo | `log_model` con `signature` e `input_example` |

**Reproducibilidad:** el ganador se reentrena con la misma semilla en un run con tag `reproducibility_check`, y un `assert` verifica que `ndcg_at_5` coincide.

## El caso en breve

- **Datos:** 2,000 estudiantes, 60 cursos y 40,000 recomendaciones mostradas (20 por estudiante).
- **Objetivo del modelo:** predecir si el estudiante completa el curso en 30 días (`completo_30d`).
- **Cómo se recomienda:** se ordenan los 20 cursos mostrados a cada estudiante por probabilidad y se toman los 5 primeros.
- **Métrica principal:** NDCG@5.
- **Modelos:** popularidad (baseline), regresión logística y `HistGradientBoostingClassifier`.
- **Evaluación:** división 80/20 por estudiante.

## Limitaciones conocidas

- **Evaluación offline:** solo se conoce el resultado de los 20 cursos mostrados. "Recomendar" aquí es ordenar esos 20 y tomar 5; no se sabe qué habría pasado con los otros 40 cursos del catálogo.
- **Exposición aleatoria:** se simula un sistema previo exploratorio; no se modela el sesgo de un recomendador real.
- **Solo arranque en frío:** no se usa historial del estudiante.
- **Relaciones inventadas:** el generador de datos produce señal para la demo; no son hallazgos sobre estudiantes reales.

## Compatibilidad y pendientes contigo

- `requirements.txt` fija `mlflow==3.17.2` **de forma provisional**. Necesito la **versión de tu servidor** para confirmarla. En MLflow 2.x cambia un parámetro de `log_model` (`artifact_path` en vez de `name`).
- Necesito saber si el servidor **proxea los artefactos** o si el cliente escribe directo al almacenamiento. Si no se proxean, `log_model` y `log_artifact` pueden fallar aunque las métricas sí se registren.
- Acceso al repo (privado) antes de la entrega.

## Estructura

```
notebook.ipynb          # lo único que se ejecuta
requirements.txt
data/                   # estudiantes.csv, cursos.csv, eventos.csv
scripts/generate_data.py  # genera los CSV (lo ejecuta solo el autor)
docs/DECISIONES_DATOS.md  # decisiones de diseño y su justificación
```

## Resultados

_Pendiente: se completará al terminar el notebook (comparación de modelos, ganador, tiempo de ejecución)._

---
Autor: Helio Castillo
