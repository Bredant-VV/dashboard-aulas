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

    if not os.path.exists(CSV_PATH):
        print("No existe el CSV")
        return pd.DataFrame(), pd.DataFrame(), None, None

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    if df.empty:
        print("CSV vacío")
        return pd.DataFrame(), pd.DataFrame(), None, None

    # 🔥 Imprimir columnas reales en logs (clave para debug)
    print("Columnas detectadas:", df.columns.tolist())

    df.columns = df.columns.str.strip()

    # Verificamos que existan las columnas necesarias EXACTAS
    columnas_necesarias = ["Hora inicio", "Hora Fin", "Dia", "Aula"]

    for col in columnas_necesarias:
        if col not in df.columns:
            print(f"Falta columna: {col}")
            return pd.DataFrame(), pd.DataFrame(), None, None

    df["Hora inicio"] = pd.to_numeric(df["Hora inicio"], errors="coerce")
    df["Hora Fin"] = pd.to_numeric(df["Hora Fin"], errors="coerce")
    df = df.dropna(subset=["Hora inicio", "Hora Fin"])

    df["Hora inicio"] = df["Hora inicio"].astype(int)
    df["Hora Fin"] = df["Hora Fin"].astype(int)

    dias = {
        0: "LUNES",
        1: "MARTES",
        2: "MIERCOLES",
        3: "JUEVES",
        4: "VIERNES",
        5: "SABADO",
        6: "DOMINGO"
    }

    ahora = datetime.now(ZoneInfo("America/Mexico_City"))
    dia_actual = dias[ahora.weekday()]
    hora_actual = ahora.hour

    df = df[df["Dia"].fillna("").str.upper() == dia_actual]
    df = df[df["Aula"].str.startswith(modulo)]

    ocupadas = df[
        (df["Hora inicio"] <= hora_actual) &
        (df["Hora Fin"] > hora_actual)
    ]

    proximas = df[
        (df["Hora inicio"] > hora_actual)
    ].sort_values(by="Hora inicio")

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