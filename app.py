from flask import Flask, render_template
import pandas as pd
from datetime import datetime
import pytz

app = Flask(__name__)

def cargar_datos(modulo):

    df = pd.read_csv("horarios.csv", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

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

    dia_actual = dias[datetime.now().weekday()]
    df = df[df["Dia"].fillna("").str.upper() == dia_actual]

    df = df[df["Aula"].str.startswith(modulo)]

    zona = pytz.timezone("America/Mexico_City")
    hora_actual = datetime.now(zona)

    ocupadas = df[
        (df["Hora inicio"] <= hora_actual) &
        (df["Hora Fin"] > hora_actual)
    ]

    proximas = df[
        (df["Hora inicio"] > hora_actual)
    ].sort_values(by="Hora inicio")

    return ocupadas, proximas, hora_actual, dia_actual


@app.route("/")
@app.route("/modulo/<modulo>")
def index(modulo="A"):

    ocupadas, proximas, hora_actual, dia_actual = cargar_datos(modulo)

    aulas_fisicas = [f"{modulo}{i}" for i in range(1, 17)]

    # ==========================
    # TARJETAS ACTUALES
    # ==========================
    tarjetas = []

    for aula in aulas_fisicas:

        clase_actual = ocupadas[ocupadas["Aula"] == aula]

        if not clase_actual.empty:
            fila = clase_actual.iloc[0]

            tarjetas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila["Materia"],
                "carrera": fila["Carrera"],
                "inicio": fila["Hora inicio"],
                "fin": fila["Hora Fin"]
            })
        else:
            tarjetas.append({
                "aula": aula,
                "estado": "libre"
            })

    # ==========================
    # TARJETAS PROXIMAS
    # ==========================
    tarjetas_proximas = []

    for aula in aulas_fisicas:

        siguiente = proximas[proximas["Aula"] == aula]

        if not siguiente.empty:
            fila = siguiente.iloc[0]

            tarjetas_proximas.append({
                "aula": aula,
                "estado": "ocupada",
                "materia": fila["Materia"],
                "carrera": fila["Carrera"],
                "inicio": fila["Hora inicio"],
                "fin": fila["Hora Fin"]
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
@app.route("/movil")
def vista_movil():
    return render_template("movil.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)