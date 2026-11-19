# Backlog: mlflow-tracking-demo

Ordenado por dependencia y riesgo. Estimaciones = **hipótesis**, se recalibran con horas reales.
Estados: Backlog → Ready → En curso → En revisión → Hecho. WIP máximo: 2.

Estado inicial verificado el 2026-11-15 contra el repo (no contra memoria):
- Datos: 2,000 estudiantes, 60 cursos, 40,000 filas; tasa `completo_30d` = 30.1%; sin duplicados ni nulos; 20 filas por estudiante.
- `notebook.ipynb`: vacío (0 celdas).

Actualización 2026-11-18: notebook completo; *Restart & Run All* sin errores en local (39 s). Solo queda T-018 (coordinación con el DE).

| ID | Ticket | Épica | Estado | Riesgo | Est. (hip.) | Depende de |
|---|---|---|---|---|---|---|
| T-001 | Repo, carpetas, `.gitignore`, `requirements.txt`, venv (Python ≥ 3.11) | Setup | Hecho (2026-11-18) | Bajo | 1 h | n/a |
| T-002 | Esqueleto MLflow: celdas 0 y 1 (URI por env var, versión, fail-fast) y run trivial en SQLite | MLflow | Hecho (2026-11-18) | **Alto** | 1–2 h | T-001 |
| T-003 | `scripts/generate_data.py` con `SEED`, 3 CSV y reporte | Datos | Hecho (commit 9f4d31d) | Medio | 2–3 h | T-001 |
| T-004 | Calibrar generador (tasa 25–35%, sin duplicados/nulos) | Datos | Hecho (tasa 30.1%) | **Alto** | 1–2 h | T-003 |
| T-005 | Notebook sección 2: carga de CSV y `assert` de validación | Notebook | Hecho (2026-11-18) | Bajo | 1 h | T-004 |
| T-006 | Sección 3: `merge`, `area_coincide`, `brecha_nivel`, `GroupShuffleSplit` | Notebook | Hecho (2026-11-18) | Medio | 1–2 h | T-005 |
| T-007 | Métricas: ROC AUC, log loss, P@5, NDCG@5, Coverage@5 (matriz 400×20) | Modelado | Hecho (2026-11-18) | Medio | 2 h | T-006 |
| T-008 | Run hijo `popularity` completo | MLflow | Hecho (2026-11-18) | Medio | 1–2 h | T-002, T-007 |
| T-009 | Run hijo `logreg` | MLflow | Hecho (2026-11-18) | Bajo | 1 h | T-008 |
| T-010 | Run hijo `hgb` (skops con `skops_trusted_types`; ver DECISIONES §13) | MLflow | Hecho (2026-11-18) | Medio | 1 h | T-008 |
| T-011 | Run padre `model-comparison`, artefactos y tags | MLflow | Hecho (2026-11-18) | Medio | 2 h | T-009, T-010 |
| T-012 | Sección 5: mejor modelo con `search_runs` por `ndcg_at_5` | MLflow | Hecho (2026-11-18) | Bajo | 1 h | T-011 |
| T-013 | Sección 6: cargar ganador y top-5 para 3 estudiantes | Notebook | Hecho (2026-11-18) | Medio | 1–2 h | T-012 |
| T-014 | Sección 7: reproducibilidad con `assert` y tolerancia | Notebook | Hecho (2026-11-18) | Bajo | 1 h | T-012 |
| T-015 | Verificar hipótesis (orden de modelos, NDCG@5 vs AUC) | Análisis | Hecho (2026-11-18) | Medio | 1 h | T-011 |
| T-016 | Versiones finales, "Restart & Run All" desde cero, medir tiempo | Cierre | Hecho (2026-11-18) | Medio | 1 h | T-014 |
| T-017 | README (cómo correr, supuestos, limitación offline, Python) | Cierre | Hecho (2026-11-18) | Bajo | 1 h | T-016 |
| T-018 | Coordinar con el DE: versión del servidor, artefactos, acceso al repo | Entrega | Backlog | **Alto** | 1–2 h + espera | T-016 |

Por qué T-002 primero: es lo que más depende del entorno y de la versión de MLflow.
