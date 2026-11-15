"""Genera los datos sintéticos del caso ficticio de la Fundación Ayudinga.

Produce tres CSV en data/: estudiantes, cursos y eventos (ver docs/DECISIONES_DATOS.md).
Lo ejecuta solo el autor; el notebook únicamente carga y valida los CSV.

Uso:
    python scripts/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# --- Configuración -----------------------------------------------------------
SEED = 42
N_STUDENTS = 2000
N_COURSES = 60
N_RECS_PER_STUDENT = 20
TARGET_RATE = 0.30  # tasa global objetivo de completo_30d (válida entre 0.25 y 0.35)
RATE_MIN, RATE_MAX = 0.25, 0.35

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Vocabularios compartidos entre estudiantes y cursos
AREAS = ["analisis_datos", "machine_learning", "sql_bases_datos", "python", "visualizacion"]
LEVELS = ["principiante", "intermedio", "avanzado"]  # escala ordinal 0, 1, 2
OBJETIVOS = ["empleo", "mejorar_trabajo", "certificacion", "proyecto_personal"]
PLANES = ["gratis", "premium"]

# Cosmético: títulos legibles para la demo
AREA_TITLES = {
    "analisis_datos": "Análisis de datos",
    "machine_learning": "Machine learning",
    "sql_bases_datos": "SQL",
    "python": "Python",
    "visualizacion": "Visualización",
}
LEVEL_TITLES = {"principiante": "básico", "intermedio": "intermedio", "avanzado": "avanzado"}

# Duración por nivel (horas, entero): la duración crece con el nivel
DURATION_RANGE = {"principiante": (2, 8), "intermedio": (6, 14), "avanzado": (10, 20)}
# 12 cursos por categoría repartidos entre los 3 niveles
COURSES_PER_LEVEL = {"principiante": 5, "intermedio": 4, "avanzado": 3}

# Efectos del generador de completo_30d (valores iniciales, calibrables)
EFFECT_AREA = 1.2
EFFECT_GAP = {-2: -0.5, -1: -0.5, 0: 0.0, 1: -0.8, 2: -2.0}
EFFECT_LOAD = -0.3
LOAD_CAP = 6
EFFECT_PREMIUM = 0.5
EFFECT_OBJETIVO = {
    "empleo": 0.4,
    "certificacion": 0.4,
    "mejorar_trabajo": 0.0,
    "proyecto_personal": -0.2,
}
SIGMA_MOTIVATION = 0.5


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def make_students(rng: np.random.Generator) -> pd.DataFrame:
    # Horas por semana: concentradas en 2 a 6, cola hasta 15
    horas = np.clip(np.round(rng.lognormal(mean=np.log(3.8), sigma=0.5, size=N_STUDENTS)), 1, 15)
    return pd.DataFrame(
        {
            "student_id": [f"E{i:04d}" for i in range(1, N_STUDENTS + 1)],
            "horas_semana": horas.astype(int),
            "objetivo_aprendizaje": rng.choice(OBJETIVOS, size=N_STUDENTS, p=[0.35, 0.30, 0.20, 0.15]),
            "nivel_experiencia": rng.choice(LEVELS, size=N_STUDENTS, p=[0.50, 0.35, 0.15]),
            "area_interes": rng.choice(AREAS, size=N_STUDENTS, p=[0.30, 0.25, 0.20, 0.15, 0.10]),
            "plan": rng.choice(PLANES, size=N_STUDENTS, p=[0.75, 0.25]),
        }
    )


def make_courses(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for area in AREAS:
        for level in LEVELS:
            low, high = DURATION_RANGE[level]
            for n in range(1, COURSES_PER_LEVEL[level] + 1):
                rows.append(
                    {
                        "titulo": f"{AREA_TITLES[area]} {LEVEL_TITLES[level]} {n}",
                        "categoria": area,
                        "nivel": level,
                        "duracion_horas": int(rng.integers(low, high + 1)),
                    }
                )
    courses = pd.DataFrame(rows)
    courses.insert(0, "course_id", [f"C{i:03d}" for i in range(1, len(courses) + 1)])
    assert len(courses) == N_COURSES
    return courses


def make_events(rng: np.random.Generator, students: pd.DataFrame, courses: pd.DataFrame) -> pd.DataFrame:
    # Exposición: 20 cursos al azar por estudiante, sin repetir
    picks = np.argsort(rng.random((N_STUDENTS, N_COURSES)), axis=1)[:, :N_RECS_PER_STUDENT]
    events = pd.DataFrame(
        {
            "student_id": np.repeat(students["student_id"].to_numpy(), N_RECS_PER_STUDENT),
            "course_id": courses["course_id"].to_numpy()[picks.ravel()],
        }
    )

    # Variables del generador (la carga NO se entrega como feature a los modelos)
    df = events.merge(students, on="student_id").merge(courses, on="course_id")
    level_idx = {lvl: i for i, lvl in enumerate(LEVELS)}
    area_coincide = (df["categoria"] == df["area_interes"]).astype(int)
    brecha = df["nivel"].map(level_idx) - df["nivel_experiencia"].map(level_idx)
    carga = df["duracion_horas"] / df["horas_semana"]

    # Motivación latente: una por estudiante, no aparece en ninguna tabla
    u = pd.Series(rng.normal(0, SIGMA_MOTIVATION, N_STUDENTS), index=students["student_id"])

    score_no_b0 = (
        EFFECT_AREA * area_coincide
        + brecha.map(EFFECT_GAP)
        + EFFECT_LOAD * np.minimum(carga, LOAD_CAP)
        + EFFECT_PREMIUM * (df["plan"] == "premium")
        + df["objetivo_aprendizaje"].map(EFFECT_OBJETIVO)
        + df["student_id"].map(u)
    ).to_numpy(dtype=float)

    b0 = calibrate_intercept(score_no_b0, TARGET_RATE)
    p = sigmoid(b0 + score_no_b0)
    events["completo_30d"] = (rng.random(len(p)) < p).astype(int)
    print(f"b0 calibrado: {b0:.3f}")
    return events.sort_values(["student_id", "course_id"]).reset_index(drop=True)


def calibrate_intercept(score_no_b0: np.ndarray, target: float) -> float:
    """Bisección sobre b0 para que la probabilidad media iguale la tasa objetivo."""
    lo, hi = -15.0, 15.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if sigmoid(mid + score_no_b0).mean() < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def validate(students: pd.DataFrame, courses: pd.DataFrame, events: pd.DataFrame) -> None:
    rate = events["completo_30d"].mean()
    assert RATE_MIN <= rate <= RATE_MAX, f"Tasa global fuera de rango: {rate:.3f}"
    assert len(events) == N_STUDENTS * N_RECS_PER_STUDENT
    assert (events.groupby("student_id").size() == N_RECS_PER_STUDENT).all()
    assert not events.duplicated(["student_id", "course_id"]).any()
    assert not students.isna().any().any() and not courses.isna().any().any() and not events.isna().any().any()
    assert set(courses["categoria"]) <= set(AREAS) and set(students["area_interes"]) <= set(AREAS)
    assert set(courses["nivel"]) <= set(LEVELS) and set(students["nivel_experiencia"]) <= set(LEVELS)
    assert set(events["student_id"]) <= set(students["student_id"])
    assert set(events["course_id"]) <= set(courses["course_id"])


def report(students: pd.DataFrame, courses: pd.DataFrame, events: pd.DataFrame) -> None:
    print(f"estudiantes: {len(students)} | cursos: {len(courses)} | eventos: {len(events)}")
    print(f"tasa global completo_30d: {events['completo_30d'].mean():.3f}")
    print("nivel_experiencia:", students["nivel_experiencia"].value_counts(normalize=True).round(2).to_dict())
    print("plan:", students["plan"].value_counts(normalize=True).round(2).to_dict())
    print("horas_semana (min/mediana/max):", students["horas_semana"].agg(["min", "median", "max"]).tolist())
    print("cursos por categoría:", courses["categoria"].value_counts().to_dict())


def main() -> None:
    rng = np.random.default_rng(SEED)
    students = make_students(rng)
    courses = make_courses(rng)
    events = make_events(rng, students, courses)

    validate(students, courses, events)
    report(students, courses, events)

    DATA_DIR.mkdir(exist_ok=True)
    students.to_csv(DATA_DIR / "estudiantes.csv", index=False, encoding="utf-8")
    courses.to_csv(DATA_DIR / "cursos.csv", index=False, encoding="utf-8")
    events.to_csv(DATA_DIR / "eventos.csv", index=False, encoding="utf-8")
    print(f"CSV escritos en {DATA_DIR}")


if __name__ == "__main__":
    main()
