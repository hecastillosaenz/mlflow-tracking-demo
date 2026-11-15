# T-002: Conectar el notebook a MLflow y registrar un run de prueba en SQLite local

**Épica:** MLflow   **Riesgo:** alto   **Estimación (hipótesis):** 1–2 h (sin límite de tiempo: lo importante es entender)
**Depende de:** T-001 (hecho) | **Bloquea a:** T-008, T-009, T-010, T-011

## 1. Por qué importa

El DE solo pide "un notebook que funcione" para hacer tracking en MLflow. Este ticket construye esa base: el notebook sabe **a qué servidor hablar**, **falla con un mensaje claro** si no puede, y demuestra que **un run se guarda y se ve en la interfaz**. Es el de más riesgo porque depende del entorno (versión de MLflow, Windows, variables de entorno), y todo lo demás se apoya en él.

## 2. Conceptos previos

> Marca con ✅ lo que ya dominas y con ❓ lo que no. Si algo te suena confuso, dímelo y lo explico distinto antes de seguir.

### 2.1 Qué es MLflow y para qué sirve aquí
MLflow es una herramienta para **registrar lo que pasa al entrenar modelos**: con qué datos, con qué parámetros, qué resultados dio, y guardar el modelo. Piensa en un **cuaderno de laboratorio automático**: cada vez que entrenas, anota todo, y luego puedes comparar experimentos sin depender de tu memoria.

### 2.2 Tracking server vs. backend store vs. artifact store
Tres piezas distintas (el DE se encarga de ellas; tú solo necesitas entenderlas):
- **Tracking server:** el programa al que tu notebook le "habla" (por HTTP). Recibe lo que registras.
- **Backend store:** donde se guardan los *metadatos* (parámetros, métricas, tags). Puede ser una base de datos (SQLite, PostgreSQL...).
- **Artifact store:** donde se guardan los *archivos* (modelos, CSV, gráficos). Puede ser una carpeta, S3, etc.

En local, el "servidor" es simplemente un archivo SQLite (`mlflow.db`) y una carpeta `mlruns/`. En el servidor del DE será otra cosa, pero **tu código no cambia**: solo cambia el URI.

### 2.3 Tracking URI
Es la "dirección" donde MLflow guarda todo. Ejemplos:
- `sqlite:///mlflow.db` → archivo local (tres barras = ruta relativa).
- `http://servidor:5000` → un servidor remoto.

Se fija con `mlflow.set_tracking_uri(...)` y se consulta con `mlflow.get_tracking_uri()`.

### 2.4 Variables de entorno
Son valores que el sistema operativo guarda **fuera de tu código**. Sirven para que el URI real (o credenciales) **nunca estén en el repo**. En Python se leen con `os.environ.get("NOMBRE", "valor_por_defecto")`.

Cómo se definen (depende de la terminal):
- **PowerShell (Windows):** `$env:MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"`
- **Git Bash / Linux / Mac:** `export MLFLOW_TRACKING_URI=sqlite:///mlflow.db`

⚠️ Una variable definida en una terminal **solo existe en esa terminal y en los programas que lances desde ella**. Si abres Jupyter o VS Code desde otro lado, el notebook no la verá. Es la trampa nº 1 de este ticket.

### 2.5 Experimento, run y parámetros/métricas
- **Experimento:** una carpeta lógica que agrupa runs de un mismo problema (`mlflow.set_experiment("nombre")`; si no existe, lo crea).
- **Run:** *una* ejecución registrada (un entrenamiento). Se abre con `with mlflow.start_run(run_name="..."):` y se cierra solo al salir del bloque `with`.
- **Parámetro:** un valor de entrada que no cambia dentro del run (`mlflow.log_param("seed", 42)`).
- **Métrica:** un resultado numérico (`mlflow.log_metric("score", 0.83)`).

(Run **anidado**, tags, artefactos y signature aparecen en tickets posteriores; no los uses todavía.)

### 2.6 Fail-fast
Principio: si algo va a fallar, que falle **al inicio y con un mensaje que explique el porqué**, no 40 celdas después con un error críptico. Aquí: si el URI sigue siendo el placeholder o el servidor no responde, el notebook se detiene con un mensaje claro.

En Python se logra con `raise RuntimeError("mensaje claro")` o con `try/except`.

### 2.7 Qué investigar (términos de búsqueda)
- Documentación de MLflow → sección **"Tracking"** y **"Quickstart"** (mlflow.org/docs).
- `mlflow.set_tracking_uri`, `mlflow.set_experiment`, `mlflow.start_run`, `mlflow.log_param`, `mlflow.log_metric`, `mlflow.search_experiments`.
- "MLflow backend store vs artifact store".
- "Python os.environ.get" y "Python try except raise".

## 3. Qué hay que lograr (resultado, no receta)

1. Un notebook con una **celda 0 (configuración)** y una **celda 1 (conexión)**, cada una precedida por una celda de texto en español que explique qué hace y por qué.
2. Si `MLFLOW_TRACKING_URI` no está definida o sigue siendo el placeholder, la celda 1 **se detiene con un mensaje claro** (no un error críptico de MLflow).
3. Con `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`, la celda imprime la versión de MLflow y el URI, y confirma que puede hablar con el backend.
4. Un **run de prueba** (experimento aparte, descartable) se ve en la interfaz de MLflow.

## 4. Pasos

> Cada paso ≤ 20–30 min. Trabaja en `notebook.ipynb`.

**Paso 1: Confirmar el entorno.**
- Qué hacer: en la terminal, activar `.venv` y ejecutar `python -c "import mlflow; print(mlflow.__version__)"`.
- Cómo comprobar: imprime `3.17.2`. Si falla, dime el error antes de seguir.

**Paso 2: Celda de texto + celda 0 (configuración).**
- Qué hacer: definir constantes en MAYÚSCULAS: `PLACEHOLDER_URI`, `EXPERIMENT_NAME = "course-recommender-demo"`, `SEED`, `K`, y leer el URI desde la variable de entorno con el placeholder como valor por defecto.
- Idea de sintaxis (ejemplo genérico, no es tu solución):
  ```python
  import os
  MI_CONSTANTE = 7
  valor = os.environ.get("MI_VARIABLE", "valor_por_defecto")
  ```
- Cómo comprobar: al ejecutar la celda, imprime el URI leído (sin secretos). Sin variable definida, debe verse el placeholder.

**Paso 3: Celda de texto + celda 1 (conexión), parte A: validar el URI.**
- Qué hacer: si el URI es igual al placeholder, detener con un mensaje que diga **qué pasó y qué hacer** ("Define MLFLOW_TRACKING_URI antes de abrir Jupyter").
- Idea de sintaxis:
  ```python
  if condicion_mala:
      raise RuntimeError("Qué pasó. Qué hacer.")
  ```
- Cómo comprobar: sin variable definida, la celda se detiene con tu mensaje.

**Paso 4: Celda 1, parte B: conectar y comprobar.**
- Qué hacer: llamar a `mlflow.set_tracking_uri(uri)`, imprimir `mlflow.__version__`, y hacer una operación **barata de lectura** que obligue a hablar con el backend (pista: `mlflow.search_experiments()`). Envolverla en `try/except` y, si falla, relanzar un error claro que incluya el URI usado.
- Cómo comprobar: con `sqlite:///mlflow.db` imprime versión y URI sin errores. Con un URI inventado (`http://no-existe:5000`) falla **con tu mensaje**, no con un traceback enorme (puede tardar unos segundos en agotar el tiempo de espera).

**Paso 5: Run trivial.**
- Qué hacer: en una celda **temporal** (se borra al final del ticket): `set_experiment("smoke-test-T002")`, abrir un run con `with mlflow.start_run(...)`, registrar un parámetro y una métrica inventados.
- Idea de sintaxis:
  ```python
  with mlflow.start_run(run_name="prueba"):
      mlflow.log_param("clave", 1)
      mlflow.log_metric("resultado", 0.5)
  ```
- Cómo comprobar: la celda termina sin error.

**Paso 6: Verlo en la interfaz.**
- Qué hacer: en **otra** terminal (con `.venv` activo, en la raíz del repo): `mlflow ui --backend-store-uri sqlite:///mlflow.db`. Abrir la URL que imprime (por defecto suele ser `http://127.0.0.1:5000`; **[hipótesis]**, usa la que veas en pantalla).
- Cómo comprobar: ver el apartado 7.

**Paso 7: Limpiar.**
- Qué hacer: borrar la celda temporal del paso 5 (el run de prueba ya cumplió su función). Dejar solo celdas 0 y 1 (con sus textos).

## 5. Qué NO hacer

- **No** escribas el URI real del DE ni credenciales en el código ni en el repo. Solo placeholder.
- **No** uses `mlflow.autolog()` (decisión D9: registro manual).
- **No** registres modelos ni artefactos todavía (eso es T-008 en adelante).
- **No** uses el experimento real `course-recommender-demo` para la prueba: mezclaría basura con los resultados reales.
- **No** subas `mlflow.db` ni `mlruns/` a git (ya están en `.gitignore`; compruébalo con `git status`).
- **No** agregues Model Registry (descartado, D11).

## 6. Escalera de pistas (pídelas una a una)

- **Pista 1:** el error que quieres evitar es que MLflow falle de forma confusa. Piensa: ¿qué dos cosas pueden estar mal? (a) el URI no está definido, (b) el URI está definido pero no hay quién responda. Cada una necesita su propio mensaje.
- **Pista 2:** funciones: `os.environ.get`, `mlflow.set_tracking_uri`, `mlflow.search_experiments`, `mlflow.set_experiment`, `mlflow.start_run`. Documentación: mlflow.org/docs → API reference → `mlflow`.
- **Pista 3:** esqueleto:
  ```python
  uri = ______
  if uri == ______:
      raise RuntimeError(______)
  mlflow.set_tracking_uri(______)
  try:
      ______  # operación de lectura
  except Exception as e:
      raise RuntimeError(f"... {uri} ... {e}") from e
  ```
- **Solución completa:** solo si la pides.

## 7. Criterios de aceptación (verificables)

- [ ] `python -c "import mlflow; print(mlflow.__version__)"` en `.venv` imprime `3.17.2`. *(Evidencia: salida de terminal.)*
- [ ] Sin `MLFLOW_TRACKING_URI` definida, ejecutar la celda 1 lanza un error con **tu** mensaje, que dice qué hacer. *(Evidencia: captura o texto del error.)*
- [ ] Con `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`, la celda 1 imprime versión y URI sin error.
- [ ] Con un URI inválido (`http://no-existe:5000`), la celda 1 falla con **tu** mensaje que incluye el URI.
- [ ] **Visible en la interfaz de MLflow:** en `http://127.0.0.1:5000` (o la URL que muestre `mlflow ui`), en la barra lateral izquierda aparece el experimento `smoke-test-T002`; al entrar, hay un run con el parámetro y la métrica que registraste (columnas "Parameters" y "Metrics" de la tabla de runs).
- [ ] `git status` **no** muestra `mlflow.db` ni `mlruns/`.
- [ ] El repo no contiene el URI real ni credenciales.

## 8. Errores comunes y cómo diagnosticarlos

| Síntoma | Causa probable | Cómo comprobarla |
|---|---|---|
| La celda dice que el URI es el placeholder aunque lo definiste | La variable se definió en una terminal distinta a la que lanzó Jupyter/VS Code, o no reiniciaste el kernel | `print(os.environ.get("MLFLOW_TRACKING_URI"))` en una celda. Cierra el editor, define la variable en la terminal y ábrelo **desde esa terminal**; reinicia el kernel |
| `ModuleNotFoundError: mlflow` | El kernel del notebook no es el de `.venv` | Revisa el kernel seleccionado (arriba a la derecha). `import sys; print(sys.executable)` debe apuntar a `.venv` |
| La interfaz abre pero no ves tu experimento | `mlflow ui` apunta a otra base | Verifica que usas **el mismo** `--backend-store-uri` que el URI del notebook y que lo lanzaste desde la misma carpeta (la ruta `sqlite:///mlflow.db` es relativa) |
| Error de puerto en uso al lanzar `mlflow ui` | Ya hay otro proceso en el 5000 | Usa `--port 5001` |
| El URI inválido tarda mucho en fallar | Es normal: MLflow reintenta antes de rendirse | Espera; no es un bug tuyo |

## 9. Preguntas de reflexión (para aprender, no para entregar)

1. ¿Por qué el URI va en una variable de entorno y no escrito directamente en el notebook?
2. ¿Qué diferencia hay entre el backend store y el artifact store? ¿Cuál de los dos usarás cuando registres un modelo?
3. ¿Por qué es mejor que el notebook falle en la celda 1 que en la celda de entrenamiento?

## 10. Entregable

- Archivos: `notebook.ipynb` (celdas 0 y 1 con sus textos).
- Commit sugerido: `feat(notebook): configuración y comprobación de conexión a MLflow (T-002)`
- Nota en `docs/sprints/sprint-01.md`: horas reales y qué fue lo más confuso.
