from flask import Flask, render_template
import pandas as pd
from datetime import datetime
import re

app = Flask(__name__)

def cargar_datos(modulo):

    # Cargar CSV
    df = pd.read_csv("horarios.csv", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    # Limpiar horas
    df["Hora inicio"] = pd.to_numeric(df["Hora inicio"], errors="coerce")
    df["Hora Fin"] = pd.to_numeric(df["Hora Fin"], errors="coerce")
    df = df.dropna(subset=["Hora inicio", "Hora Fin"])

    df["Hora inicio"] = df["Hora inicio"].astype(int)
    df["Hora Fin"] = df["Hora Fin"].astype(int)

    # Obtener día actual
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

    # Filtrar por módulo
    df = df[df["Aula"].str.startswith(modulo)]

    # Ordenar aulas
    df = df.sort_values(by="Aula")

    hora_actual = datetime.now().hour

    # Filtrar clases activas
    ocupadas = df[
        (df["Hora inicio"] <= hora_actual) &
        (df["Hora Fin"] > hora_actual)
    ]

    return df, ocupadas, hora_actual, dia_actual


@app.route("/")
@app.route("/modulo/<modulo>")
def index(modulo="A"):

    df, ocupadas, hora_actual, dia_actual = cargar_datos(modulo)

    aulas = list(df["Aula"].dropna().unique())

    def obtener_numero(aula):
        match = re.search(r'\d+', aula)
        return int(match.group()) if match else 999

    def prioridad(aula):
        if re.match(r'^A\d+$', aula):
            return (1, obtener_numero(aula))
        elif "RECREACION" in aula.upper():
            return (2, obtener_numero(aula))
        elif "ESPEJO" in aula.upper():
            return (3, obtener_numero(aula))
        else:
            return (4, obtener_numero(aula))

    aulas.sort(key=prioridad)

    tarjetas = []

    for aula in aulas:

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

    return render_template(
        "index.html",
        tarjetas=tarjetas,
        hora_actual=hora_actual,
        dia_actual=dia_actual,
        modulo=modulo
    )


if __name__ == "__main__":
    app.run(debug=True)