"""
Contexto físico: cortes topográficos de la cuenca con la altura de la inversión térmica costera.

(a) Ubicación regional; (b) relieve del sector costa–cuenca–divisoria con las líneas de corte; (c) corte oeste–este
a la latitud de El Tambo, del océano a la divisoria continental; (d) perfil longitudinal del río principal, de El Tambo a la
cabecera. En (c) y (d) se superpone la capa de inversión (base y tope medianos)
de los radiosondeos de Trujillo en la estación seca (may–sep) y en la húmeda (dic–abr) (script 34b), para ver qué parte
del valle queda debajo de la inversión. El corte (d) empieza en El Tambo porque la capa del río principal
(script 06) termina en el cierre de la cuenca.

DEM: Copernicus GLO-90 (90 m; ESA/Airbus, distribuido por AWS Open Data, sin cuenta), seis teselas de 1°
entre 7–9° S y 77–80° O. Se usa GLO-90 y no GLO-30 porque el corte llega a la costa y más allá de la divisoria,
fuera de las teselas GLO-30 de la cuenca, y para la escala del corte basta 90 m.

Salidas:
  Tarea 1/El_Tambo/datos/dem/GLO90_tiles/*.tif (+ PROCEDENCIA.json)
  Tarea 1/El_Tambo/resultados/contexto_fisico/fig_perfil_topografico.png, perfil_topografico.csv
"""
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.merge import merge
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from pyproj import Geod
from shapely.geometry import LineString, Point

from estilo_figuras import CMAP_ELEV, EST, TINTA, TINTA2, GRIS, INVERSION, VAR, aplicar_estilo

aplicar_estilo()
ROOT = Path(__file__).resolve().parents[2] / "Tarea 1" / "El_Tambo"
TILES = ROOT / "datos" / "dem" / "GLO90_tiles"
TILES.mkdir(parents=True, exist_ok=True)
DL = ROOT / "resultados" / "delimitacion"
INV = ROOT / "resultados" / "inversion"
OUT = ROOT / "resultados" / "contexto_fisico"
URL = "https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"
NOMBRES = [f"Copernicus_DSM_COG_30_S0{la}_00_W0{lo}_00_DEM" for la in (8, 9) for lo in (80, 79, 78)]
EL_TAMBO = (-78.707, -7.574)
TRUJILLO = (-79.059, -8.044)                     # radiosondeo IGRA2 PEM00084516
LIM = (-79.75, -77.55, -8.45, -7.05)             # lon_min, lon_max, lat_min, lat_max del mapa (b)

# ---------------------------------------------------------------- descarga de teselas
nuevos = []
for n in NOMBRES:
    f = TILES / f"{n}.tif"
    if not f.exists():
        print(f"Descargando {n} …")
        urllib.request.urlretrieve(URL.format(n=n), f)
        nuevos.append(n)
if nuevos:
    (TILES / "PROCEDENCIA.json").write_text(json.dumps({
        "producto": "Copernicus DEM GLO-90 (DSM, 90 m), ESA / Airbus", "acceso": "AWS Open Data, s3://copernicus-dem-90m",
        "url_modelo": URL, "teselas": NOMBRES, "descargado": time.strftime("%Y-%m-%d"),
        "uso": "cortes topográficos costa–cuenca–divisoria (script 07c)"}, indent=2, ensure_ascii=False), encoding="utf-8")

srcs = [rasterio.open(TILES / f"{n}.tif") for n in NOMBRES]
dem, tr = merge(srcs, bounds=(LIM[0], LIM[2], LIM[1], LIM[3]))
dem = dem[0].astype(float)
dem[dem < -100] = np.nan
dem[dem <= 0] = np.nan                            # océano
for s in srcs:
    s.close()
lons = tr.c + tr.a * (np.arange(dem.shape[1]) + 0.5)
lats = tr.f + tr.e * (np.arange(dem.shape[0]) + 0.5)


def muestrear(linea, paso_m=200):
    """Cotas del DEM cada paso_m a lo largo de una línea (lon, lat); devuelve distancia (km), lon, lat, z."""
    g = Geod(ellps="WGS84")
    xs, ys = linea.xy
    tramos = [g.inv(xs[i], ys[i], xs[i + 1], ys[i + 1])[2] for i in range(len(xs) - 1)]
    total = sum(tramos)
    d = np.arange(0, total, paso_m)
    pts = [linea.interpolate(t / total, normalized=True) for t in d]
    lo = np.array([p.x for p in pts]); la = np.array([p.y for p in pts])
    j = np.clip(((lo - tr.c) / tr.a).astype(int), 0, dem.shape[1] - 1)
    i = np.clip(((la - tr.f) / tr.e).astype(int), 0, dem.shape[0] - 1)
    z = dem[i, j]
    return d / 1000, lo, la, np.where(np.isnan(z), 0.0, z)


cuenca = gpd.read_file(DL / "cuenca_el_tambo_glo30_wgs84.geojson").to_crs(4326)
rio = gpd.read_file(DL / "rio_principal_el_tambo.gpkg").to_crs(4326)
pol = cuenca.geometry.iloc[0]

# corte (c): oeste–este a la latitud de El Tambo, del océano a pasada la divisoria
corte_we = LineString([(-79.6, EL_TAMBO[1]), (-77.7, EL_TAMBO[1])])
# corte (d): río principal de El Tambo a la cabecera
rio_ln = rio.geometry.union_all() if hasattr(rio.geometry, "union_all") else rio.geometry.unary_union
if rio_ln.geom_type == "MultiLineString":
    from shapely.ops import linemerge
    rio_ln = linemerge(rio_ln)
c_rio = list(rio_ln.coords)
if Point(c_rio[0]).distance(Point(EL_TAMBO)) > Point(c_rio[-1]).distance(Point(EL_TAMBO)):
    c_rio = c_rio[::-1]                                          # que empiece en El Tambo
corte_rio = LineString(c_rio[::max(1, len(c_rio) // 400)] + [c_rio[-1]])

perfiles = {"c": muestrear(corte_we), "d": muestrear(corte_rio)}
filas = []
for k, (d, lo, la, z) in perfiles.items():
    filas += [{"corte": k, "dist_km": a, "lon": b, "lat": c_, "z_m": e} for a, b, c_, e in zip(d, lo, la, z)]
pd.DataFrame(filas).round(5).to_csv(OUT / "perfil_topografico.csv", index=False)

# capa de inversión por estación (medianas mensuales de los radiosondeos de Trujillo, script 34b)
rm = pd.read_csv(INV / "inversion_resumen_mensual.csv").set_index("mes")
CAPAS = {"seca (may–sep)": ([5, 6, 7, 8, 9], EST["seca"]), "húmeda (dic–abr)": ([12, 1, 2, 3, 4], EST["húmeda"])}
capa = {e: (rm.loc[m, "base_med_m"].median(), rm.loc[m, "tope_med_m"].median(), rm.loc[m, "frecuencia_pct"].mean(), c)
        for e, (m, c) in CAPAS.items()}

# ---------------------------------------------------------------- figura
fig = plt.figure(figsize=(14, 11.5))
gs = fig.add_gridspec(3, 2, height_ratios=[1.1, 0.85, 0.85], width_ratios=[1, 1.35], hspace=0.34, wspace=0.12)

# (a) ubicación
ax = fig.add_subplot(gs[0, 0])
paises = gpd.read_file(ROOT / "datos" / "ne_50m_admin_0_countries.geojson")
ax.set_facecolor("#dbe9f6")
paises.plot(ax=ax, color="#efeae1", edgecolor="#8a8378", lw=0.4)
paises[paises["ADMIN"] == "Peru"].plot(ax=ax, color="#ddd2bd", edgecolor="#6f6658", lw=0.6)
ax.add_patch(plt.Rectangle((LIM[0], LIM[2]), LIM[1] - LIM[0], LIM[3] - LIM[2], fill=False, ec="#d03b3b", lw=1.6))
cuenca.plot(ax=ax, color=TINTA, lw=0)
ax.set_xlim(-92, -60); ax.set_ylim(-20, 6); ax.set_aspect("equal")
ax.set_xticks([-90, -80, -70, -60], ["90°O", "80°O", "70°O", "60°O"])
ax.set_yticks([-20, -10, 0], ["20°S", "10°S", "0°"])
ax.set_xlabel(""); ax.set_ylabel("")
ax.set_title("(a) Ubicación: vertiente pacífica del norte del Perú", loc="left", fontsize=10.5)

# (b) relieve y líneas de corte
ax = fig.add_subplot(gs[0, 1])
ls = LightSource(azdeg=315, altdeg=45)
dz = np.nan_to_num(dem, nan=0)
hs = ls.hillshade(dz, vert_exag=6, dx=90, dy=90)
ax.set_facecolor("#dbe9f6")
ext = (lons[0], lons[-1], lats[-1], lats[0])
ax.imshow(np.where(np.isnan(dem), np.nan, hs), cmap="gray", extent=ext, alpha=0.55)
im = ax.imshow(dem, cmap=CMAP_ELEV, vmin=0, vmax=4500, extent=ext, alpha=0.75)
cuenca.boundary.plot(ax=ax, color=TINTA, lw=1.3)
rio.plot(ax=ax, color="#184f95", lw=1.1)
for ln, nom in ((corte_we, "c"), (corte_rio, "d")):
    x, y = ln.xy
    ax.plot(x, y, color="#d03b3b", lw=1.4, ls="--" if nom == "c" else "-")
    ax.text(x[0] - 0.03, y[0] + 0.03, nom, color="#d03b3b", fontsize=11, fontweight="bold", ha="right")
ax.plot(*EL_TAMBO, "o", mfc="#ffd400", mec=TINTA, ms=8, zorder=5)
ax.annotate("El Tambo", EL_TAMBO, xytext=(6, 8), textcoords="offset points", fontsize=8.5)
ax.plot(*TRUJILLO, "^", mfc="white", mec=TINTA, ms=8, zorder=5)
ax.annotate("Trujillo (radiosondeo)", TRUJILLO, xytext=(6, -12), textcoords="offset points", fontsize=8.5)
ax.text(-79.62, -8.3, "Océano Pacífico", fontsize=9, color="#3d5a80", style="italic")
ax.set_xlim(LIM[0], LIM[1]); ax.set_ylim(LIM[2], LIM[3]); ax.set_aspect(1 / np.cos(np.deg2rad(-7.7)))
ax.set_xticks([-79.5, -79, -78.5, -78], ["79.5°O", "79°O", "78.5°O", "78°O"])
ax.set_yticks([-8.4, -8, -7.6, -7.2], ["8.4°S", "8.0°S", "7.6°S", "7.2°S"])
ax.set_xlabel(""); ax.set_ylabel("")
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("altitud (m s.n.m.)")
ax.set_title("(b) Relieve (Copernicus GLO-90), cuenca y líneas de corte", loc="left", fontsize=10.5)


def panel(ax, k, titulo, marcas):
    d, lo, la, z = perfiles[k]
    dentro = np.array([pol.contains(Point(a, b)) for a, b in zip(lo, la)])
    ax.fill_between(d, 0, z, color="#d8d4cc", lw=0, zorder=2)
    ax.fill_between(d, 0, np.where(dentro, z, np.nan), color="#b9ad98", lw=0, zorder=2)
    ax.plot(d, z, color=TINTA, lw=1.1, zorder=3)
    from matplotlib.patches import Patch
    h = []
    for e, (base, tope, frec, c) in capa.items():
        ax.axhspan(base, tope, color=c, alpha=0.25, lw=0, zorder=1)
        h.append(Patch(color=c, alpha=0.35, label=f"inversión, estación {e}: {base:.0f}–{tope:.0f} m "
                                                  f"({frec:.0f} % de los sondeos)"))
    h.append(Patch(color="#b9ad98", label="tramo dentro de la cuenca"))
    ax.legend(handles=h, loc="upper left", fontsize=8, frameon=False)
    for x_, txt, dy in marcas:
        zx = np.interp(x_, d, z)
        ax.annotate(txt, (x_, zx), xytext=(0, dy), textcoords="offset points", ha="center", fontsize=8.5,
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=0.8), zorder=5)
    ax.set_xlim(0, d[-1]); ax.set_ylim(0, 4700)
    ax.set_ylabel("altitud (m s.n.m.)")
    ax.grid(alpha=0.3, lw=0.5)
    ax.set_title(titulo, loc="left", fontsize=10.5)


def dist_a(k, punto):
    d, lo, la, _ = perfiles[k]
    return d[np.argmin(np.hypot(lo - punto[0], la - punto[1]))]


dc, loc_, lac, zc = perfiles["c"]
den_c = np.array([pol.contains(Point(a, b)) for a, b in zip(loc_, lac)])
i_div = np.where(den_c)[0][-1]                                   # borde este de la cuenca en el corte
panel(fig.add_subplot(gs[1, :]), "c", f"(c) Corte oeste–este a {abs(EL_TAMBO[1]):.2f}° S, del océano a la cordillera "
      "(línea discontinua en b)",
      [(dist_a("c", (-79.5, EL_TAMBO[1])), "costa", 22), (dist_a("c", EL_TAMBO), "valle del Chicama\n(El Tambo, 684 m)", 38),
       (dc[i_div], f"divisoria de la cuenca\n({zc[i_div]:.0f} m)", 30)])
ax = fig.axes[-1]
ax.set_xlabel("distancia desde el océano (km)")
dd, lod, lad, zd = perfiles["d"]
panel(fig.add_subplot(gs[2, :]), "d", "(d) Perfil longitudinal del río principal, de El Tambo a la cabecera "
      "(línea continua en b)",
      [(dd[0] + 3.5, "El Tambo\n(cierre)", 34), (dd[-1] - 4, "cabecera", 14)])
fig.axes[-1].set_xlabel("distancia a lo largo del río desde El Tambo (km)")
fig.suptitle("Cortes topográficos: el valle del Chicama y la altura de la inversión térmica costera", fontsize=13, y=0.93)
fig.text(0.01, 0.005, "Inversión: base y tope medianos de los radiosondeos de Trujillo (IGRA2 PEM00084516, 12 UTC) por "
         "estación, script 34b. Cotas del DEM GLO-90 (90 m) muestreadas cada 200 m.",
         fontsize=8, color=TINTA2)
fig.savefig(OUT / "fig_perfil_topografico.png", dpi=170, bbox_inches="tight")

# resumen para el texto
alt = pd.read_csv(OUT / "perfil_topografico.csv")
print({e: f"{b:.0f}–{t:.0f} m" for e, (b, t, f, c) in capa.items()})
print(f"Borde este de la cuenca en el corte c: {zc[i_div]:.0f} m a {dc[i_div]:.0f} km; El Tambo a {dist_a('c', EL_TAMBO):.0f} km")
print(f"Río principal bajo el tope de la inversión seca: primeros {dd[np.argmax(zd > capa['seca (may–sep)'][1])]:.0f} km "
      f"de {dd[-1]:.0f} km")
print(OUT / "fig_perfil_topografico.png")
