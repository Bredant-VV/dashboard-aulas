import requests
import pandas as pd
import os
from datetime import datetime

URL = "http://148.202.89.11/spasav4/php/class/class.ConsultaHorarios.php"

ARCHIVO_ACTUAL = "horarios.csv"
ARCHIVO_NUEVO = "horarios_nuevo.csv"


def actualizar_csv():

    payload = {
        "cc": "2026A"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://148.202.89.11/spasav4/php/reportes/ltsMateriasGlobal.php"
    }

    response = requests.post(URL, data=payload, headers=headers)

    if response.status_code != 200:
        print("❌ Error en la petición:", response.status_code)
        return

    print("✅ Respuesta recibida correctamente")

    try:
        data = response.json()

        if not data:
            print("⚠ La respuesta JSON está vacía.")
            return

        df_nuevo = pd.DataFrame(data)

        # Guardamos temporalmente
        df_nuevo.to_csv(ARCHIVO_NUEVO, index=False, encoding="utf-8-sig")

        print("📄 CSV nuevo generado")

        # Si no existe archivo actual, lo creamos directamente
        if not os.path.exists(ARCHIVO_ACTUAL):
            df_nuevo.to_csv(ARCHIVO_ACTUAL, index=False, encoding="utf-8-sig")
            print("📁 No existía archivo anterior. Se creó horarios.csv")
            return

        # Cargar archivo actual
        df_actual = pd.read_csv(ARCHIVO_ACTUAL)

        # Comparar
        if df_actual.equals(df_nuevo):
            print("🟢 No hay cambios. Todo está actualizado.")
            os.remove(ARCHIVO_NUEVO)
        else:
            print("🟡 Se detectaron cambios. Actualizando...")

            # Crear respaldo
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            respaldo = f"respaldo_{fecha}.csv"
            os.rename(ARCHIVO_ACTUAL, respaldo)

            print(f"💾 Respaldo creado: {respaldo}")

            # Reemplazar archivo
            os.rename(ARCHIVO_NUEVO, ARCHIVO_ACTUAL)

            print("🚀 Archivo actualizado correctamente.")

    except Exception as e:
        print("❌ Error procesando JSON:", e)


if __name__ == "__main__":
    actualizar_csv()