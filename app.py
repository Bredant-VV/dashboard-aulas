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
    hora_actual = ahora.hour

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

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.lower()

    if not all(col in df.columns for col in ["aula", "dia", "hora_ini", "hora_fin"]):
        return pd.DataFrame(), pd.DataFrame(), hora_actual, dia_actual

    # Limpiar datos
    df["aula"] = df["aula"].astype(str).str.strip().str.upper()
    df["dia"] = df["dia"].astype(str).str.strip().str.upper()

    df["hora_ini"] = pd.to_numeric(df["hora_ini"], errors="coerce")
    df["hora_fin"] = pd.to_numeric(df["hora_fin"], errors="coerce")

    df = df.dropna(subset=["hora_ini", "hora_fin"])

    df["hora_ini"] = df["hora_ini"].astype(int)
    df["hora_fin"] = df["hora_fin"].astype(int)

    # Filtrar día y módulo
    df = df[df["dia"] == dia_actual]
    df = df[df["aula"].str.startswith(modulo.upper())]

    ocupadas = df[
        (df["hora_ini"] <= hora_actual) &
        (df["hora_fin"] > hora_actual)
    ]

    proximas = df[
        (df["hora_ini"] > hora_actual)
    ].sort_values(by="hora_ini")

    return ocupadas, proximas, hora_actual, dia_actual


# =====================================
# DASHBOARD PRINCIPAL
# =====================================
@app.route("/")
@app.route("/modulo/<modulo>")
def index(modulo="A"):

    ocupadas, proximas, hora_actual, dia_actual = cargar_datos(modulo)

    aulas_fisicas = [f"{modulo}{i}" for i in range(1, 17)]

    tarjetas = []
    tarjetas_proximas = []

    for aula in aulas_fisicas:

        clase_actual = ocupadas[ocupadas["aula"] == aula] if not ocupadas.empty else pd.DataFrame()
        siguiente = proximas[proximas["aula"] == aula] if not proximas.empty else pd.DataFrame()

        # CLASE ACTUAL
        if not clase_actual.empty:
            fila = clase_actual.iloc[0]
            tarjetas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila.get("materia", ""),
                "carrera": fila.get("programa", ""),
                "inicio": int(fila.get("hora_ini", 0)),
                "fin": int(fila.get("hora_fin", 0))
            })
        else:
            tarjetas.append({
                "aula": aula,
                "estado": "libre"
            })

        # PROXIMA CLASE
        if not siguiente.empty:
            fila = siguiente.iloc[0]
            tarjetas_proximas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila.get("materia", ""),
                "carrera": fila.get("programa", ""),
                "inicio": int(fila.get("hora_ini", 0)),
                "fin": int(fila.get("hora_fin", 0))
            })
        else:
            tarjetas_proximas.append({
                "aula": aula,
                "estado": "libre"
            })

    return render_template(
        "index.html",
        tarjetas=tarjetas,
        tarjetas_proximas=tarjetas_proximas,
        hora_actual=hora_actual,
        dia_actual=dia_actual,
        modulo=modulo
    )


# =====================================
# VISTA MOVIL
# =====================================
@app.route("/movil")
def vista_movil():
    return render_template("movil.html")


# =====================================
# LOGIN
# =====================================
@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        if request.form.get("username") == USERNAME and request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Credenciales incorrectas"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================================
# PANEL ADMIN
# =====================================
@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return render_template("admin.html")


# =====================================
# EJECUCION LOCAL
# =====================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)