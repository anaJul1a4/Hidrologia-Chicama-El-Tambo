"""
Arma el ZIP de entrega de la Tarea 1 con la estructura que pide la guía:
informe PDF, códigos, datos de la cuenca efectivamente usados (incluido IMERG y los campos ERA5/ERA5-Land),
productos del análisis, README y anexos. No incluye bases nacionales completas, entornos de Python ni credenciales.

Uso:  python 41_armar_entrega.py            → ../../../Tarea1_Hidrologia_Chicama_El_Tambo.zip (junto a la carpeta
                                              del proyecto) y la carpeta de prueba descomprimida no se crea
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

PROY = Path(__file__).resolve().parents[2]
NOMBRE = "Tarea1_Hidrologia_Chicama_El_Tambo"
ZIP = PROY.parent / f"{NOMBRE}.zip"
T1 = PROY / "Tarea 1"

# ---------------------------------------------------------------- qué entra
INCLUIR = [
    PROY / "Informe_Tarea1_Chicama_El_Tambo.pdf",
    PROY / "requirements.txt",
    PROY / "index.html",
    PROY / "web",
    T1 / "El_Tambo" / "resultados",
    T1 / "El_Tambo" / "datos",
    # subconjunto de CAMELS-PE que usa el script 06 (polígonos para la validación y lista de estaciones)
    T1 / "CAMELS_PE" / "CAMELS-PE" / "04_geospatial" / "camels_pe_catchments.gpkg",
    T1 / "CAMELS_PE" / "CAMELS-PE" / "01_metadata" / "stations.csv",
]
ANEXOS = {  # archivo → nombre dentro de Anexos/
    PROY / "Informe_Tarea1_Chicama_El_Tambo.docx": "Informe_Tarea1_Chicama_El_Tambo_editable.docx",
    PROY / "ESTADO_PROYECTO.md": "Bitacora_decisiones_y_notas.md",
    PROY / "DATOS.md": "Procedencia_y_tratamiento_de_datos.md",
}
CODIGOS = PROY / "Hidrologiat1" / "Codigos"
SCRIPTS_FUERA = {"01_delimitacion.py", "02_Prueba.py", "03.py", "08_descarga_piscop.py"}   # CAMELS-DE y descartados
EXCLUIR = [
    re.compile(r"__pycache__|\.pyc$"),
    re.compile(r"datos/dem/GLO30_El_Tambo_(EPSG4326|UTM17S_30m)\.tif$"),   # los regenera el 06 desde las teselas
    re.compile(r"datos/suelos/"),                                           # descargado, no usado en el análisis
    re.compile(r"datos/radiosondeo/.*\.zip$"),                             # duplicado del .txt
    re.compile(r"\.tmp$"),
]
SECRETOS = re.compile(r"(password|passwd|contraseña|api[_-]?key|token)\s*[=:]\s*['\"][^'\"]{4,}", re.I)

README = """# Tarea 1 · Hidrología 2026-2 · Clasificación hidroclimática del río Chicama hasta El Tambo

**Integrantes:** Marlin Julie Schwebel · Juan Diego Galvis
**Profesor:** Carlos David Hoyos · Universidad Nacional de Colombia, Sede Medellín

Cuenca del río Chicama hasta la estación hidrométrica El Tambo (SENAMHI 211003; CAMELS-PE `PE_47E0A2A8`;
−7.574°, −78.707°, 684 m s.n.m.; 2 170 km²), Perú. Periodo común de análisis: **1998-01 a 2024-12** (324 meses).

## Contenido del paquete

| Ruta | Contenido |
|---|---|
| `Informe_Tarea1_Chicama_El_Tambo.pdf` | **Informe final** (cinco secciones de la guía y referencias) |
| `Hidrologiat1/Codigos/` | Scripts de Python numerados en orden de trabajo; `ejecutar_todo.py` reproduce todo |
| `Tarea 1/El_Tambo/datos/` | **Datos de entrada efectivamente usados**, recortados a la cuenca (detalle abajo) |
| `Tarea 1/El_Tambo/resultados/` | **Productos**: series mensuales procesadas, anomalías, tablas (CSV) y figuras (PNG) |
| `Tarea 1/CAMELS_PE/CAMELS-PE/` | Solo los dos archivos de CAMELS-PE nacional que usa el script 06 (polígonos y estaciones) |
| `index.html`, `web/` | Página de resultados interactiva (abrir `index.html`; funciona sin internet) |
| `Anexos/` | Informe editable (.docx), bitácora de decisiones y notas, procedencia y tratamiento de cada conjunto |
| `requirements.txt` | Dependencias con versiones |

## Datos incluidos (procedencia, versión, unidades)

Cada carpeta de `datos/` trae un `PROCEDENCIA.json` con fuente, DOI o URL, solicitud, fecha y tamaño. Resumen:

| Carpeta | Conjunto | Contenido y unidades |
|---|---|---|
| `camels_pe/` | CAMELS-PE v1.0.1 (doi:10.5281/zenodo.21195425, MD5 verificado) | Serie diaria 1981–2025 de la cuenca: `prec` (PISCOp v2.1, mm/d), `flow_obs` (SENAMHI, mm/d), `tmean`/`tmin`/`tmax` (PISCOt v1.2, °C), `pet` (mm/d), `flow_sim`; polígono, salida, atributos |
| `imerg/` | GPM IMERG V07 Final mensual (doi:10.5067/GPM/IMERG/3B-MONTH/07) | 332 archivos mensuales 1998-01 a 2025-08 recortados a la cuenca (`manual/`, mm/h), recorte unido y pesos por celda |
| `era5land/` | ERA5-Land mensual (doi:10.24381/cds.68d2bb30) | T 2 m 1981–2025 y geopotencial, recorte de la cuenca; pesos por celda |
| `era5/`, `era5_inversion/`, `era5_perfiles/` | ERA5 mensual (doi:10.24381/cds.6860a573, 10.24381/cds.f17050d7) | Climatologías estacionales de viento, humedad e IVT; T y ω por niveles; perfiles de las 12 UTC |
| `campos_globales/` | ERSST v5 (doi:10.7289/V5T72FNM) y ERA5 | SST (°C), presión al nivel del mar (Pa) y u en 200 hPa (m/s), malla 2°, 1981–2025 (punto 5) |
| `indices_clima/` | CPC/NOAA | Índices Niño 1+2, 3, 4 y 3.4 de ERSST v5 (°C, base 1991–2020) |
| `chirps/`, `piscop_senamhi/` | CHIRPS v2.0 (doi:10.15780/G2RP4Q); PISCOp v3.0 (doi:10.6084/m9.figshare.32411886.v1) | Recortes de la cuenca (mm/mes y mm/d) usados como apoyo y sensibilidad |
| `dem/GLO30_tiles/` | Copernicus GLO-30 | Dos teselas de 1°; el script 06 genera el mosaico y la versión UTM |
| `cobertura/`, `geologia/`, `estaciones/` | ESA WorldCover 2021; INGEMMET 1:100 000; red SENAMHI | Recortes y capas del contexto físico |
| `radiosondeo/` | IGRA2, estación PEM00084516 (Trujillo) | Sondeos usados para la inversión térmica |

No se incluyen las bases nacionales o regionales completas (CAMELS-PE completo, PISCOp nacional de 1.5 GB, ERA5
regional mensual de ~400 MB); de ellas se entregan los subconjuntos y productos efectivamente analizados.

## Requisitos

Python 3.13 (probado con 3.13 en Windows 11). Instalar las dependencias:

```bash
python -m venv .venv
.venv\\Scripts\\activate          # Windows   (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## Reproducir el análisis

```bash
cd Hidrologiat1/Codigos
python ejecutar_todo.py           # toda la cadena, sin internet, en el orden correcto
```

Orden que sigue `ejecutar_todo.py`:
`09 → 06 → 10 → 28 → 26 → 07b → 11 → 12 → 17 → 15 → 16 → 18 → 19 → 20 → 21 → 23 → 25 → 27 → 30 → 31 → 32 → 33 → 34b → 35 → 37 → 38 → 39 → 36`
(con `--informe` regenera además el informe con el script 40). Correspondencia con la tarea: 09–12, 15–19 punto
1.1–1.4; 20–23, 27 punto 1.5; 30–31 punto 2; 32 punto 3; 33 y 38 punto 4; 37 punto 5; 06–07b y 24–35 contexto
físico; 36 página; 39–40 síntesis e informe.

Scripts que **no** se ejecutan en la reproducción porque descargan datos o parten de bases que no se entregan (su
producto recortado está en `datos/`): 07a (WorldCover, INGEMMET), 13 (verificación con PISCOp nacional), 14 (recorte
de PISCOp v3.0 diario nacional), 24 y 29 (ERA5 regional mensual), 34a (radiosondeos y perfiles ERA5), 37a (campos
globales). Los scripts 04 y 05 documentan la selección de la cuenca con CAMELS-PE completo. Volver a descargar
requiere cuentas gratuitas en NASA Earthdata y Copernicus CDS; **el paquete no contiene credenciales**.
"""


def excluido(rel):
    return any(p.search(rel) for p in EXCLUIR)


def agregar(z, ruta, arc):
    if ruta.is_dir():
        for f in sorted(ruta.rglob("*")):
            if f.is_file():
                rel = f.relative_to(PROY).as_posix()
                if not excluido(rel):
                    z.write(f, f"{NOMBRE}/{rel}")
    else:
        z.write(ruta, arc)


faltan = [p for p in INCLUIR + list(ANEXOS) if not p.exists()]
if faltan:
    sys.exit("Faltan archivos para la entrega:\n" + "\n".join(map(str, faltan)))
for f in CODIGOS.glob("*.py"):                                            # control de credenciales en el código
    if SECRETOS.search(f.read_text(encoding="utf-8", errors="ignore")):
        sys.exit(f"Posible credencial en {f.name}: revisar antes de entregar.")

ZIP.unlink(missing_ok=True)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr(f"{NOMBRE}/README.md", README)
    for p in INCLUIR:
        agregar(z, p, f"{NOMBRE}/{p.relative_to(PROY).as_posix()}")
    for f in sorted(CODIGOS.glob("*.py")):
        if f.name not in SCRIPTS_FUERA:
            z.write(f, f"{NOMBRE}/{f.relative_to(PROY).as_posix()}")
    for origen, destino in ANEXOS.items():
        z.write(origen, f"{NOMBRE}/Anexos/{destino}")
    nombres = z.namelist()
print(f"{ZIP}  ·  {len(nombres)} archivos  ·  {ZIP.stat().st_size / 2**20:.0f} MB")
