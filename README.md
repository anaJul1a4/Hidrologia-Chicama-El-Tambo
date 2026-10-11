# Tarea 1 – Hidrología 2026-2S (UNAL Medellín)

Clasificación hidroclimática mensual de la cuenca del río Chicama hasta la estación El Tambo
(CAMELS-PE `PE_47E0A2A8`, SENAMHI 211003, 2170 km²), Perú.

**Integrantes:** _(completar)_

## Ver los resultados

**Página web:** https://anajul1a4.github.io/Hidrologia-Chicama-El-Tambo/

La página tiene una pestaña por punto de la tarea (cuenca, contexto físico, 1.1 a 1.5.c y los puntos 2 a 5,
que se irán agregando). En cada gráfica se explica **qué muestra** y **cómo se construyó**, con el script y los
archivos de datos que la generan.

- Las **series de tiempo y los ciclos anuales son interactivos** (Plotly): zoom, lectura del valor al pasar el
  cursor y series que se activan o desactivan desde la leyenda. Se dibujan directamente desde los CSV de resultados.
- Los **mapas, el DEM y las demás figuras** (histogramas, cajas, disponibilidad, síntesis) se muestran como PNG.
  Al hacer clic se amplían, y hay un enlace al original en resolución completa.

La página también funciona sin internet: clone o descargue el repositorio y abra `index.html` con doble clic.
Plotly va incluido en `web/lib/`.

## Estructura

| Ruta | Contenido |
|---|---|
| `index.html`, `web/` | Página web (la genera `Hidrologiat1/Codigos/29_pagina_web.py`) |
| `Hidrologiat1/Codigos/` | Scripts de Python numerados en orden de trabajo |
| `Tarea 1/El_Tambo/datos/` | Datos ya recortados a la cuenca (CAMELS-PE, IMERG, PISCOp v3, ERA5-Land, CHIRPS, cobertura) |
| `Tarea 1/El_Tambo/resultados/` | Figuras (PNG) y tablas (CSV) generadas por los scripts |
| `DATOS.md` | Qué datos se descargaron, qué tratamiento recibieron y con cuáles se trabaja |
| `ESTADO_PROYECTO.md` | Bitácora: fuentes, decisiones metodológicas y notas para el informe |
| `visor_resultados.html` | Visor estático anterior (un solo archivo, script 22) |

Periodo común de análisis: **1998-01 a 2025-08** (meses con precipitación de CAMELS-PE e IMERG).

## Reproducir

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cd Hidrologiat1/Codigos
```

Orden de ejecución: `09 → 06 → 07a → 13 → 14 → 10 → 28 → 26 → 07b → 11 → 12 → 17 → 15 → 16 → 18 → 19 → 20 → 21 → 23 → 24 → 25 → 27 → 22 → 30a → 30b → 31 → 29`.

El script 09 descarga y verifica CAMELS-PE v1.0.1 desde Zenodo. Después hay que **extraer el ZIP**
en `Tarea 1/CAMELS_PE/`, porque el script 06 lee de ahí el polígono y las estaciones.

**DEM:** el script 06 no descarga el DEM. Hay que bajar antes las dos teselas Copernicus GLO-30 a
`Tarea 1/El_Tambo/datos/dem/GLO30_tiles/`:

```bash
for t in S08_00_W079_00 S09_00_W079_00; do
  n=Copernicus_DSM_COG_10_${t}_DEM
  curl -o "Tarea 1/El_Tambo/datos/dem/GLO30_tiles/$n.tif" "https://copernicus-dem-30m.s3.amazonaws.com/$n/$n.tif"
done
```

No se incluyen en el repositorio, por tamaño, el DEM, la geología INGEMMET, los NetCDF nacionales de PISCOp,
el CAMELS-PE completo ni el ERA5 regional mensual. Los scripts 07a, 09, 13 y 24 los descargan. Las descargas de
IMERG (script 10) y ERA5/ERA5-Land (scripts 17 y 24) requieren cuentas personales gratuitas en NASA Earthdata
(`~/_netrc`) y en Copernicus CDS (`~/.cdsapirc`). Las credenciales nunca se guardan en el repositorio.

## Fuentes

CAMELS-PE v1.0.1 (PISCOp v2.1, PISCOt v1.2, caudales SENAMHI) · GPM IMERG V07 Final mensual ·
PISCOp v3.0 (doi:10.6084/m9.figshare.32411886.v1) · ERA5-Land mensual (doi:10.24381/cds.68d2bb30) ·
CHIRPS v2.0 (doi:10.15780/G2RP4Q) · ERA5 mensual (doi:10.24381/cds.6860a573, 10.24381/cds.f17050d7) ·
Copernicus GLO-30 · Plotly.js 2.35.2 (MIT).
