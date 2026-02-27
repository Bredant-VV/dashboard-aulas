from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_super_secreta_cambiar")

USERNAME = os.environ.get("ADMIN_USER", "admin")
PASSWORD = os.environ.get("ADMIN_PASS", "1234")

CSV_PATH = "horarios.csv"


# =====================================
# FUNCION PARA CARGAR DATOS
# =====================================
def cargar_datos(modulo):

    ahora = datetime.now(ZoneInfo("America/Mexico_City"))
    hora_actual = ahora.hour  # ← ya no fija en 10

    dias_map = {
        0: "LUNES",
        1: "MARTES",
        2: "MIERCOLES",
        3: "JUEVES",
        4: "VIERNES",
        5: "SABADO",
        6: "DOMINGO"
    }

    dia_actual = dias_map.get(ahora.weekday(), "SIN_DIA")

    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual

    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual

        # Normalizar nombres
        df.columns = df.columns.str.strip().str.lower()

        if not all(col in df.columns for col in ["aula", "dia", "hora_ini", "hora_fin"]):
            return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual

        df["aula"] = df["aula"].astype(str).str.strip().str.upper()
        df["dia"] = df["dia"].astype(str).str.strip().str.upper()

        df["hora_ini"] = pd.to_numeric(df["hora_ini"], errors="coerce")
        df["hora_fin"] = pd.to_numeric(df["hora_fin"], errors="coerce")

        df = df.dropna(subset=["hora_ini", "hora_fin"])

        df["hora_ini"] = df["hora_ini"].astype(int)
        df["hora_fin"] = df["hora_fin"].astype(int)

        df = df[df["dia"] == dia_actual]
        df = df[df["aula"].str.startswith(modulo.upper())]

        ocupadas = df[
            (df["hora_ini"] <= hora_actual) &
            (df["hora_fin"] > hora_actual)
        ]

        proximas = df[
            (df["hora_ini"] > hora_actual)
        ].sort_values(by="hora_ini")

        # Renombrar columnas para el template
        ocupadas = ocupadas.rename(columns={
            "aula": "Aula",
            "dia": "Dia",
            "hora_ini": "Hora inicio",
            "hora_fin": "Hora Fin"
        })

        proximas = proximas.rename(columns={
            "aula": "Aula",
            "dia": "Dia",
            "hora_ini": "Hora inicio",
            "hora_fin": "Hora Fin"
        })

        return ocupadas, proximas, hora_actual, dia_actual

    except Exception:
        return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual


# =====================================
# RUTA PRINCIPAL
# =====================================
@app.route("/")
@app.route("/modulo/<modulo>")
def index(modulo="A"):

    ocupadas, proximas, hora_actual, dia_actual = cargar_datos(modulo)

    aulas_fisicas = [f"{modulo}{i}" for i in range(1, 17)]

    tarjetas = []
    tarjetas_proximas = []

    for aula in aulas_fisicas:

        clase_actual = ocupadas[ocupadas["Aula"] == aula] if not ocupadas.empty else pd.DataFrame()
        siguiente = proximas[proximas["Aula"] == aula] if not proximas.empty else pd.DataFrame()

        if not clase_actual.empty:
            fila = clase_actual.iloc[0]
            tarjetas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila.get("materia", ""),
                "carrera": fila.get("programa", ""),
                "inicio": int(fila.get("Hora inicio", 0)),
                "fin": int(fila.get("Hora Fin", 0))
            })
        else:
            tarjetas.append({"aula": aula, "estado": "libre"})

        if not siguiente.empty:
            fila = siguiente.iloc[0]
            tarjetas_proximas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila.get("materia", ""),
                "carrera": fila.get("programa", ""),
                "inicio": int(fila.get("Hora inicio", 0)),
                "fin": int(fila.get("Hora Fin", 0))
            })
        else:
            tarjetas_proximas.append({"aula": aula, "estado": "libre"})

    return render_template(
        "index.html",
        tarjetas=tarjetas,
        tarjetas_proximas=tarjetas_proximas,
        hora_actual=hora_actual,
        dia_actual=dia_actual,
        modulo=modulo
    )


# =====================================
# EJECUCION LOCAL
# =====================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)