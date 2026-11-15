# T-005: Cargar los tres CSV en el notebook y validarlos con `assert`

**Épica:** Notebook   **Riesgo:** bajo   **Estimación (hipótesis):** 1–2 h (sin límite de tiempo)
**Depende de:** T-004 (hecho) | **Bloquea a:** T-006

## 1. Por qué importa

Los CSV son la **fuente de verdad** del proyecto. Antes de entrenar, el notebook debe comprobar que los datos son los esperados: si alguien (o un cambio futuro del generador) los rompe, el notebook se detiene **antes** de producir métricas engañosas. Es también el primer contacto con `pandas` en el proyecto.

> Recomendación: haz T-002 primero o en paralelo (máximo 2 tickets en curso). Las celdas de este ticket van **después** de las celdas 0 y 1.

## 2. Conceptos previos

> Marca con ✅ lo que ya dominas y con ❓ lo que no.

### 2.1 DataFrame y lectura de CSV
Un `DataFrame` de `pandas` es una tabla en memoria (filas y columnas con nombre). Se crea desde un CSV con `pd.read_csv(ruta)`.
```python
import pandas as pd
df = pd.read_csv("data/algo.csv")
df.shape      # (filas, columnas)
df.head()     # primeras filas
df.dtypes     # tipo de cada columna
```

### 2.2 Rutas con `pathlib`
`Path` trata rutas como objetos y funciona igual en Windows y Linux (importante: el DE puede usar otro sistema).
```python
from pathlib import Path
DATA_DIR = Path("data")
DATA_DIR.exists()               # True / False
(DATA_DIR / "archivo.csv")      # une rutas con /
```

### 2.3 `assert`
`assert condicion, "mensaje"` no hace nada si la condición es verdadera; si es falsa, detiene el programa con ese mensaje.
```python
assert 2 + 2 == 4, "las matemáticas están rotas"
```
Escribir **mensajes que digan qué se esperaba y qué se encontró** (con f-strings) te ahorra muchísimo debug.

### 2.4 Validar un DataFrame: herramientas útiles
- **Nulos:** `df.isna().sum()` cuenta nulos por columna; `.sum().sum()` da el total.
- **Duplicados:** `df.duplicated(subset=["a", "b"]).sum()` cuenta filas repetidas según esas columnas.
- **Conteo por grupo:** `df.groupby("col").size()` da cuántas filas tiene cada valor de `col`.
- **Pertenencia a un vocabulario:** `df["col"].isin(["x", "y"])` devuelve True/False por fila; `.all()` dice si **todas** son True.
- **Media de una columna 0/1:** `df["target"].mean()` = proporción de unos (la tasa).

### 2.5 Vocabulario controlado y consistencia entre tablas
Las columnas categóricas deben usar **exactamente** los valores definidos (ver `docs/DECISIONES_DATOS.md`, sección 3). Un error de escritura como `"principante"` rompería el cruce con otras tablas más adelante.

También conviene comprobar la **integridad referencial**: cada `student_id` de `eventos` debe existir en `estudiantes`, y cada `course_id` en `cursos`. (Esta comprobación es **un extra mío**, no está en el documento de decisiones; es barata y evita cruces vacíos en T-006.)

### 2.6 Qué investigar (términos de búsqueda)
- "pandas read_csv", "pandas DataFrame isna sum", "pandas duplicated subset".
- "pandas groupby size", "pandas Series isin".
- "Python assert statement", "Python f-string".
- "pathlib Path exists".

## 3. Qué hay que lograr (resultado, no receta)

Una sección del notebook (texto + código) que:
1. Comprueba que existe la carpeta `data/` y los tres archivos, y si no, falla con un mensaje claro.
2. Carga `estudiantes`, `cursos` y `eventos` en tres DataFrames.
3. Ejecuta todas las validaciones de abajo con `assert` y mensajes informativos.
4. Imprime un pequeño resumen (filas por tabla y tasa de completación) al terminar bien.

Validaciones (de `docs/DECISIONES_DATOS.md`, sección 6, más las marcadas como extra):
- Tamaños: 2,000 estudiantes, 60 cursos, 40,000 eventos.
- Tasa global de `completo_30d` entre 25% y 35%.
- Cada estudiante tiene exactamente 20 filas en `eventos`.
- Sin pares (`student_id`, `course_id`) duplicados.
- Sin nulos en ninguna tabla.
- Vocabulario válido en: `objetivo_aprendizaje`, `nivel_experiencia`, `area_interes`, `plan` (estudiantes) y `categoria`, `nivel` (cursos).
- `completo_30d` solo contiene 0 y 1 *(extra)*.
- Integridad referencial de `student_id` y `course_id` *(extra)*.

## 4. Pasos

**Paso 1: Celda de texto.** Explica en 3–4 líneas qué hace la sección y por qué (el DE la lee de corrido). Cómo comprobar: se lee bien sin conocer el proyecto.

**Paso 2: Verificar que existen los archivos.**
- Qué hacer: con `Path`, comprobar la carpeta y los tres CSV; si falta algo, `raise FileNotFoundError` con un mensaje que explique que hay que entregar el repo completo (no solo el `.ipynb`).
- Cómo comprobar: renombra temporalmente `data/` → el mensaje aparece; devuélvele el nombre.

**Paso 3: Cargar los CSV.**
- Qué hacer: `pd.read_csv` para cada uno.
- Cómo comprobar: imprime `.shape` de cada DataFrame: `(2000, 6)`, `(60, 5)`, `(40000, 3)`.

**Paso 4: Validaciones de estructura (tamaño, nulos, duplicados, 20 por estudiante).**
- Idea de sintaxis (ejemplo genérico):
  ```python
  n_nulos = int(tabla.isna().sum().sum())
  assert n_nulos == 0, f"Hay {n_nulos} nulos en la tabla"
  ```
- Cómo comprobar: pasan. Luego **rómpelas a propósito** en una copia (por ejemplo `copia = eventos.copy(); copia.loc[0, "completo_30d"] = None`) y confirma que tu `assert` salta con un mensaje útil. *Una validación que nunca has visto fallar no está probada.*

**Paso 5: Validaciones de la tasa y de `completo_30d`.**
- Qué hacer: calcular la tasa con `.mean()` y verificar que está entre 0.25 y 0.35 (puedes encadenar: `assert 0.25 <= tasa <= 0.35, ...`). Verificar que los valores únicos son `{0, 1}` (pista: `.unique()` y `set(...)`).
- Cómo comprobar: pasan; prueba con una copia modificada.

**Paso 6: Validaciones de vocabulario.**
- Qué hacer: definir los vocabularios como listas/constantes **una sola vez** y reutilizarlos. Idea: `df["col"].isin(VOCAB).all()`. Para el mensaje de error, muestra qué valores sobraron (pista: `set(df["col"]) - set(VOCAB)`).
- Cómo comprobar: pasan; cambia un valor en una copia (`"principiante"` → `"principante"`) y verifica el mensaje.

**Paso 7: Integridad referencial.**
- Qué hacer: comprobar que los `student_id` de `eventos` están en `estudiantes` y los `course_id` de `eventos` en `cursos`.
- Cómo comprobar: pasan.

**Paso 8: Resumen final.**
- Qué hacer: imprimir filas por tabla y la tasa con 3 decimales.
- Cómo comprobar: la tasa debe ser ≈ 0.301.

## 5. Qué NO hacer

- **No** modifiques los CSV (ni a mano ni con código): son la fuente de verdad. Si algo falla, el problema se corrige en `scripts/generate_data.py`, no aquí.
- **No** limpies ni rellenes datos: el notebook **valida**, no arregla.
- **No** hagas `merge` ni crees variables nuevas (eso es T-006).
- **No** uses una librería de validación externa (Great Expectations, pandera...): fuera de alcance, basta con `assert`.
- **No** dejes rutas absolutas de tu PC (`C:\Users\...`); usa rutas relativas.
- **No** uses `assert` sin mensaje.

## 6. Escalera de pistas (pídelas una a una)

- **Pista 1:** para cada regla de la lista, pregúntate: ¿cuál es la condición que debe ser verdadera? Escríbela primero en español y luego tradúcela a código.
- **Pista 2:** funciones: `pd.read_csv`, `Path.exists`, `DataFrame.isna`, `DataFrame.duplicated`, `groupby(...).size()`, `Series.isin`, `Series.mean`, `Series.unique`. Documentación: pandas.pydata.org → User Guide / API reference.
- **Pista 3:** esqueleto para "20 filas por estudiante":
  ```python
  filas_por_estudiante = eventos.groupby(______).size()
  assert (filas_por_estudiante == ______).all(), f"..."
  ```
  y para vocabulario:
  ```python
  VOCAB = [______]
  fuera = set(tabla[______]) - set(VOCAB)
  assert not fuera, f"Valores fuera del vocabulario: {fuera}"
  ```
- **Solución completa:** solo si la pides.

## 7. Criterios de aceptación (verificables)

- [ ] Con `data/` renombrada, la celda falla con un mensaje claro sobre entregar el repo completo. *(Evidencia: texto del error.)*
- [ ] `estudiantes.shape == (2000, 6)`, `cursos.shape == (60, 5)`, `eventos.shape == (40000, 3)`. *(Evidencia: salida impresa.)*
- [ ] Todos los `assert` pasan con los datos reales y la tasa impresa es ≈ 0.301.
- [ ] Probaste **al menos 3** validaciones rompiéndolas en una copia y viste el mensaje esperado. *(Evidencia: una nota en el sprint log con cuáles y qué mensaje saltó.)*
- [ ] Cada `assert` tiene un mensaje que dice qué se esperaba y qué se encontró.
- [ ] El notebook corre de arriba abajo (celdas 0, 1 y esta sección) tras "Restart & Run All".
- [ ] Los CSV no cambiaron: `git status` no muestra `data/` modificada.

## 8. Errores comunes y cómo diagnosticarlos

| Síntoma | Causa probable | Cómo comprobarla |
|---|---|---|
| `FileNotFoundError` aunque el archivo existe | El notebook corre en otra carpeta de trabajo | `print(Path.cwd())`: debe ser la raíz del repo. Ábrelo desde ahí |
| Caracteres raros en `titulo` (`Ã¡`) | Codificación al leer | `pd.read_csv(ruta, encoding="utf-8")` y revisa que `cursos.head()` muestre tildes bien |
| `KeyError: 'nombre_columna'` | Nombre mal escrito o con espacios | `print(df.columns.tolist())` |
| `AssertionError` en la tasa con datos reales | Comparaste con 25 en vez de 0.25 | `print(tasa)`: es una proporción, no un porcentaje |
| `assert` pasa siempre aunque rompas los datos | Comparaste con la tabla equivocada, o tu condición no usa `.all()` | Rompe a propósito una copia y verifica que salta |
| `.isin(...).all()` da True pero hay un valor raro | Validaste otra columna | Revisa que el nombre de columna coincida con la del vocabulario |

## 9. Preguntas de reflexión (para aprender, no para entregar)

1. ¿Por qué es mejor que el notebook valide los datos al cargarlos en vez de confiar en que el generador los hizo bien?
2. ¿Qué pasaría en T-006 (`merge`) si hubiera `course_id` en `eventos` que no existen en `cursos`?
3. ¿Por qué se exige exactamente 20 filas por estudiante? (Pista: lee la sección 7.3 de `docs/DECISIONES_DATOS.md`.)

## 10. Entregable

- Archivos: `notebook.ipynb` (sección 2 con texto y código).
- Commit sugerido: `feat(notebook): carga de CSV y validación de datos con assert (T-005)`
- Nota en `docs/sprints/sprint-01.md`: horas reales, validaciones que rompiste a propósito y qué aprendiste.
