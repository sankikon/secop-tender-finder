"""Busca procesos de contratación pública en SECOP II (datos abiertos de Colombia)
y los exporta a un CSV listo para abrir en Excel.

Uso:
    python secop_oportunidades.py "desarrollo de software" --dias 30 --ciudad Bogotá
    python secop_oportunidades.py --test
"""
import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = "https://www.datos.gov.co/resource/p6dx-8zbt.json"
PAGINA = 1000

# columna de la API -> encabezado del CSV
COLUMNAS = {
    "fecha_de_publicacion_del": "Fecha publicación",
    "entidad": "Entidad",
    "ciudad_entidad": "Ciudad",
    "nombre_del_procedimiento": "Proceso",
    "modalidad_de_contratacion": "Modalidad",
    "tipo_de_contrato": "Tipo de contrato",
    "precio_base": "Precio base (COP)",
    "estado_resumen": "Estado",
    "urlproceso": "Enlace",
}


def texto_soql(valor):
    # SoQL escapa la comilla simple duplicándola; evita que el término rompa la consulta
    return "'" + valor.replace("'", "''") + "'"


# Sin filtro por estado: en el dataset "estado_resumen" queda desactualizado
# (la mayoría figura como "Presentación de oferta" aunque ya cerró).
def construir_filtro(buscar, desde, ciudad=None):
    partes = [
        f"upper(descripci_n_del_procedimiento) like {texto_soql('%' + buscar.upper() + '%')}",
        f"fecha_de_publicacion_del >= {texto_soql(desde.isoformat() + 'T00:00:00')}",
    ]
    if ciudad:
        partes.append(f"upper(ciudad_entidad) = {texto_soql(ciudad.upper())}")
    return " AND ".join(partes)


def descargar(filtro, maximo):
    filas, offset = [], 0
    while len(filas) < maximo:
        params = urllib.parse.urlencode({
            "$where": filtro,
            "$order": "fecha_de_publicacion_del DESC",
            "$limit": min(PAGINA, maximo - len(filas)),
            "$offset": offset,
        })
        with urllib.request.urlopen(f"{API}?{params}", timeout=60) as r:
            lote = json.load(r)
        if not lote:
            break
        filas += lote
        offset += len(lote)
    return filas


def a_fila_csv(registro):
    fila = {}
    for clave, encabezado in COLUMNAS.items():
        valor = registro.get(clave, "")
        if isinstance(valor, dict):  # urlproceso llega como {"url": ...}
            valor = valor.get("url", "")
        if clave == "fecha_de_publicacion_del":
            valor = valor[:10]
        fila[encabezado] = valor
    return fila


def guardar_csv(registros, ruta):
    # utf-8-sig: Excel en español abre bien las tildes
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNAS.values()))
        w.writeheader()
        w.writerows(a_fila_csv(r) for r in registros)


def autoprueba():
    f = construir_filtro("o'brien", date(2026, 1, 2), ciudad="Bogotá")
    assert "'%O''BRIEN%'" in f, f
    assert "'2026-01-02T00:00:00'" in f, f
    assert "= 'BOGOTÁ'" in f, f
    fila = a_fila_csv({"fecha_de_publicacion_del": "2026-10-01T00:00:00.000",
                       "urlproceso": {"url": "https://x"}})
    assert fila["Fecha publicación"] == "2026-10-01" and fila["Enlace"] == "https://x", fila
    assert fila["Entidad"] == "", fila
    print("autoprueba OK")


def main():
    p = argparse.ArgumentParser(description="Busca procesos de SECOP II y los exporta a CSV.")
    p.add_argument("buscar", nargs="?", help="palabra o frase a buscar en la descripción")
    p.add_argument("--dias", type=int, default=30, help="días hacia atrás (por defecto 30)")
    p.add_argument("--ciudad", help="ciudad de la entidad, p. ej. Bogotá")
    p.add_argument("--max", type=int, default=5000, help="máximo de resultados")
    p.add_argument("--salida", default="secop_resultados.csv", help="archivo CSV de salida")
    p.add_argument("--test", action="store_true", help="ejecuta la autoprueba y sale")
    a = p.parse_args()

    if a.test:
        autoprueba()
        return
    if not a.buscar:
        p.error("falta el término a buscar")

    filtro = construir_filtro(a.buscar, date.today() - timedelta(days=a.dias), a.ciudad)
    try:
        registros = descargar(filtro, a.max)
    except OSError as e:
        sys.exit(f"No se pudo consultar datos.gov.co: {e}")
    guardar_csv(registros, a.salida)
    print(f"{len(registros)} procesos guardados en {a.salida}")


if __name__ == "__main__":
    main()
