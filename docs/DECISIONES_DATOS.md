# Decisiones de diseño: `mlflow-tracking-demo`

Caso ficticio: plataforma e-learning de la Fundación Ayudinga (Panamá). Todos los datos son sintéticos; no se usa ningún dato real de la fundación.

Etiquetas usadas en este documento:
- **[Hecho]**: sostenido por el planteamiento del proyecto o por conocimiento técnico estable.
- **[Supuesto]**: simplificación asumida a propósito.
- **[Hipótesis]**: expectativa que debe verificarse al correr el código.

---

## 0. Registro de decisiones

| ID | Decisión | Estado |
|---|---|---|
| D1 | Unidad de análisis: recomendación mostrada. Target: `completo_30d` | Cerrada |
| D2 | Tres tablas: `estudiantes` (6 columnas), `cursos` (5), `eventos` (3). Solo cursos, sin rutas | Cerrada |
| D2d | Exposición: 20 cursos al azar por estudiante | Cerrada |
| D3 | Clasificación puntual: P(`completo_30d`) por par, ordenar por estudiante | Cerrada |
| D4 | División por estudiante, 80/20, sin validación | Cerrada |
| D5 | Métricas: ROC AUC, log loss, Precision@5, NDCG@5, Coverage@5. Primaria: NDCG@5 | Cerrada |
| D6 | 2,000 estudiantes, 60 cursos, 40,000 filas | Cerrada |
| D7 | Generador aditivo con motivación latente | Cerrada (magnitudes a calibrar) |
| D8 | Modelos: popularidad (logit sobre `course_id`), regresión logística, `HistGradientBoostingClassifier` | Cerrada |
| D9 | Convención MLflow: padre + 3 hijos, registro manual | Cerrada |
| D10 | Repo con notebook, script generador, CSV versionados y docs | Cerrada |
| D11 | Model Registry: **descartado** | Cerrada |

---

## 1. Propósito y alcance

- **[Hecho]** El objetivo es demostrar corridas y tracking en MLflow. El Data Engineer (DE) no evalúa el realismo de los datos ni el tipo de algoritmo; pide un notebook que funcione.
- **[Hecho]** El DE se encarga de la infraestructura (tracking server). El URI queda como placeholder.
- **Pregunta de negocio del caso:** ¿qué curso deberíamos recomendar a cada estudiante?
- **Fuera de alcance (a propósito):** rutas de aprendizaje, prerrequisitos, historial del estudiante, Model Registry, despliegue o serving, experimento A/B, filtrado colaborativo y rankers dedicados.

## 2. Unidad de análisis y variable objetivo (D1)

| Decisión | Detalle | Justificación |
|---|---|---|
| Unidad de análisis | Una fila por **recomendación mostrada** (estudiante, curso) | Con solo interacciones no se distingue un curso rechazado de uno nunca visto. Con recomendaciones mostradas, el negativo significa "se mostró y no se completó" |
| Variable objetivo | `completo_30d`: 1 si el estudiante completó el curso en los 30 días posteriores a la recomendación | Alineada con la misión educativa de la fundación. Clic o inicio no garantizan aprendizaje |
| Ventana | 30 días fijos para todas las filas | Evita censura. Una recomendación reciente aparecería como 0 solo por falta de tiempo |

- **[Supuesto]** Todas las filas tienen ventana completa por construcción. No se simulan fechas. En un sistema real, las recomendaciones con menos de 30 días de observación se **excluirían** del entrenamiento; no se rellenan con 0.
- **[Hipótesis]** Los cursos cortos tienden a completarse más. Por eso `duracion_horas` entra como variable explícita.

## 3. Estructura de tablas (D2)

| Tabla | Se usa en | Contenido |
|---|---|---|
| `estudiantes` | Entrenamiento y recomendación | Perfil del estudiante |
| `cursos` | Entrenamiento y recomendación | Catálogo |
| `eventos` | Solo entrenamiento | Recomendaciones mostradas y resultado |

### 3.1 `estudiantes` (2,000 filas)

| Columna | Valores | Distribución inicial |
|---|---|---|
| `student_id` | E0001… | único |
| `horas_semana` | entero 1 a 15 | concentrada en 2 a 6, cola hasta 15 |
| `objetivo_aprendizaje` | `empleo`, `mejorar_trabajo`, `certificacion`, `proyecto_personal` | desigual, no uniforme |
| `nivel_experiencia` | `principiante`, `intermedio`, `avanzado` | 50% / 35% / 15% |
| `area_interes` | `analisis_datos`, `machine_learning`, `sql_bases_datos`, `python`, `visualizacion` | desigual, no uniforme |
| `plan` | `gratis`, `premium` | 75% / 25% |

- **[Supuesto]** Las distribuciones son plausibles pero inventadas; buscan evitar un dataset uniforme.
- Solo atributos **conocidos el día que llega el estudiante**. Se excluyen historial, racha y tiempo en plataforma, porque un estudiante nuevo no los tiene (fuga de información en arranque en frío).
- **Excluidos a propósito:** `rol_objetivo` (se solapa con área y objetivo), `pais` e `idioma` (casi constantes en un caso panameño), edad y género (no necesarios y abren un tema de equidad fuera de alcance).

### 3.2 `cursos` (60 filas)

| Columna | Valores |
|---|---|
| `course_id` | C001…C060 |
| `titulo` | generado, por ejemplo "SQL básico 2" (cosmético, hace legible la demo) |
| `categoria` | mismos 5 valores que `area_interes` |
| `nivel` | mismos 3 valores que `nivel_experiencia` |
| `duracion_horas` | entero 2 a 20 |

- Aproximadamente 12 cursos por categoría, repartidos entre los 3 niveles.
- **[Supuesto]** La duración crece con el nivel (ejemplo: principiante 2–8 h, intermedio 6–14 h, avanzado 10–20 h).
- **Vocabulario compartido:** `categoria` y `nivel` usan exactamente los mismos valores que `area_interes` y `nivel_experiencia`, para poder derivar variables de cruce.
- **Excluidos a propósito:** `ruta_id`, prerrequisitos, `formato` (señal débil frente al costo) y `popularidad`. Esta última es derivada de los eventos; guardarla en el catálogo causaría fuga de información.

### 3.3 `eventos` (40,000 filas)

| Columna | Descripción |
|---|---|
| `student_id`, `course_id` | Par recomendado |
| `completo_30d` | Variable objetivo (0 o 1) |

## 4. Exposición (D2d)

- Cada estudiante recibe **20 cursos elegidos al azar**, sin repetir. Total: 2,000 × 20 = 40,000 filas.
- **[Supuesto]** Se simula un sistema previo exploratorio. En la realidad, un recomendador previo sesga qué se muestra y a quién. Se evita para no complicar el notebook. Debe constar en el README.
- Se requieren al menos K=5 recomendaciones por estudiante para que existan las métricas de ranking; con 20 filas fijas se obtiene una matriz regular.

## 5. Generador de `completo_30d` (D7)

Puntuación aditiva convertida en probabilidad con la sigmoide, y resultado sorteado:

```
score = b0
      + 1.2  * area_coincide
      + efecto_brecha_nivel
      - 0.3  * min(carga, 6)
      + 0.5  * (plan == premium)
      + efecto_objetivo
      + u_estudiante

p = sigmoid(score)
completo_30d ~ Bernoulli(p)
```

- `area_coincide` = 1 si `categoria` del curso es igual a `area_interes` del estudiante.
- `brecha_nivel` = nivel del curso − nivel del estudiante, con escala ordinal principiante=0, intermedio=1, avanzado=2. Rango: −2 a +2.
- `efecto_brecha_nivel`: +1 → −0.8; +2 → −2.0; −1 o −2 → −0.5; 0 → 0.
- `carga` = `duracion_horas / horas_semana`.
- `efecto_objetivo`: `empleo` y `certificacion` → +0.4; `proyecto_personal` → −0.2; `mejorar_trabajo` → 0.
- `u_estudiante` ~ Normal(0, 0.5): **motivación latente**, no aparece en ninguna tabla.
- `b0` se calibra para cumplir la tasa global objetivo.

| Componente | Justificación |
|---|---|
| Coincidencia de área | Un curso del interés propio se termina con más facilidad |
| Brecha de nivel | Uno muy por encima del nivel se abandona; uno por debajo aburre, con penalización menor |
| Carga | Quien tiene pocas horas completa menos cursos largos |
| Plan premium | **[Hipótesis]** mayor compromiso asociado al pago |
| Objetivo | Un objetivo con consecuencias concretas sostiene la constancia |
| Motivación latente | Representa lo que no se mide. Sin ella, un buen modelo acertaría casi siempre, lo cual no es realista |

**Decisiones de diseño intencionales:**
1. La carga es una **razón entre dos columnas**. La regresión logística no la capta con columnas crudas; el gradient boosting sí. Así la comparación entre modelos arroja diferencias visibles de forma natural.
2. Las magnitudes son **valores iniciales**, no verdades. Se calibran para cumplir la sección 6.
3. Una sola constante `SEED` controla todo el generador.

## 6. Validación de datos

Se implementan como `assert` al cargar los CSV en el notebook (y como reporte al generarlos):

- Tasa global de `completo_30d` entre 25% y 35%.
- Cada estudiante con exactamente 20 filas; sin pares (`student_id`, `course_id`) duplicados; sin nulos.
- Valores de `categoria`, `nivel`, `area_interes` y `nivel_experiencia` dentro del vocabulario definido.
- **[Hipótesis]** Orden esperado de rendimiento: popularidad < regresión logística ≤ gradient boosting. Si no se cumple, se recalibra el generador. Si el boosting gana por mucho, probablemente se coló una interacción no intencional.

## 7. Modelado y evaluación

### 7.1 Planteamiento (D3)

Clasificación puntual: se predice P(`completo_30d`) por par (estudiante, curso) y se ordenan los cursos de cada estudiante de mayor a menor probabilidad, quedándose con los K primeros. Se descartan los rankers dedicados (dependencias extra) y el filtrado colaborativo (requiere historial, que no usamos). Los tres modelos comparten la misma interfaz de salida.

### 7.2 Modelos (D8)

| Modelo | Entrada | Rol |
|---|---|---|
| Popularidad | Solo `course_id` (one-hot) con regresión logística, equivalente a la tasa por curso | Baseline. Evita escribir una clase propia que pueda dar problemas al serializar |
| Regresión logística | Columnas de las tres tablas más `area_coincide` y `brecha_nivel` | Modelo simple e interpretable |
| `HistGradientBoostingClassifier` | Mismas variables que la regresión logística | Capta no linealidades, como la carga, sin que se le entregue hecha |

- La variable `carga` **no se entrega** como feature a ningún modelo. Es la que debería permitir al boosting ganar.
- Cada modelo es un `Pipeline` de `scikit-learn` que incluye el preprocesamiento; el artefacto guardado recibe datos crudos.

### 7.3 División (D4)

- `GroupShuffleSplit` por `student_id`, 80/20: 1,600 estudiantes (32,000 filas) para entrenamiento y 400 (8,000 filas) para prueba.
- **Razón decisiva [Hecho]:** las métricas de ranking necesitan la lista completa de 20 filas de cada estudiante. Una división aleatoria por fila dejaría unas 4 por estudiante de prueba.
- **Razón complementaria [Hipótesis, magnitud sin verificar]:** evita fuga de información, porque los atributos del estudiante se repiten en sus 20 filas.
- Sin conjunto de validación porque no se ajustan hiperparámetros. Si más adelante se ajustan, habría que añadir una segunda división.

### 7.4 Métricas (D5)

| Métrica | Qué mide |
|---|---|
| ROC AUC | Calidad de las probabilidades (todos los pares mezclados) |
| Log loss | Acierto de las probabilidades |
| Precision@5 | De los 5 cursos recomendados, cuántos se completaron |
| NDCG@5 | Igual, premiando los aciertos más arriba en la lista |
| Coverage@5 | Porcentaje del catálogo que aparece en los top-5 de los estudiantes de prueba |

- **Primaria para elegir el ganador: NDCG@5.** Mide exactamente qué poner al inicio de una lista corta y respeta el orden. AUC se registra como control. **[Hipótesis]** ambas deberían coincidir en el orden de los modelos; si no, es un hallazgo.
- K = 5, constante configurable.
- Implementación sugerida: `ndcg_score` de `scikit-learn` sobre una matriz de 400 × 20; Precision@5 manual.
- **Limitación offline [Hecho]:** solo se conoce el resultado de los 20 cursos mostrados. En la evaluación, "recomendar" equivale a ordenar esos 20 cursos y tomar los 5 primeros. En producción se elegiría entre los 60, pero de los 40 restantes no se sabe qué habría pasado. Debe constar en el README.

## 8. Convención de MLflow (D9)

| Elemento | Valor |
|---|---|
| Experimento | `course-recommender-demo` |
| Run padre | `model-comparison` |
| Runs hijos (anidados) | `popularity`, `logreg`, `hgb` |
| Parámetros | `seed`, `test_size`, `k`, `n_train_estudiantes`, `n_test_estudiantes` y los hiperparámetros de cada modelo |
| Métricas | `roc_auc`, `log_loss`, `precision_at_5`, `ndcg_at_5`, `coverage_at_5` |
| Tags | `model_family`, `data_hash`, `caso=ficticio` |
| Artefactos | `top5_muestra.csv` (5 estudiantes de prueba, con títulos legibles); gráfico de importancia de variables solo en logreg y boosting |
| Modelo | `log_model` con signature e input example |
| Run padre, al cierre | `best_ndcg_at_5` y nombre del modelo ganador |

- **Registro manual, sin `autolog`**: el DE ve exactamente qué se registra y se evita registrar cosas dobles.
- `data_hash` se calcula sobre los datos cargados para dar linaje; no se compara contra un valor esperado.
- **Reproducibilidad:** se reentrena el ganador con la misma semilla en un run con tag `reproducibility_check`, y un `assert` (con tolerancia numérica) verifica que `ndcg_at_5` coincide.
- **Conexión:** `MLFLOW_TRACKING_URI` se lee de una variable de entorno, con el placeholder acordado con el DE. Una celda posterior comprueba la conexión y falla con un mensaje claro. Si el servidor requiere autenticación, las credenciales van solo en variables de entorno.

## 9. Estructura del repo y del notebook (D10)

```
mlflow-tracking-demo/
├── notebook.ipynb          # único archivo que corre el DE
├── README.md
├── requirements.txt
├── CLAUDE.md
├── .gitignore              # mlruns/, mlflow.db, .env, .ipynb_checkpoints/
├── data/                   # fuente de verdad, versionada
│   ├── estudiantes.csv
│   ├── cursos.csv
│   └── eventos.csv
├── scripts/
│   └── generate_data.py    # lo ejecuta solo el autor
└── docs/
    └── DECISIONES_DATOS.md
```

**Política de datos.** Los CSV son la fuente de verdad, el notebook los carga y los valida, y `scripts/generate_data.py` los produce con una semilla fija. Razones: el notebook se centra en MLflow; los datos congelados evitan el riesgo de que cambie el flujo de números aleatorios entre versiones de `numpy`; y se parece más a un pipeline real. Costo conocido: si el DE copia solo el `.ipynb`, no encuentra los datos. Mitigación: celda inicial que verifica la existencia de `data/` y falla con mensaje claro, y entrega del repo completo.

**Secciones del notebook:**

| # | Sección | Contenido |
|---|---|---|
| 0 | Configuración | URI (variable de entorno con placeholder), `EXPERIMENT_NAME`, `SEED`, `K` |
| 1 | Conexión | Imprime `mlflow.__version__` y comprueba el servidor |
| 2 | Carga y validación | Lee los CSV y ejecuta los `assert` de la sección 6 |
| 3 | Preparación | `merge`, variables de cruce y división por estudiante |
| 4 | Entrenamiento | Run padre y tres hijos, con registro manual |
| 5 | Selección | Mejor modelo con `search_runs`, ordenado por `ndcg_at_5` |
| 6 | Recomendaciones | Carga del modelo ganador desde `runs:/<run_id>/model` y top-5 para 3 estudiantes |
| 7 | Reproducibilidad | Reentrenamiento y `assert` |

Cada sección lleva una celda de texto que explica qué hace y por qué.

**Convenciones:** textos y comentarios en español, columnas en español sin tildes, código en inglés. `mlflow` no se fija en `requirements.txt` hasta conocer la versión del servidor del DE; las demás librerías se fijan a la versión con la que se pruebe.

**Criterios de aceptación:**
1. "Restart & Run All" corre sin errores contra el servidor del DE.
2. Aparece un experimento con un run padre y tres hijos.
3. Cada hijo tiene sus 5 métricas, parámetros, tags, artefactos y modelo con signature.
4. Todos los `assert` (datos y reproducibilidad) pasan.
5. El modelo ganador se carga desde su run y genera recomendaciones.
6. El repo no contiene credenciales ni el URI real.
7. **[Hipótesis]** El notebook completo corre en menos de unos 3 minutos.

## 10. Model Registry: descartado (D11)

El DE pidió corridas y tracking; el registry no entra en ese pedido y es la parte que más depende de la configuración de su servidor. Se retiró por completo, sin flag. Si el DE lo solicita, se añade una sección posterior (registrar el ganador y asignarle un alias), sin afectar al resto del notebook.

## 11. Limitaciones conocidas

- Solo arranque en frío: no se usa historial del estudiante.
- Exposición aleatoria: no se modela el sesgo de un recomendador previo.
- Sin dimensión temporal ni censura simulada.
- Solo cursos; sin rutas ni prerrequisitos.
- Las relaciones causales son inventadas y sirven únicamente para producir señal en la demo; no deben leerse como hallazgos sobre estudiantes reales.

## 12. Pendientes abiertos

| Pendiente | Responsable | Impacto |
|---|---|---|
| Versión de MLflow del servidor del DE | DE, vía el autor | Fijar `mlflow` en `requirements.txt` y revisar la API de `log_model` |
| Cómo maneja el servidor los artefactos (proxy o escritura directa) | DE | Si no se proxean, `log_model` y `log_artifact` pueden fallar desde el cliente aunque las métricas sí se registren |
| Acceso del DE al repo privado | Autor | Necesario antes de entregar |

## 13. Decisiones de implementación (notebook terminado, 2026-11-18)

Decisiones tomadas al escribir el notebook que no estaban fijadas en las secciones anteriores.

| Tema | Decisión | Justificación |
|---|---|---|
| Entrada de los modelos | Los 3 modelos reciben el **mismo DataFrame crudo** (`course_id` + 6 categóricas + 4 numéricas); cada `Pipeline` elige sus columnas | La sección 6 carga cualquier ganador y le pasa la misma entrada. La signature es idéntica en los 3 runs |
| `course_id` | Solo lo usa popularidad. `logreg` y `hgb` **no** lo reciben | "Mismas variables, salvo popularidad". Con `course_id`, los otros dos modelos también aprenderían popularidad por curso y se mezclarían los roles |
| Numéricas como `float` | `horas_semana`, `duracion_horas`, `area_coincide` y `brecha_nivel` se convierten a `float` | Evita el aviso de MLflow sobre columnas enteras en la signature |
| Preprocesamiento | `logreg`: one-hot + `StandardScaler`. `hgb`: `OrdinalEncoder` + soporte categórico nativo | Cada modelo recibe la codificación que le conviene, siempre dentro del `Pipeline` |
| `hgb` sin `early_stopping` | `early_stopping=False`, `max_iter=300` | Con más de 10,000 filas, scikit-learn activa por defecto una validación interna; se apaga para respetar D4 ("sin validación") |
| Serialización | `skops` (por defecto en MLflow 3.x) con `skops_trusted_types` explícitos solo para `hgb` | Se mantiene el formato seguro. **Desvío del backlog:** T-010 proponía `cloudpickle`; se descartó porque bastaba con declarar 3 tipos internos de scikit-learn |
| Importancia de variables | Importancia por permutación (caída de ROC AUC, 5 repeticiones) sobre las variables crudas | Es el mismo método para `logreg` y `hgb` (que no tiene `feature_importances_`), y se lee en términos de columnas originales, no codificadas |
| Selección del ganador | `search_runs` filtrando `tags.mlflow.parentRunId`; luego se reabre el run padre para registrar `best_ndcg_at_5`, `best_model` y `best_run_id` | El ganador sale de lo registrado en el servidor, no de la memoria del notebook |
| Recomendaciones (sección 6) | Se puntúan los **60 cursos** del catálogo; la columna `mostrado` marca los 20 expuestos | Muestra el uso real. Antes, se verifica que el modelo cargado reproduce las predicciones del entrenado (tolerancia `1e-12`) |
| Run de reproducibilidad | Run aparte (fuera del padre) `reproducibility-check-<modelo>`, con tags `reproducibility_check=true` y `reproduces_run_id`. Se comparan las **5** métricas contra las del servidor, con tolerancia `1e-9` | Así no compite en la comparación y se mantiene "1 padre + 3 hijos" |
| Configuración | El notebook lee `.env` (sin pisar variables ya definidas); en el repo se versiona `.env.example` | No depende de cómo el editor o la terminal carguen las variables (en VS Code el kernel no veía la variable) |
| Datos con outputs | El notebook se versiona con los outputs de la prueba local | Evidencia para el DE de una ejecución completa sin errores |

**Resultado de la prueba local** (MLflow 3.17.2, scikit-learn 1.8.0, SQLite; 39 s): NDCG@5 = 0.452 (popularidad), 0.556 (logreg) y 0.577 (hgb, ganador). Se cumplen las hipótesis de la sección 6 (orden de modelos; NDCG@5 y AUC coinciden).
