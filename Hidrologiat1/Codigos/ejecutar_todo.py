"""
Reproduce todo el análisis desde los datos incluidos en la entrega, en el orden correcto y sin internet.

Uso (desde esta carpeta, con el entorno de requirements.txt activo):
    python ejecutar_todo.py              # cadena completa sin descargas
    python ejecutar_todo.py --desde 30   # retoma desde el script 30
    python ejecutar_todo.py --informe    # además regenera el informe PDF/Word (sobrescribe los de la raíz)

No se ejecutan los scripts de descarga ni los que parten de bases nacionales o regionales que no se entregan
(su producto recortado sí está en Tarea 1/El_Tambo/datos/):
    07a  descarga WorldCover, INGEMMET y SoilGrids          → datos/cobertura, datos/geologia
    13   verificación con PISCOp nacional (v2.1 y v3.0)       → resultados/precipitacion/verificacion_*.csv
    14   recorte de PISCOp v3.0 diario nacional (1.5 GB)      → datos/piscop_senamhi/v3p0/*_recorte.nc
    24   ERA5 mensual regional, viento y humedad (~400 MB)    → datos/era5/*_climatologia_estacional.nc
    29   ERA5 mensual por niveles, inversión (~77 MB)         → datos/era5_inversion/climatologia_inversion.nc
    34a  descarga de radiosondeos (IGRA2) y perfiles ERA5     → datos/radiosondeo, datos/era5_perfiles
    37a  descarga de SST y campos ERA5 globales               → datos/campos_globales
    22   visor anterior (reemplazado por la página, script 36)
Las descargas de IMERG (10), ERA5-Land (17), CHIRPS (26) y del índice Niño (32) se saltan solas porque los archivos
ya están en datos/.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORDEN = ["09", "06", "10", "28", "26", "07b", "11", "12", "17", "15", "16", "18", "19", "20", "21", "23", "25", "27",
         "30", "31", "32", "33", "34b", "35", "37", "38", "39", "36"]

ap = argparse.ArgumentParser()
ap.add_argument("--desde", help="número del script desde el que se retoma (p. ej. 30)")
ap.add_argument("--informe", action="store_true", help="regenerar también el informe (script 40)")
args = ap.parse_args()
orden = ORDEN + (["40"] if args.informe else [])
if args.desde:
    orden = orden[orden.index(args.desde):]

t_total = time.time()
for n in orden:
    script = next(AQUI.glob(f"{n}_*.py"))
    t0 = time.time()
    print(f"\n=== {script.name} ===", flush=True)
    r = subprocess.run([sys.executable, script.name], cwd=AQUI, env={**__import__("os").environ,
                                                                    "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"})
    if r.returncode != 0:
        sys.exit(f"Falló {script.name} (código {r.returncode}). Corregir y retomar con --desde {n}.")
    print(f"--- {script.name}: {time.time() - t0:.0f} s", flush=True)
print(f"\nCadena completa en {(time.time() - t_total) / 60:.1f} min.")
