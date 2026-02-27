from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from actualizador import actualizar_horarios

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_super_secreta_cambiar")

USERNAME = os.environ.get("ADMIN_USER", "admin")
PASSWORD = os.environ.get("ADMIN_PASS", "1234")

CSV_PATH = "horarios.csv"


# =====================================
# FUNCION PARA CARGAR DATOS
# =====================================
def cargar_datos(modulo):

    if not os.path.exists("horarios.csv"):
        return pd.DataFrame(), pd.DataFrame(), None, None

    df = pd.read_csv("horarios.csv", encoding="utf-8-sig")

    # 🔥 Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Posibles nombres alternativos
    columnas_map = {
        "hora inicio": ["hora inicio", "hora_inicio", "horainicio"],
        "hora fin": ["hora fin", "hora_fin", "horafin"],
        "dia": ["dia", "día"],
        "aula": ["aula"],
        "materia": ["materia"],
        "carrera": ["carrera"]
    }

    def encontrar_columna(nombre_base):
        for opcion in columnas_map[nombre_base]:
            if opcion in df.columns:
                return opcion
        return None

    col_inicio = encontrar_columna("hora inicio")
    col_fin = encontrar_columna("hora fin")
    col_dia = encontrar_columna("dia")
    col_aula = encontrar_columna("aula")

    if not all([col_inicio, col_fin, col_dia, col_aula]):
        print("Columnas no coinciden con el formato esperado")
        return pd.DataFrame(), pd.DataFrame(), None, None

    df[col_inicio] = pd.to_numeric(df[col_inicio], errors="coerce")
    df[col_fin] = pd.to_numeric(df[col_fin], errors="coerce")
    df = df.dropna(subset=[col_inicio, col_fin])

    df[col_inicio] = df[col_inicio].astype(int)
    df[col_fin] = df[col_fin].astype(int)

    dias = {
        0: "lunes",
        1: "martes",
        2: "miercoles",
        3: "jueves",
        4: "viernes",
        5: "sabado",
        6: "domingo"
    }

    ahora = datetime.now(ZoneInfo("America/Mexico_City"))
    dia_actual = dias[ahora.weekday()]
    hora_actual = ahora.hour

    df = df[df[col_dia].fillna("").str.lower() == dia_actual]
    df = df[df[col_aula].str.startswith(modulo)]

    ocupadas = df[
        (df[col_inicio] <= hora_actual) &
        (df[col_fin] > hora_actual)
    ]

    proximas = df[
        (df[col_inicio] > hora_actual)
    ].sort_values(by=col_inicio)

    # Renombramos para que el resto del código no cambie
    ocupadas = ocupadas.rename(columns={
        col_inicio: "Hora inicio",
        col_fin: "Hora Fin",
        col_dia: "Dia",
        col_aula: "Aula"
    })

    proximas = proximas.rename(columns={
        col_inicio: "Hora inicio",
        col_fin: "Hora Fin",
        col_dia: "Dia",
        col_aula: "Aula"
    })

    return ocupadas, proximas, hora_actual, dia_actual


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
                "materia": fila.get("Materia", ""),
                "carrera": fila.get("Carrera", ""),
                "inicio": fila.get("Hora inicio", ""),
                "fin": fila.get("Hora Fin", "")
            })
        else:
            tarjetas.append({"aula": aula, "estado": "libre"})

        if not siguiente.empty:
            fila = siguiente.iloc[0]
            tarjetas_proximas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila.get("Materia", ""),
                "carrera": fila.get("Carrera", ""),
                "inicio": fila.get("Hora inicio", ""),
                "fin": fila.get("Hora Fin", "")
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


# =====================================
# LOGOUT
# =====================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================================
# PANEL ADMIN
# =====================================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    mensaje = None

    if request.method == "POST":
        mensaje = actualizar_horarios()

    return render_template("admin.html", mensaje=mensaje)


@app.route("/movil")
def vista_movil():
    return render_template("movil.html")


# =====================================
# EJECUCION
# =====================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)