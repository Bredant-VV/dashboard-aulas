import requests
import pandas as pd
import os
from datetime import datetime

URL = "http://148.202.89.11/spasav4/php/class/class.ConsultaHorarios.php"

ARCHIVO_ACTUAL = "horarios.csv"
ARCHIVO_NUEVO = "horarios_nuevo.csv"


def actualizar_horarios():

    payload = {"cc": "2026A"}

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://148.202.89.11/spasav4/php/reportes/ltsMateriasGlobal.php"
    }

    response = requests.post(URL, data=payload, headers=headers)

    if response.status_code != 200:
        return "Error en la petición"

    try:
        data = response.json()
        df_nuevo = pd.DataFrame(data)

        df_nuevo.to_csv(ARCHIVO_NUEVO, index=False, encoding="utf-8-sig")

        if not os.path.exists(ARCHIVO_ACTUAL):
            df_nuevo.to_csv(ARCHIVO_ACTUAL, index=False, encoding="utf-8-sig")
            return "Archivo creado por primera vez"

        df_actual = pd.read_csv(ARCHIVO_ACTUAL)

        if df_actual.equals(df_nuevo):
            os.remove(ARCHIVO_NUEVO)
            return "Sin cambios"

        else:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            respaldo = f"respaldo_{fecha}.csv"
            os.rename(ARCHIVO_ACTUAL, respaldo)
            os.rename(ARCHIVO_NUEVO, ARCHIVO_ACTUAL)
            return f"Actualizado correctamente. Respaldo: {respaldo}"

    except Exception as e:
        return f"Error procesando datos: {e}"