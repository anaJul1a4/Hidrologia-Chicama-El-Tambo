"""
Página web interactiva de la Tarea 1 (cuenca El Tambo, río Chicama), pensada para GitHub Pages.

Genera en la raíz del proyecto:
  index.html                 página con una pestaña por punto de la tarea
  web/datos.js               series y climatologías para las gráficas interactivas (Plotly)
  web/img/*.png              copias reducidas (≤ 1800 px de ancho) de los mapas y figuras no cronológicas
  web/lib/plotly-*.min.js    Plotly incluido en el repositorio (la página no depende de ningún CDN)

Criterio: las series de tiempo y los ciclos anuales se dibujan interactivos a partir de los CSV de
resultados (zoom, lectura del valor al pasar el cursor, activar/desactivar series). Los mapas, el DEM y
las demás figuras (histogramas, cajas, disponibilidad, síntesis…) se muestran como PNG, con enlace al
original en resolución completa. Cada gráfica lleva «Qué muestra» y «Cómo se construyó».

Las cifras de los textos se leen de las tablas de resultados, así que al volver a ejecutar los scripts
06–28 y luego este, la página queda actualizada. Funciona también abriendo index.html con doble clic.
"""
from pathlib import Path
from datetime import date
import html
import json
import shutil

import numpy as np
import pandas as pd
from PIL import Image

from periodo_comun import periodo_comun

PROY = Path(__file__).resolve().parents[2]
R = PROY / "Tarea 1" / "El_Tambo" / "resultados"
SM, CL, CC, CF, DL = R / "series_mensuales", R / "climatologia", R / "control_calidad", R / "contexto_fisico", R / "delimitacion"
WEB = PROY / "web"
IMG = WEB / "img"
IMG.mkdir(parents=True, exist_ok=True)
for _f in IMG.glob("*.png"):                                  # solo quedan las figuras que usa la página
    _f.unlink()
PLOTLY = "web/lib/plotly-2.35.2.min.js"
ANCHO_MAX = 1800

INI, FIN = periodo_comun()
PER = f"{INI:%Y-%m} a {FIN:%Y-%m}"
N_MESES = len(pd.date_range(INI, FIN, freq="MS"))
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ------------------------------------------------------------------ cifras leídas de los resultados
def leer(p, **kw):
    return pd.read_csv(p, **kw)


cam_full = leer(SM / "series_mensuales_camels_pe.csv", index_col="fecha", parse_dates=True)
cam = cam_full.loc[INI:FIN]
imerg = leer(SM / "imerg_cuenca_mensual.csv", index_col="fecha", parse_dates=True)["P_I_mm_mes"].loc[INI:FIN]
chirps = leer(SM / "chirps_cuenca_mensual.csv", index_col="fecha", parse_dates=True)["P_chirps_mm_mes"].loc[INI:FIN]
piscop = leer(SM / "piscop_v3_cuenca_mensual.csv", index_col="fecha", parse_dates=True)["P_piscop_v3_mm_mes"].loc[INI:FIN]
text = leer(SM / "temperatura_piscot_extendida_era5land.csv", index_col="fecha", parse_dates=True).loc[INI:FIN]
e5 = leer(SM / "era5land_t2m_cuenca_mensual.csv", index_col="fecha", parse_dates=True)["T_era5land_C"].loc[INI:FIN]

pp = pd.concat([cam["P_L_mm_mes"], imerg], axis=1).dropna()
d = pp["P_I_mm_mes"] - pp["P_L_mm_mes"]
IM = dict(PL=pp["P_L_mm_mes"].mean(), PI=pp["P_I_mm_mes"].mean(), sesgo=d.mean(), mae=d.abs().mean(),
          rmse=np.sqrt((d ** 2).mean()), r=pp.corr().iloc[0, 1], ratio=pp["P_I_mm_mes"].sum() / pp["P_L_mm_mes"].sum())
pesos = leer(PROY / "Tarea 1" / "El_Tambo" / "datos" / "imerg" / "pesos_imerg_cuenca.csv")
PW = dict(n=len(pesos), comp=int((pesos.fraccion_celda > 0.99).sum()),
          borde=100 * pesos.loc[pesos.fraccion_celda <= 0.99, "area_en_cuenca_km2"].sum() / pesos.area_en_cuenca_km2.sum(),
          eq=pesos.fraccion_celda.sum())
est = leer(SM / "estadisticos_1_3_periodo_comun.csv", index_col="variable")
cl = leer(CL / "climatologia_1_5a.csv")
ind = leer(CL / "indicadores_estacionalidad_1_5b.csv")
ip = ind[ind.muestra.str.startswith("periodo")].set_index("variable")
val = leer(SM / "validacion_extension_T.csv", index_col=0)["valor"]
tt = pd.concat([cam["T_C"], e5], axis=1).dropna()
TB = dict(sesgo=(tt["T_era5land_C"] - tt["T_C"]).mean(), r=tt.corr().iloc[0, 1], n=len(tt))
acal = leer(CL / "anomalias_anio_calendario_1_5b.csv")
_o = acal.sort_values("P_L_anom_total_mm")
humedos = ", ".join(str(int(a)) for a in _o.tail(4)["anio"][::-1])
secos = ", ".join(str(int(a)) for a in _o.head(4)["anio"])
reg = leer(CC / "registro_anomalias_1_4.csv")
RL = dict(obs=int((cam.R_flag == "completo").sum()), interp=int((cam.R_flag == "interpolado_diario").sum()),
          esc=int((cam.R_flag == "escalado").sum()), mod=int((cam.R_flag == "modelo_mensual").sum()),
          mes_mod=", ".join(f"{f:%Y-%m}" for f in cam.index[cam.R_flag == "modelo_mensual"]),
          excl=int(cam.R_flag_obs.isin(["excluido", "sin_dato"]).sum()))
pico = leer(CL / "mes_pico_por_anio_1_5b.csv")
pct_mar = (pico["mes_max_P_L"] == "Mar").mean() * 100
pct_fa = pico["mes_max_P_L"].isin(["Feb", "Mar", "Abr"]).mean() * 100
pct_qabr = (pico["mes_max_Q"].dropna() == "Abr").mean() * 100
morf = leer(DL / "parametros_morfometricos.csv", index_col=0)["valor"]
ari = leer(CL / "aridez_budyko_1_5c.csv")
ari = ari[ari.fuente_PET.str.startswith("Penman")].set_index("fuente_P")


_clp = cl[cl.variable == "P_L"].set_index("mes")["media"]
P_ANUAL = _clp.sum()
CH_ANUAL = chirps.groupby(chirps.index.month).mean().sum()
TRIM_PCT = {k: 100 * _clp.loc[m].sum() / P_ANUAL for k, m in
            {"DEF": [12, 1, 2], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}.items()}


def cmes(var, mes):
    return cl[(cl.variable == var) & (cl.mes == mes)].iloc[0]


def lag_centroide(p):
    return (ip.loc["R", "centroide_mes"] - ip.loc[p, "centroide_mes"]) % 12


# ------------------------------------------------------------------ datos de las gráficas interactivas
def lista(s, nd=2):
    return [None if pd.isna(v) else round(float(v), nd) for v in s]


idx = pd.date_range(INI, FIN, freq="MS")
T_full = text["T_piscot_C"].fillna(text["T_estimada_era5land_C"])
serie_anom = {"P_L": cam["P_L_mm_mes"], "P_I": imerg, "R": cam["R_mm_mes"], "T": T_full}
anom = {}
for k, s in serie_anom.items():
    s = s.reindex(idx)
    a = s - s.index.month.map(s.groupby(s.index.month).mean()).values         # igual que el script 21
    anom[k] = {"m": lista(a), "mm12": lista(a.rolling(12, center=True, min_periods=10).mean())}
anios_comp = [y for y in range(INI.year, FIN.year + 1) if pp.index.year.tolist().count(y) == 12]
anual = pd.DataFrame({"P_L": cam["P_L_mm_mes"], "P_I": imerg}).groupby(lambda f: f.year).sum().loc[anios_comp]

DATOS = {
    "fechas": [f"{f:%Y-%m}" for f in idx],
    "P_L": lista(cam["P_L_mm_mes"].reindex(idx)), "P_I": lista(imerg.reindex(idx)),
    "chirps": lista(chirps.reindex(idx)), "piscop": lista(piscop.reindex(idx)),
    "Q": lista(cam["Q_m3_s"].reindex(idx), 3), "R": lista(cam["R_mm_mes"].reindex(idx)),
    "R_flag": cam["R_flag"].reindex(idx).fillna("sin_dato").tolist(),
    "R_flag_obs": cam["R_flag_obs"].reindex(idx).fillna("sin_dato").tolist(),
    "T_piscot": lista(text["T_piscot_C"].reindex(idx)), "T_est": lista(text["T_estimada_era5land_C"].reindex(idx)),
    "T_era5": lista(e5.reindex(idx)),
    "anual": {"anios": [int(a) for a in anual.index], "P_L": lista(anual["P_L"], 1), "P_I": lista(anual["P_I"], 1)},
    "clim": {v: {"unid": g.unidades.iloc[0], **{c: lista(g.sort_values("mes")[c], 2)
                                                for c in ("media", "mediana", "Q1", "Q3", "P10", "P90")}}
             for v, g in cl.groupby("variable")},
    "anom": anom,
    "anom_anual": {"anios": acal["anio"].astype(int).tolist(),
                   "P_L": lista(acal["P_L_anom_total_mm"], 1), "P_I": lista(acal["P_I_anom_total_mm"], 1),
                   "R": lista(acal["R_anom_total_mm"], 1), "T": lista(acal["T_anom_media_C"], 2)},
}
# diarios (control de calidad): caudal sin rellenar, días interpolados, precipitación y temperatura
FIN_D = FIN + pd.offsets.MonthEnd(0)
dia = leer(PROY / "Tarea 1" / "El_Tambo" / "datos" / "camels_pe" / "PE_47E0A2A8.csv", index_col="date",
           parse_dates=True).loc[INI:FIN_D]
qint = leer(SM / "caudal_diario_interpolado.csv", index_col="fecha", parse_dates=True).reindex(dia.index)
A_KM2 = 2171.585                                                  # área CAMELS-PE, igual que el script 09
disp_cond = leer(CC / "disponibilidad_condicion_mes.csv", index_col="fecha", parse_dates=True).loc[INI:FIN]
anios = list(range(INI.year, FIN.year + 1))


def matriz(valido):
    """Fracción de días válidos por año × mes (None fuera del periodo común)."""
    g = valido.groupby([valido.index.year, valido.index.month]).mean()
    return [[None if (y, m) not in g.index else round(float(g[(y, m)]), 3) for m in range(1, 13)] for y in anios]


def matriz_cond(col):
    c = disp_cond[col]
    return [[c.get(pd.Timestamp(y, m, 1), None) for m in range(1, 13)] for y in anios]


DATOS["diario"] = {
    "ini": f"{dia.index[0]:%Y-%m-%d}", "n": len(dia),
    "P_L": lista(dia["prec"], 1), "T": lista(dia["tmean"], 1),
    "Q": lista(dia["flow_obs"] * A_KM2 / 86.4, 2),
    "Q_int": lista((qint["q_mm_d"] * A_KM2 / 86.4).where(qint["interpolado"] == 1), 2),
}
DATOS["disp"] = {"anios": anios,
                 "P_L": {"f": matriz(dia["prec"].notna()), "c": matriz_cond("P_L")},
                 "Q": {"f": matriz(dia["flow_obs"].notna()), "c": matriz_cond("Q")},
                 "T": {"f": matriz(dia["tmean"].notna()), "c": matriz_cond("T")},
                 "P_I": {"f": matriz(imerg.reindex(dia.index, method="ffill").notna()), "c": matriz_cond("P_I")}}

(WEB / "datos.js").write_text("window.DATOS = " + json.dumps(DATOS, ensure_ascii=False, separators=(",", ":")) + ";\n",
                              encoding="utf-8")


# ------------------------------------------------------------------ utilidades HTML
def rel(p):
    return Path(p).relative_to(PROY).as_posix().replace(" ", "%20")


def png_web(p):
    """Copia reducida del PNG para la página (el original queda enlazado)."""
    p = Path(p)
    dst = IMG / p.name
    im = Image.open(p)
    if im.width > ANCHO_MAX:
        im = im.resize((ANCHO_MAX, round(im.height * ANCHO_MAX / im.width)), Image.LANCZOS)
        im.save(dst, "PNG", optimize=True)
    if im.width <= ANCHO_MAX and (not dst.exists() or dst.stat().st_size >= p.stat().st_size):
        shutil.copyfile(p, dst)                                 # el original ya es liviano
    return dst


def enlaces(csvs):
    if not csvs:
        return ""
    return " · ".join(f'<a href="{rel(c)}" download>{html.escape(Path(c).name)}</a>' for c in csvs)


def tarjeta(titulo, muestra, construccion, script, png=None, grafica=None, csvs=(), controles="", leer_=None):
    """Una gráfica (PNG o interactiva) con sus dos bloques de texto."""
    if png:
        w = png_web(png)
        cuerpo = (f'<button class="zoom" data-full="{rel(png)}" aria-label="Ampliar: {html.escape(titulo)}">'
                  f'<img loading="lazy" src="{rel(w)}" alt="{html.escape(titulo)}"></button>')
        original = f'<a href="{rel(png)}" target="_blank" rel="noopener">PNG en resolución completa</a>'
        tipo = '<span class="tipo">imagen</span>'
    else:
        cuerpo = f'{controles}<div class="plot" data-plot="{grafica}" role="img" aria-label="{html.escape(titulo)}"></div>'
        original = ""
        tipo = '<span class="tipo int">interactiva</span>'
    extra = f'<p class="leer"><b>Cómo leerla.</b> {leer_}</p>' if leer_ else ""
    datos = enlaces(csvs)
    meta = " · ".join(x for x in [f'<span class="script">{html.escape(script)}</span>', original,
                                  f"Datos: {datos}" if datos else ""] if x)
    return f"""
<article class="fig">
  <header class="fig-h"><h3>{titulo}</h3>{tipo}</header>
  <div class="fig-cuerpo">{cuerpo}</div>
  <div class="fig-texto">
    <div><h4>Qué muestra</h4><p>{muestra}</p>{extra}</div>
    <div><h4>Cómo se construyó</h4><p>{construccion}</p></div>
  </div>
  <p class="meta">{meta}</p>
</article>"""


def tabla(df, titulo, nota=""):
    t = df.to_html(index=False, border=0, classes="tabla", na_rep="—", escape=True)
    n = f'<p class="nota">{nota}</p>' if nota else ""
    return f'<div class="tabla-cont"><h3>{titulo}</h3><div class="scroll">{t}</div>{n}</div>'


def selector(grafica, opciones):
    b = "".join(f'<button type="button" data-v="{v}" aria-pressed="{"true" if i == 0 else "false"}">{t}</button>'
                for i, (v, t) in enumerate(opciones))
    return f'<div class="selector" data-para="{grafica}" role="group" aria-label="Variable">{b}</div>'


VARS_CLIM = [("P_L", "P<sub>L</sub>"), ("P_I", "P<sub>I</sub>"), ("Q", "Q̄"), ("R", "R"), ("T", "T")]
def conmutador(grafica, opciones, etiqueta):
    b = "".join(f'<button type="button" data-v="{v}" aria-pressed="true">{t}</button>' for v, t in opciones)
    return (f'<div class="selector multi" data-para="{grafica}" role="group" aria-label="{etiqueta}">'
            f'<span class="sel-tit">{etiqueta}:</span>{b}</div>')


VARS_ANOM = [("P_L", "P<sub>L</sub>"), ("P_I", "P<sub>I</sub>"), ("R", "R"), ("T", "T")]

# ------------------------------------------------------------------ tablas
fuentes = pd.DataFrame([
    ["P_L – precipitación de referencia", "CAMELS-PE v1.0.1 (`prec`, PISCOp v2.1 promediado sobre la cuenca)", "doi:10.5281/zenodo.21195425", "diaria → mensual"],
    ["Q / R – caudal observado", "CAMELS-PE v1.0.1 (`flow_obs`, SENAMHI)", "doi:10.5281/zenodo.21195425", "diaria → mensual"],
    ["T – temperatura", "CAMELS-PE (`tmean`, PISCOt v1.2) hasta 2020; ERA5-Land T2m desde 2021 (estimación aparte)", "doi:10.24381/cds.68d2bb30", "diaria / mensual"],
    ["P_I – precipitación satelital", "GPM IMERG V07 Final (GPM_3IMERGM.07, NASA GES DISC)", "doi:10.5067/GPM/IMERG/3B-MONTH/07", "mensual, 0.1°"],
    ["Precipitación en malla (apoyo)", "PISCOp v3.0 (SENAMHI)", "doi:10.6084/m9.figshare.32411886.v1", "diaria, 0.1°"],
    ["Mapas de precipitación", "CHIRPS v2.0 (UCSB/CHC), recorte del IRI Data Library", "doi:10.15780/G2RP4Q", "mensual, 0.05°"],
    ["Transporte de humedad y viento", "ERA5 (C3S/ECMWF), niveles de presión y nivel único", "doi:10.24381/cds.6860a573; 10.24381/cds.f17050d7", "mensual, 0.5°"],
    ["Relieve", "Copernicus GLO-30 DSM", "ESA / Airbus", "30 m"],
    ["Cobertura y geología", "ESA WorldCover 2021; INGEMMET 1:100 000 (GEOCATMIN)", "—", "10 m / vectorial"],
], columns=["Variable", "Fuente", "DOI / proveedor", "Resolución"])

tmorf = morf.reset_index()
tmorf.columns = ["Parámetro", "Valor"]
tmorf["Valor"] = pd.to_numeric(tmorf["Valor"], errors="coerce").round(3).astype(object).where(
    pd.to_numeric(tmorf["Valor"], errors="coerce").notna(), morf.values)
t13 = est.reset_index()[["variable", "unidades", "n_meses_validos", "media", "mediana", "desv_est", "minimo",
                         "maximo", "Q1", "Q3", "P10", "P90", "asimetria_G1"]].round(2)
t13.columns = ["Variable", "Unidades", "Meses válidos", "Media", "Mediana", "Desv. est.", "Mín.", "Máx.",
               "Q1", "Q3", "P10", "P90", "Asimetría G1"]
t15 = ip.reset_index()[["variable", "mes_max", "mes_min", "SI", "PCI", "centroide", "concentracion", "picos",
                        "meses_humedos", "meses_secos_gaussen", "pct_en_dic_abr", "regimen"]].round(2)
t15.columns = ["Variable", "Mes máx.", "Mes mín.", "SI", "PCI", "Centroide", "Concentración", "Picos",
               "Meses húmedos", "Meses secos (Gaussen)", "% en dic–abr", "Régimen"]
t15c = leer(CL / "criterios_clasificacion_1_5c.csv").drop(columns="fuente")
t15c.columns = ["Rasgo", "Criterio", "Evidencia (P_L)", "Evidencia alternativa", "Lectura propuesta",
                "Robustez / incertidumbre"]
t14 = reg[["id", "variable", "fecha_o_periodo", "anomalia", "decision", "estado"]]
t14.columns = ["Id", "Variable", "Fecha / periodo", "Anomalía", "Decisión", "Estado"]

SM_CSV = SM / "series_mensuales_camels_pe.csv"

# ------------------------------------------------------------------ pestañas
pestanas = []


# Qué se hizo en cada punto: resumen del método al pie de cada pestaña
PIE = {
    "cuenca": "Se delimitó la cuenca con el DEM Copernicus GLO-30 (30 m, UTM 17S) por dirección de flujo D8 (pysheds), "
              "con el cierre en la estación El Tambo ajustado a la celda cuya área drenada coincide con la de CAMELS-PE "
              "(2 170 frente a 2 171.6 km²; IoU 0.994). Se calcularon la red de Strahler (umbral 5 km²), el río principal y "
              "la morfometría, y se ubicaron las estaciones de SENAMHI. Script 06.",
    "contexto": "Se reunieron los rasgos que pueden explicar los resultados: orientación de laderas y relieve (GLO-30), "
                "cobertura (ESA WorldCover 2021), geología de INGEMMET agrupada por comportamiento hidrogeológico, lluvia "
                "media de CHIRPS, transporte de humedad (IVT y viento de ERA5) por estación y perfiles de temperatura de los "
                "radiosondeos de Trujillo para la inversión térmica. Scripts 07a, 07b, 24, 25, 34a, 34b y 35.",
    "p11": "Se agregaron los registros diarios de CAMELS-PE a meses: P_L como suma, Q̄ como media, R como suma de la "
           "lámina diaria y T como media. Los huecos del caudal se rellenaron (interpolación de ln q en huecos de hasta 15 "
           "días, escalado con ≥ 50 % de días y un mes con modelo), marcando cada mes rellenado; los faltantes antes del "
           "relleno son 3.2 % de los días (límite de la guía: 10 %). La temperatura desde 2021 es una estimación con "
           "ERA5-Land, dibujada aparte. Scripts 09, 15 y 17; validación del relleno en el 28.",
    "p12": "Se descargó IMERG V07 Final mensual (0.1°), se convirtió la tasa (mm/h) a mm/mes y se promedió sobre la cuenca "
           "ponderando cada celda por su área de intersección con el polígono (31 celdas, ≈ 18 equivalentes). Se comparó "
           "con P_L en los mismos meses y con CHIRPS y PISCOp v3 como fuentes de apoyo. Scripts 10, 12, 16 y 26.",
    "p13": "Se calcularon estadísticos (media, mediana, cuartiles, percentiles 5–95, asimetría) sobre el periodo común y "
           "el registro completo, histogramas con ancho de Freedman–Diaconis y los mismos límites para las dos lluvias, "
           "y diagramas de caja de Tukey. Se buscaron los meses extremos en las series. Script 18.",
    "p14": "Se armó la disponibilidad año × mes de cada variable, se revisaron fechas, duplicados, códigos de faltantes, "
           "negativos, secuencias constantes, tramos lineales y picos aislados, y se registró cada anomalía con su "
           "comprobación y decisión (17 entradas). Se revisaron a mano dos meses de agregación. Script 19.",
    "p15a": "Se agruparon los meses por mes calendario en el periodo común y se calcularon media, mediana, cuartiles y "
            "percentiles 10–90 de cada mes; las bandas muestran dispersión entre años. Mapa año × mes y mapas mensuales "
            "de CHIRPS para la distribución espacial. Scripts 20 y 27.",
    "p15b": "Se midió la forma del ciclo con índices explícitos (SI de Walsh y Lawler, PCI de Oliver, centroide de "
            "Markham, armónicos, meses secos de Gaussen), el desfase lluvia → caudal, el mes del pico en cada año, la "
            "variabilidad por mes (CV, jackknife), dos subperiodos y las anomalías por año. Script 21.",
    "p15c": "Se clasificó el régimen con criterios climáticos: aridez P/PET (UNEP) con tres fuentes de lluvia y dos de "
            "PET, contraste con Budyko, Köppen–Geiger y la clase de cada mes (FAO, Gaussen, aguas altas, R > P). La "
            "explicación física con bibliografía queda para el grupo. Script 23.",
    "p2": "Se compararon pares mensuales coincidentes (dispersión, Pearson y Spearman, sesgo, MAE y RMSE de IMERG), con "
          "rezagos y lluvia acumulada para el caudal, en series originales y en anomalías. Se ajustaron modelos "
          "(P_L ← IMERG y Q̄ ← lluvia) eligiendo el tipo dentro del periodo de ajuste por validación cruzada, y se "
          "evaluaron en bloques de años no usados (2016–2024 y 1998–2006) frente a referencias sencillas. Scripts 30 y 31.",
    "p3": "Se analizaron tendencias en tres representaciones (serie, anomalía y anomalía estandarizada, referencia fija "
          "1998–2020), para todos los meses y para cada mes calendario, con OLS con errores HAC, Mann–Kendall de "
          "Hamed–Rao con pendiente de Sen y LOWESS; FDR de Benjamini–Hochberg para las 60 pruebas por mes; "
          "sensibilidad a ventanas, extremos y fuente; relación con Niño 1+2. Script 32.",
    "p4": "Se calcularon periodogramas de la secuencia mensual sin vacíos (FFT, Hann y Welch) de las series centradas y "
          "de las anomalías, con un fondo de ruido rojo AR(1) y umbrales del 95 % puntual y global, el reparto de la "
          "varianza por bandas y su estabilidad. Las onditas de Morlet (Torrence y Compo 1998) muestran en qué años "
          "aparece cada periodo y si la banda de 2–7 años de la cuenca coincide con la del ENSO. Scripts 33 y 38.",
    "p5": "Se descargaron SST (ERSST v5), presión al nivel del mar y viento zonal en 200 hPa (ERA5) en malla global de "
          "2°. Para cada mes calendario se correlacionaron, entre los 27 años 1998–2024, las anomalías de la cuenca con "
          "las de cada celda; la significancia usa n efectivo por persistencia y FDR por mapa. Se resumió con índices "
          "(Niño 1+2, Niño 3.4 y cajas) y se probó la robustez (Spearman, sin tendencia, sin años extremos, IMERG, "
          "subperiodos y rezago de un mes). Scripts 37a y 37.",
    "sintesis": "Esta pestaña no hace cálculos nuevos: reúne los resultados de cada punto (cifras leídas de los CSV) y "
                "propone hipótesis físicas para contrastar. Las hipótesis y la clasificación son borradores: el grupo "
                "debe sustentarlas con bibliografía leída y verificada.",
    "datos": "Fuentes, versiones y orden de ejecución de los scripts; cada figura enlaza el script y los CSV que la generan.",
}


def pestana(id_, corto, titulo, intro, cuerpo):
    pie = (f'<aside class="pie-metodo"><h3>Qué se hizo en este punto</h3><p>{PIE[id_]}</p></aside>'
           if id_ in PIE else "")
    pestanas.append((id_, corto, f'<section class="panel" id="tab-{id_}" data-tab="{id_}" hidden>'
                                 f'<h2>{titulo}</h2><p class="intro">{intro}</p>{cuerpo}{pie}</section>'))


INV = R / "inversion"
inversion_html = ""
if (INV / "inversion_por_sondeo.csv").exists():
    sd = leer(INV / "inversion_por_sondeo.csv", parse_dates=["fecha"])
    S = {t: g for t, g in sd.groupby("temporada")}
    sec, hum = S["may–sep (seca)"], S["dic–abr (húmeda)"]
    rm = leer(INV / "inversion_resumen_mensual.csv").set_index("mes")
    IV = dict(n=len(sd), ini=f"{sd.fecha.min():%Y-%m}", fin=f"{sd.fecha.max():%Y-%m}", f=100 * sd.inversion.mean(),
              fs=100 * sec.inversion.mean(), fh=100 * hum.inversion.mean(),
              bs=sec.base_m.median(), ts=sec.tope_m.median(), ds=sec.intensidad_C.median(),
              bh=hum.base_m.median(), th=hum.tope_m.median(), dh=hum.intensidad_C.median(),
              hrb=sec.HR_bajo_base.median(), hrs=sec.HR_sobre_tope.median(),
              fmin=rm.frecuencia_pct.min(), mmin=MESES[int(rm.frecuencia_pct.idxmin()) - 1])
    inversion_html = (
        '<h2 class="sub2">Fuentes de humedad e inversión térmica</h2>'
        f'<p class="intro">Radiosondeos observados de Trujillo (IGRA2 84516, a ~40 km de la salida de la cuenca): {IV["n"]} '
        f'sondeos de las 7 a.m. entre {IV["ini"]} y {IV["fin"]}, con inversión en el {IV["f"]:.0f} % de ellos; y transporte '
        f'de humedad de ERA5 en el periodo común.</p>'
        + tarjeta("Sondeo típico de la estación seca",
                  f"La temperatura baja con la altura cerca de la adiabática seca hasta el nivel de condensación (NCA), donde "
                  f"se forman los estratocúmulos (HR ≈ 100 %). En la base de la inversión el aire se calienta de golpe, unos "
                  f"{IV['ds']:.0f} °C, y por encima la humedad cae a menos del 50 %. Debajo queda el aire marino frío y "
                  f"húmedo; encima, aire de la troposfera libre que desciende y se calienta. La capa de nubes queda atrapada a "
                  f"la altura del cierre de la cuenca y no llega a la cuenca alta.",
                  "Sondeo observado. Las alturas de los niveles significativos se calcularon con la ecuación hipsométrica "
                  "desde la superficie y se ajustaron a la altura geopotencial de los niveles estándar. La inversión es el "
                  "primer aumento continuo de T con la altura (≥ 1 °C); la capa de nubes, el tramo con HR ≥ 95 %. La parcela "
                  "sube por la adiabática seca hasta el NCA y luego por la adiabática húmeda. Se eligió el sondeo de may–sep "
                  "más cercano a las medianas de base, tope e intensidad de esa estación.",
                  "34a_descarga_perfiles.py, 34b_perfiles_inversion.py", png=INV / "fig_sondeo_tipico_inversion.png",
                  csvs=[INV / "inversion_por_sondeo.csv"])
        + tarjeta("De dónde llega la humedad y qué la frena: estación seca frente a estación húmeda",
                  f"<b>La diferencia entre temporadas no está en cuánto vapor pasa sobre la cuenca, sino en si puede subir.</b> "
                  f"En ERA5 el transporte sobre la cuenca va hacia el oeste en las dos temporadas y no es menor en la seca "
                  f"(≈ 50 frente a 33 kg m⁻¹ s⁻¹), aunque la columna lleva menos agua precipitable (≈ 22 frente a 28 mm). "
                  f"<b>Estación seca (may–sep):</b> la inversión es fuerte (+{IV['ds']:.1f} °C) y está casi siempre "
                  f"({IV['fs']:.0f} % de los días), con base a {IV['bs']:.0f} m y tope a {IV['ts']:.0f} m, justo sobre el "
                  f"cierre: casi toda la cuenca queda en aire cálido y seco que desciende, y el vapor pasa sin condensar. "
                  f"Frente a la costa, el flujo del anticiclón del Pacífico corre paralelo a ella, de sureste a noroeste. "
                  f"<b>Estación húmeda (dic–abr):</b> el flujo del Atlántico cruza la Amazonía y al este de los Andes gira "
                  f"hacia el sur junto a la cordillera; la columna es más húmeda y la inversión es más baja y débil "
                  f"(+{IV['dh']:.1f} °C, {IV['bh']:.0f}–{IV['th']:.0f} m, por debajo del cierre) y falta algunos días. "
                  f"Sobre la cuenca el perfil se enfría con la altura sin tapa, lo que permite la convección.",
                  "Izquierda: flujo de vapor de agua integrado en la vertical (IVT) de ERA5 mensual (0.5°, promediado a 1°), "
                  "media de cada temporada en el periodo común; color = magnitud, flechas = dirección. Derecha: radiosondeos de "
                  "Trujillo interpolados a una malla vertical de 25 m; mediana y rango intercuartílico de la temporada, "
                  "adiabática seca de referencia desde la superficie y capa de inversión entre las medianas de base y tope "
                  "de los sondeos con inversión. Mismas escalas en las dos filas.",
                  "24_era5_vientos_humedad.py, 34b_perfiles_inversion.py, 35_temporadas_humedad_inversion.py",
                  png=INV / "fig_temporadas_humedad_inversion.png",
                  csvs=[INV / "perfiles_compuestos_temporada.csv", INV / "inversion_resumen_mensual.csv"],
                  leer_="El transporte de humedad no equivale a lluvia: llueve donde el flujo converge y asciende. Los "
                        "sondeos cubren dos años y son de las 7 a.m. La explicación física (anticiclón del Pacífico sur, "
                        "corriente de Humboldt, convección andina) debe sustentarse con bibliografía."))

HI = (float(morf["Cota media (m s.n.m.)"]) - float(morf["Cota mínima (m s.n.m.)"])) / (
    float(morf["Cota máxima (m s.n.m.)"]) - float(morf["Cota mínima (m s.n.m.)"]))
pestana("cuenca", "Cuenca", "La cuenca y su delimitación",
        "Río Chicama hasta la estación hidrométrica El Tambo (SENAMHI 211003; CAMELS-PE PE_47E0A2A8), en la vertiente "
        "del Pacífico del norte del Perú (−7.574°, −78.707°; 684 m s.n.m.). La cuenca se delimitó con el modelo digital "
        "de elevación Copernicus GLO-30; coincide con el polígono oficial de CAMELS-PE (intersección sobre unión 0.994).",
        tarjeta("Mapa de la cuenca y relieve",
                f"Relieve sombreado del DEM, límite de la cuenca, río Chicama, red de drenaje, punto de cierre, estaciones de "
                f"SENAMHI y ubicación regional (Sudamérica y Perú). Área {float(morf['Área A (km2)']):,.0f} km², cotas de "
                f"{float(morf['Cota mínima (m s.n.m.)']):,.0f} a {float(morf['Cota máxima (m s.n.m.)']):,.0f} m s.n.m. "
                f"(mediana {float(morf['Cota mediana (m s.n.m.)']):,.0f} m) y pendiente media de "
                f"{float(morf['Pendiente media de la cuenca (°)']):.0f}°. La integral hipsométrica ({HI:.2f}) indica un "
                f"<b>relieve intermedio</b>: la mitad del área está por encima de la cota media, a media ladera, y no "
                f"concentrada en la cabecera ni en el valle bajo. Las fuentes de humedad se discuten en <i>Contexto físico</i>."
                .replace(",", " "),
                "Mosaico de dos teselas Copernicus GLO-30 (30 m), recortado y reproyectado a UTM 17S. El DEM se acondicionó "
                "(relleno de depresiones y zonas planas) y se calcularon direcciones de flujo D8 y área acumulada con pysheds; "
                "el punto de cierre se ajustó a la celda de mayor área acumulada en un radio de 1.5 km de la estación. La red "
                "de drenaje son las celdas con más de 5 km² de área drenada. Integral hipsométrica = (cota media − mínima) / "
                "(máxima − mínima). Estaciones: mapa web de SENAMHI (copia del 2026-10-06); límites: Natural Earth.",
                "06_delimitacion_el_tambo_glo30.py", png=DL / "mapa_cuenca_el_tambo.png",
                csvs=[DL / "parametros_morfometricos.csv", DL / "curva_hipsometrica.csv", DL / "estaciones_senamhi_mapa.csv"])
        + tabla(tmorf, "Parámetros morfométricos", "Calculados sobre el DEM GLO-30 en UTM 17S (script 06)."))

pestana("contexto", "Contexto físico", "Contexto físico",
        "Rasgos del terreno, de la cobertura y de la atmósfera que ayudan a explicar cómo la cuenca recibe, guarda y entrega "
        "el agua. Haga clic en el panel para ampliarlo.",
        tarjeta("Panel de contexto físico",
                "(a) Orientación de laderas: se reparte casi por igual (10–14 % por dirección); al norte del río dominan las "
                "laderas hacia el S–SO y al sur las orientadas al N–NE, perpendiculares al valle del Chicama. "
                "(b) Cobertura: pastizales y pajonales (55 %), arbustales (23 %) y bosque (17 %); la agricultura se concentra "
                "en el fondo del valle. (c) Unidades hidrogeológicas: los acuíferos fisurados (areniscas y cuarcitas, 40 %) y "
                "los acuitardos sedimentarios (lutitas, 37 %) alternan en franjas NO–SE; los acuíferos porosos se limitan a "
                "los fondos de valle (2.5 %). (d) Precipitación media anual: aumenta de unos 400 mm/año en la salida a 900 "
                f"mm/año en las cabeceras del sureste. CHIRPS da un promedio menor que P<sub>L</sub> ({CH_ANUAL:.0f} frente a {P_ANUAL:.0f} mm/año), "
                "así que el mapa sirve para ver el patrón espacial, no la magnitud.",
                "(a) Orientación calculada del DEM GLO-30 a 30 m. (b) ESA WorldCover 2021 (10 m) remuestreado por moda a la "
                "malla del DEM. (c) Geología INGEMMET 1:100 000 descargada de GEOCATMIN; las 25 unidades se agruparon en 6 "
                "grupos hidrogeológicos según porosidad y permeabilidad esperadas, con colores de la convención IAH/UNESCO. "
                "(d) CHIRPS v2.0 mensual (0.05°) con la georreferencia corregida (+0.025° en longitud); media anual del "
                "periodo común en cada celda, interpolada de forma bilineal a la malla del DEM solo para dibujarla continua, "
                "con isoyetas cada 100 mm.",
                "07a_descarga_contexto_fisico.py, 26_chirps_cuenca.py, 07b_mapas_contexto_fisico.py",
                png=CF / "panel_contexto_fisico.png",
                csvs=[CF / "ficha_contexto_fisico.csv", CF / "unidades_geologicas_cuenca.csv", SM / "chirps_cuenca_mensual.csv"],
                leer_="La agrupación hidrogeológica es una propuesta del grupo que debe contrastarse con INGEMMET y ANA.")
        + inversion_html)

pestana("p11", "1.1 Series", "Punto 1.1 · Series mensuales de precipitación, caudal y temperatura",
        f"Series construidas desde los registros diarios de CAMELS-PE en el <b>periodo común {PER}</b> ({N_MESES} meses: "
        f"los meses con precipitación de CAMELS-PE y de IMERG a la vez). Use la rueda o arrastre para hacer zoom, la barra "
        f"inferior para elegir un intervalo y doble clic para volver a la vista completa.",
        tarjeta("Series mensuales en paneles alineados",
                f"Los cuatro paneles comparten el eje de tiempo: al pasar el cursor se leen los cuatro valores del mismo mes. "
                f"El caudal y la escorrentía tienen sus faltantes rellenados ({RL['interp']} meses con días interpolados, "
                f"{RL['esc']} escalados y {RL['mod']} reconstruido con modelo, {RL['mes_mod']}; el método de cada mes está en "
                f"la columna R_flag del CSV); el fondo rojo claro marca los {RL['excl']} meses que sin relleno quedaban excluidos. Desde 2021 "
                f"la temperatura es una estimación con ERA5-Land (línea discontinua), no PISCOt. Con los botones se eligen los "
                f"paneles que se muestran; siempre quedan alineados en el mismo eje de tiempo.",
                "P<sub>L</sub> = suma de la precipitación diaria (PISCOp v2.1 promediado en la cuenca por CAMELS-PE), solo "
                "meses completos. Q̄ = media del caudal diario observado (SENAMHI), convertido de mm/d a m³/s con "
                "Q̄ = q̄·A/86.4 y A = 2 171.6 km². R = suma de q diario en mm. T = media de la temperatura diaria (PISCOt "
                "v1.2) si faltan ≤ 10 % de los días. El relleno de caudal sigue tres pasos: interpolación de ln q en huecos "
                "≤ 15 días, escalado de la media en meses con ≥ 50 % de días y modelo mensual con el caudal simulado en el "
                "resto (validación en el punto 1.4).",
                "09_datos_camels_pe_el_tambo.py, relleno_caudal.py (página: 36_pagina_web.py)", grafica="serie11",
                controles=conmutador("serie11", [("P_L", "P<sub>L</sub>"), ("Q", "Q̄"), ("R", "R"), ("T", "T")],
                                     "Paneles visibles"),
                csvs=[SM_CSV, SM / "temperatura_piscot_extendida_era5land.csv"],
                leer_="Los máximos de 1998 y 2017 corresponden a eventos de El Niño; el caudal queda alto también en los meses "
                      "siguientes.")
        + tarjeta("Temperatura: PISCOt frente a ERA5-Land",
                  f"PISCOt termina en 2020. En los {TB['n']} meses con ambas fuentes varían igual (r = {TB['r']:.2f}), pero "
                  f"ERA5-Land es {abs(TB['sesgo']):.1f} °C más fría de forma casi constante. La estimación desde 2021 "
                  f"(ERA5-Land + sesgo de cada mes) tuvo un error medio de {float(val['MAE_C']):.2f} °C al validarla en "
                  f"{val['evaluacion']}. Las dos fuentes no se unen en una sola serie. El ciclo anual (b) tiene la misma forma en "
                  f"las dos: casi plano, con el máximo en agosto–septiembre, al final de la estación seca.",
                  "ERA5-Land T2m mensual (0.1°) descargado del CDS y promediado sobre la cuenca ponderando por área (30 celdas). "
                  "El sesgo de cada mes calendario frente a PISCOt se calculó en 1998–2010 y se evaluó fuera de muestra en "
                  "2011–2020; con él se estima T desde 2021: T<sub>est</sub> = ERA5-Land + sesgo del mes. Solo unos 0.5 °C del "
                  "desfase se explican por la altitud del relieve del modelo. (b) Media de cada mes calendario en 1998–2020, "
                  "solo con los meses en que existen las dos fuentes.",
                  "17_era5land_temperatura.py", grafica="temp",
                  csvs=[SM / "era5land_t2m_cuenca_mensual.csv", SM / "temperatura_piscot_extendida_era5land.csv",
                        SM / "validacion_extension_T.csv"]))

pestana("p12", "1.2 IMERG", "Punto 1.2 · Precipitación satelital IMERG",
        f"IMERG V07 Final (0.1°) promediado sobre la cuenca. Frente a P<sub>L</sub>: media {IM['PI']:.1f} frente a "
        f"{IM['PL']:.1f} mm/mes, sesgo {IM['sesgo']:+.1f} mm/mes, MAE {IM['mae']:.1f}, RMSE {IM['rmse']:.1f}, "
        f"r = {IM['r']:.2f}. IMERG acumula el {100 * IM['ratio']:.0f} % de la lluvia de P<sub>L</sub>. Ninguna de las dos es "
        f"una observación directa: P<sub>L</sub> interpola pluviómetros con información satelital, e IMERG Final también "
        f"se ajusta con pluviómetros.",
        tarjeta("P<sub>L</sub> frente a IMERG, mes a mes",
                "IMERG sigue bien el ritmo de la lluvia, pero sus picos son mucho más bajos, sobre todo en los meses más "
                "lluviosos. CHIRPS y PISCOp v3.0 están ocultas: haga clic en su nombre en la leyenda para compararlas.",
                "IMERG mensual: la tasa media (mm/h) se convierte a acumulado con mm/mes = tasa · 24 · días del mes, y se "
                f"promedia sobre la cuenca ponderando cada celda por su área de intersección con el polígono (UTM 17S): "
                f"{PW['n']} celdas, {PW['comp']} completas. CHIRPS (0.05°, 98 celdas) y PISCOp v3.0 (0.1°) se promediaron igual. "
                "P<sub>L</sub> es el promedio de cuenca que entrega CAMELS-PE.",
                "10_imerg_mensual_y_grafica.py, 26_chirps_cuenca.py, 14_piscop_v3_cuenca.py", grafica="precip",
                csvs=[SM_CSV, SM / "imerg_cuenca_mensual.csv", SM / "chirps_cuenca_mensual.csv",
                      SM / "piscop_v3_cuenca_mensual.csv"])
        + tarjeta("Totales anuales de P<sub>L</sub> e IMERG",
                  "IMERG queda por debajo de P<sub>L</sub> todos los años; la diferencia es mayor en los años muy húmedos "
                  "(1998, 2017, 2023).",
                  f"Suma de los 12 meses de cada año calendario del periodo común ({INI.year}–{FIN.year}, años completos).",
                  "36_pagina_web.py (a partir de las series mensuales)", grafica="anual",
                  csvs=[SM_CSV, SM / "imerg_cuenca_mensual.csv"])
        + tarjeta("Celdas de IMERG y pesos en el promedio de cuenca",
                  f"(a) Peso de cada celda = área dentro de la cuenca / área de la cuenca: {PW['n']} celdas, {PW['comp']} "
                  f"completas, {PW['borde']:.0f} % del peso en celdas de borde (≈ {PW['eq']:.1f} celdas equivalentes). "
                  "(b) Desnivel del terreno dentro de cada celda: una sola celda abarca más de 1 000 m.",
                  "Intersección de la malla de 0.1° de IMERG con el polígono de la cuenca en UTM 17S; el desnivel es el rango "
                  "de cotas del DEM GLO-30 dentro de cada celda. Los pesos no consideran la topografía.",
                  "12_mapa_pesos_imerg.py", png=SM / "mapa_celdas_imerg_pesos.png",
                  csvs=[SM / "relieve_celdas_imerg.csv"]))

pestana("p13", "1.3 Distribución", "Punto 1.3 · Distribución de los valores mensuales",
        "Histogramas, diagramas de caja y estadísticos descriptivos en el periodo común. P<sub>L</sub> y P<sub>I</sub> usan "
        "los mismos meses y los mismos límites de clase.",
        tarjeta("Histogramas",
                "La lluvia y sobre todo el caudal son asimétricos: muchos meses bajos y pocos muy altos. La temperatura es "
                "casi simétrica.",
                "Ancho de clase por la regla de Freedman–Diaconis y frecuencia relativa (% de meses), con los meses del "
                "periodo común. T solo con PISCOt.",
                "18_estadisticos_1_3.py", png=SM / "fig_histogramas_1_3.png")
        + tarjeta("Diagramas de caja",
                  "Caja = cuartiles 1 a 3, línea = mediana, rombo = media. Los puntos fuera de los bigotes son meses "
                  "extremos (sobre todo eventos de El Niño); se muestran, no se eliminan.",
                  "Bigotes de Tukey (1.5 × rango intercuartílico) sobre los meses válidos del periodo común.",
                  "18_estadisticos_1_3.py", png=SM / "fig_cajas_1_3.png")
        + tabla(t13, f"Estadísticos en el periodo común ({PER})",
                "Percentiles con interpolación lineal (tipo 7). T solo PISCOt, sin la estimación desde 2021. La tabla del "
                "registro completo está en estadisticos_1_3_registro_completo.csv."))

_VQC = {"P_L": ("P<sub>L</sub> · precipitación", r"P_L|Todas"), "Q": ("Q̄ · caudal", r"\bQ\b|Todas"),
        "T": ("T · temperatura", r"\bT\b|Todas"), "P_I": ("P<sub>I</sub> · IMERG", r"P_I")}
_rd = leer(CC / "resumen_disponibilidad_1_4.csv")
_rd = _rd[_rd.periodo.str.startswith("periodo")].set_index("variable")
TRAT = {
    "P_L": "Sin días faltantes en 1981–2025. P<sub>L</sub> mensual = suma de los días del mes, solo con meses completos. "
           "No es una observación directa: es PISCOp v2.1 (pluviómetros de SENAMHI + CHIRPS) promediado sobre la cuenca "
           "por CAMELS-PE, y no se pudo reproducir con PISCOp v3.0 (−14.5 %). Los meses con menos de 1 mm son meses secos "
           "reales, no faltantes.",
    "Q": f"{_rd.loc['Q', 'pct_dias_faltantes']:.1f} % de días faltantes en el periodo común, concentrados en ago–oct y en 2019–2021. Con el criterio de "
         f"completitud (≤ 10 % de días faltantes) quedaban {RL['excl']} meses excluidos; el grupo decidió rellenarlos: "
         f"(1) huecos ≤ 15 días, interpolación de ln q; (2) meses con ≥ 50 % de días, media × días del mes; (3) el "
         f"resto, modelo mensual con el caudal simulado de CAMELS-PE. Resultado: {RL['obs']} meses observados completos, "
         f"{RL['interp']} con días interpolados, {RL['esc']} escalados y {RL['mod']} reconstruido ({RL['mes_mod']}). "
         f"Lo observado se conserva aparte (R_obs, R_flag_obs) y la bandera R_flag indica el origen de cada mes. "
         f"Validación en la figura de abajo.",
    "T": f"PISCOt (CAMELS-PE) termina en 2020-12: los {int(_rd.loc['T', 'sin_dato'])} meses desde 2021 no tienen dato "
         f"observado. Se estimaron con ERA5-Land + sesgo de cada mes calendario (MAE {float(val['MAE_C']):.2f} °C en la "
         f"validación {val['evaluacion']}) y se guardan en una columna aparte, sin unir las fuentes. En las estadísticas "
         f"del punto 1.3 solo entra PISCOt.",
    "P_I": f"Producto mensual (IMERG V07 Final): los {N_MESES} meses del periodo común están completos. La tasa media (mm/h) se "
           "convirtió a mm/mes con los días de cada mes y se promedió sobre la cuenca ponderando por área. Nunca baja de "
           "≈ 2 mm/mes y sus picos son mucho menores que los de P<sub>L</sub> (limitación del producto, no error de datos).",
}


def panel_qc(v, primero):
    nombre, patron = _VQC[v]
    r = _rd.loc[v]
    falt = "—" if pd.isna(r.pct_dias_faltantes) else f"{r.pct_dias_faltantes:.1f} %"
    chips = "".join(f'<div class="dato">{t}<b>{x}</b></div>' for t, x in [
        ("Días faltantes", falt), ("Meses completos", int(r.completo)), ("Escalados", int(r.escalado)),
        ("Excluidos", int(r.excluido)), ("Sin dato", int(r.sin_dato))])
    filas = reg[reg.variable.str.contains(patron, regex=True)]
    items = "".join(f'<li><span class="estado e-{html.escape(x.estado.replace(" ", "-"))}">{html.escape(x.estado)}</span> '
                    f'<b>{html.escape(x.id)}</b> · {html.escape(str(x.fecha_o_periodo))}: {html.escape(x.anomalia)} '
                    f'<i>→ {html.escape(x.decision)}</i></li>' for _, x in filas.iterrows())
    return (f'<div class="qc-var" data-var="{v}"{"" if primero else " hidden"}>'
            f'<h4>{nombre}</h4><p class="nota">Periodo común {PER}, antes del relleno.</p>'
            f'<div class="datos-clave">{chips}</div>'
            f'<h4>Qué se hizo</h4><p>{TRAT[v]}</p>'
            f'<h4>Comprobaciones y decisiones</h4><ul class="qc-lista">{items}</ul></div>')


qc_html = f"""
<article class="fig qc">
  <header class="fig-h"><h3>Disponibilidad y control de calidad por variable</h3><span class="tipo int">interactiva</span></header>
  {selector("qc", [("P_L", "P<sub>L</sub>"), ("Q", "Q̄ caudal"), ("T", "T"), ("P_I", "P<sub>I</sub> IMERG")])}
  <div class="qc-grid">
    <div class="fig-cuerpo"><div class="plot" data-plot="qc" role="img" aria-label="Disponibilidad y serie diaria"></div></div>
    <aside class="qc-lado">{"".join(panel_qc(v, i == 0) for i, v in enumerate(_VQC))}</aside>
  </div>
  <div class="fig-texto">
    <div><h4>Qué muestra</h4><p>Arriba, la condición de cada mes (año × mes) antes de cualquier relleno, con los mismos
    colores que la figura del informe: azul completo, celeste escalado (≤ 10 % de días faltantes), rojo excluido (> 10 %) y gris
    sin dato; el número es la cantidad de días con dato en los meses incompletos. Abajo, la serie diaria del mismo periodo con los vacíos sin rellenar; en el caudal, los días
    interpolados se marcan con puntos negros. A la derecha, lo que se comprobó y se decidió con esa variable, para leerlo junto a la
    gráfica.</p></div>
    <div><h4>Cómo se construyó</h4><p>Días válidos contados en el registro diario de CAMELS-PE (P<sub>L</sub>, caudal y T) y
    meses de IMERG. Un mes es completo si faltan ≤ 10 % de sus días, criterio aplicado igual a todas las variables y durante
    todo el análisis; no se presentan sumas parciales como acumulados mensuales completos. Caudal convertido de mm/d a m³/s
    con A = 2 171.6 km². La condición de cada mes (completo, escalado, excluido, sin dato) aparece al pasar el cursor.</p></div>
  </div>
  <p class="meta"><span class="script">19_control_calidad_1_4.py, 09_datos_camels_pe_el_tambo.py (página: 36_pagina_web.py)</span> ·
  Datos: {enlaces([CC / "disponibilidad_condicion_mes.csv", CC / "resumen_disponibilidad_1_4.csv",
                   CC / "registro_anomalias_1_4.csv", SM / "caudal_diario_interpolado.csv"])}</p>
</article>"""

pestana("p14", "1.4 Calidad", "Punto 1.4 · Control de calidad",
        "Elija una variable: su disponibilidad, su serie diaria y todo lo que se hizo con ella quedan en el mismo lugar.",
        tarjeta("Disponibilidad año × mes de las cuatro variables",
                "Lluvia de referencia y temperatura completas en todo el periodo (la temperatura de PISCOt termina en "
                "2020-12); IMERG completo; el caudal tiene meses incompletos concentrados en el estiaje (ago–oct) y en "
                "2019–2021. Es la misma figura del informe.",
                "Condición de cada mes antes del relleno: completo, escalado (≤ 10 % de días faltantes), excluido "
                "(> 10 %) o sin dato. El número indica los días con dato en los meses incompletos.",
                "19_control_calidad_1_4.py", png=CC / "fig_disponibilidad_1_4.png",
                csvs=[CC / "disponibilidad_condicion_mes.csv", CC / "resumen_disponibilidad_1_4.csv"])
        + qc_html
        + tarjeta("Relleno de los faltantes de caudal y su validación",
                  "(a) Al borrar días de meses completos, la interpolación da errores 3–8 veces menores que el escalado "
                  "(≤ 1.5 % de mediana hasta 7 días). (b) El modelo mensual, evaluado dejando un año fuera, tiene un error "
                  "típico del 23 % (NSE 0.72); por eso solo se usa donde no hay suficientes días medidos.",
                  "Validación sintética: en meses completos se borraron huecos de 1 a 15 días y se compararon los totales "
                  "rellenados con los reales. El modelo mensual ln R<sub>m</sub> = a<sub>mes</sub> + b·ln(flow_sim) + "
                  "c·ln R<sub>m−1</sub> se evaluó con validación cruzada dejando un año fuera.",
                  "relleno_caudal.py, 28_validacion_relleno_caudal.py", png=SM / "fig_validacion_relleno_caudal.png",
                  csvs=[SM / "validacion_relleno_huecos_diarios.csv", SM / "validacion_relleno_modelo_mensual.csv",
                        SM / "resumen_relleno_caudal.csv"]))


pestana("p15a", "1.5.a Climatología", "Punto 1.5.a · Climatología de doce meses",
        f"P<sub>L</sub> llega a su máximo en marzo ({cmes('P_L', 3)['media']:.0f} mm de media) y a su mínimo en julio–agosto; "
        f"el caudal llega a su máximo en abril ({cmes('Q', 4)['media']:.0f} m³/s).",
        tarjeta("Ciclo anual medio con bandas de dispersión",
                "Línea continua = media; discontinua = mediana; banda oscura = rango intercuartílico (Q1–Q3); banda clara = "
                "percentiles 10–90. Elija la variable con los botones. Las bandas describen cuánto cambian los años entre sí; "
                "no son intervalos de confianza.",
                f"Los meses del periodo común ({PER}) se agrupan por mes calendario y en cada grupo se calculan media, mediana, "
                "cuartiles y percentiles 10 y 90 (interpolación lineal). Para T se usa PISCOt y, desde 2021, la estimación "
                "con ERA5-Land.",
                "20_climatologia_1_5a.py", grafica="clim",
                controles=selector("clim", VARS_CLIM),
                csvs=[CL / "climatologia_1_5a.csv"])
        + tarjeta("Precipitación media de cada mes sobre la cuenca",
                  "Doce mapas: la lluvia crece de diciembre a marzo, cuando cubre toda la cuenca, y en junio–agosto casi "
                  "desaparece. En los meses húmedos llueve más en las cabeceras del sureste. Del total anual de P<sub>L</sub>, "
                  f"DEF aporta el {TRIM_PCT['DEF']:.0f} %, MAM el {TRIM_PCT['MAM']:.0f} %, SON el {TRIM_PCT['SON']:.0f} % "
                  f"y JJA el {TRIM_PCT['JJA']:.0f} %.",
                  "Climatología mensual de CHIRPS (0.05°) en el periodo común, con la georreferencia corregida, interpolada "
                  "a la malla del DEM y con la escala discreta común a todos los mapas de agua: de blanco (seco) a azul oscuro (húmedo). El recuadro de cada "
                  "mapa compara el promedio de cuenca de CHIRPS con el de P<sub>L</sub>.",
                  "27_mapas_precipitacion_mensual.py", png=CL / "mapas_precipitacion_mensual_chirps.png"))

pestana("p15b", "1.5.b Ciclo anual", "Punto 1.5.b · Rasgos del ciclo anual y su variabilidad",
        f"Con los criterios propuestos, el régimen de P<sub>L</sub> es <b>{ip.loc['P_L', 'regimen']}</b>. "
        f"Años más húmedos según P<sub>L</sub>: {humedos}; más secos: {secos}.",
        tarjeta("Anomalías mensuales respecto al ciclo anual",
                "Barras = diferencia de cada mes respecto a la media de su mes calendario (azul por encima de lo normal, rojo "
                "por debajo; en T, rojo = más cálido). Línea = media móvil centrada de 12 meses, que deja ver los años húmedos "
                "y secos sin el ciclo estacional.",
                "Anomalía = valor del mes − media del mismo mes calendario en el periodo común. La media móvil exige al menos "
                "10 de los 12 meses. Para T se usa PISCOt y, desde 2021, la estimación con ERA5-Land.",
                "21_ciclo_anual_1_5b.py (página: 36_pagina_web.py)", grafica="anom", controles=selector("anom", VARS_ANOM),
                csvs=[SM_CSV, SM / "imerg_cuenca_mensual.csv"])
        + tarjeta("Anomalía anual (año calendario)",
                  "Suma de las anomalías de cada año (media para T). Los extremos húmedos coinciden con El Niño costero "
                  "(1998, 2017, 2023).",
                  "Suma de las 12 anomalías mensuales de cada año calendario completo del periodo común; usa la misma variable "
                  "elegida arriba.",
                  "21_ciclo_anual_1_5b.py", grafica="anomanual",
                  csvs=[CL / "anomalias_anio_calendario_1_5b.csv", CL / "anomalias_anio_hidrologico_1_5b.csv"])
        + tarjeta("Rasgos del ciclo anual",
                  f"(a) Forma y fase: el caudal va {lag_centroide('P_L'):.1f} meses detrás de P<sub>L</sub> según el centroide. "
                  f"(b) El máximo anual de P<sub>L</sub> cae en marzo en el {pct_mar:.0f} % de los años (feb–abr en el "
                  f"{pct_fa:.0f} %), y el del caudal en abril en el {pct_qabr:.0f} %. (c) Los dos subperiodos mantienen el mismo "
                  f"régimen. (d) Variabilidad entre años por mes; en los meses secos el CV es inestable porque la media es casi "
                  f"cero.",
                  "SI = índice de estacionalidad (Walsh & Lawler, 1981); PCI = índice de concentración (Oliver, 1980); "
                  f"centroide = Markham (1970). Mes pico de cada año, subperiodos 1998–2011 y 2012–{FIN.year}, y CV por mes con "
                  "prueba jackknife.",
                  "21_ciclo_anual_1_5b.py", png=CL / "fig_ciclo_1_5b.png",
                  csvs=[CL / "indicadores_estacionalidad_1_5b.csv", CL / "mes_pico_por_anio_1_5b.csv",
                        CL / "subperiodos_1_5b.csv", CL / "variabilidad_por_mes_1_5b.csv"])
        + tabla(t15, "Indicadores de estacionalidad (periodo común)",
                "R = caudal en lámina. Mes seco según Bagnouls–Gaussen (P < 2T). Unimodal si hay un solo pico y el armónico "
                "anual domina; bimodal si hay dos picos y el semianual es comparable; estacionalidad débil si SI < 0.40."))

pestana("p15c", "1.5.c Síntesis", "Punto 1.5.c · Síntesis y procesos",
        "Evidencia reunida para proponer la clasificación hidroclimática mensual. Para la aridez se usa un criterio climático "
        "(P/PET), no solo el total de lluvia. La clasificación final y su explicación física las sustenta el grupo con "
        "bibliografía.",
        tarjeta("Ciclo anual frente a la demanda de agua",
                "Con P<sub>L</sub>, la lluvia supera a la PET solo en feb–abr, y de mayo a agosto el caudal medio supera a la "
                f"lluvia del mismo mes (aporte de almacenamiento). Aridez UNEP (P/PET): P<sub>L</sub> "
                f"{ari.loc['P_L (CAMELS-PE)', 'AI_P_PET']:.2f} ({ari.loc['P_L (CAMELS-PE)', 'clase_UNEP']}), IMERG "
                f"{ari.loc['P_I (IMERG)', 'AI_P_PET']:.2f} ({ari.loc['P_I (IMERG)', 'clase_UNEP']}): la clase depende de la "
                "fuente de lluvia.",
                "Barras: lluvia media de cada mes (P<sub>L</sub> e IMERG). Líneas: PET de Penman–Monteith de CAMELS-PE "
                "(1998–2016), la mitad de la PET y el caudal en lámina. Debajo, cada mes clasificado por varios criterios; "
                "fila FAO: húmedo si P ≥ PET, intermedio si P ≥ 0.5·PET, seco si es menor.",
                "23_sintesis_ciclo_1_5c.py", png=CL / "fig_sintesis_ciclo_1_5c.png",
                csvs=[CL / "clasificacion_mensual_1_5c.csv", CL / "aridez_budyko_1_5c.csv", CL / "koppen_1_5c.csv",
                      CL / "laminas_estacionales_1_5c.csv"])
        + tabla(t15c, "Criterios, evidencia e incertidumbre",
                "«Lectura propuesta» es un apoyo cuantitativo para la discusión del grupo, no la conclusión."))

# ------------------------------------------------------------------ puntos 2, 3 y 4 (scripts 30–33 del grupo)
RE, MO, TE, ES = R / "relaciones", R / "modelos", R / "tendencias", R / "espectros"
_m21 = leer(RE / "metricas_2_1.csv")
_m21 = _m21[(_m21.serie == "original") & (_m21.muestra == "todos los meses")].set_index("par")
R21 = dict(a=_m21.loc["(a) P_I vs P_L", "pearson_r"], b=_m21.loc["(b) P_L vs Q̄", "spearman_rho"],
           c=_m21.loc["(c) P_I vs Q̄", "spearman_rho"])
E21 = leer(RE / "metricas_IMERG_por_estacion_2_1.csv", index_col=0).loc["todo el año"]
_rz = leer(RE / "rezagos_2_1.csv").query("lluvia == 'P_L'")
RZ = dict(k0=_rz.query("serie == 'original' and tipo == 'rezago P(t−k)' and k == 0").spearman_rho.iloc[0],
          k1=_rz.query("serie == 'original' and tipo == 'rezago P(t−k)' and k == 1").spearman_rho.iloc[0],
          acu=_rz.query("serie == 'original' and tipo == 'acumulada P(t−k..t)'").spearman_rho.max(),
          an1=_rz.query("serie == 'anomalías' and tipo == 'rezago P(t−k)' and k == 1").spearman_rho.iloc[0])

_td = leer(TE / "tendencias_todos_meses_3_4.csv")
_ta = _td[(_td.representacion == "anomalia") & _td.variable.isin(["P_L", "P_I", "Q", "T_PISCOt", "T_ERA5L"])]
t3 = _ta[["variable", "periodo", "inicio", "fin", "n", "metodo", "pend", "lo", "hi", "p", "unidad"]].copy()
t3["periodo"] = t3["periodo"].replace({"comun": "común"})
t3 = t3.round({"pend": 3, "lo": 3, "hi": 3, "p": 3})
t3.columns = ["Variable", "Periodo", "Inicio", "Fin", "n", "Método", "Pendiente", "IC inf.", "IC sup.", "p", "Unidad"]
TD = _ta.set_index(["variable", "periodo", "metodo"])


def pend3(v, per="completo", met="MK Hamed-Rao + Sen"):
    r = TD.loc[(v, per, met)]
    return f"{r.pend:+.2f} [{r.lo:+.2f}, {r.hi:+.2f}] (p = {r.p:.3f})"


_enso = leer(TE / "enso_3_6.csv").set_index("variable")
_esc = leer(TE / "escorrentia_anual_3_6.csv").set_index("serie_anual")
_mes = leer(TE / "tendencias_por_mes_3_4.csv")
_fdr = _mes[(_mes.representacion == "original") & (_mes.periodo == "completo") & (_mes.q_fdr < 0.05)]
FDR = {v: ", ".join(MESES[m - 1] for m in sorted(set(g.mes))) for v, g in _fdr.groupby("variable")}
_bd = leer(ES / "bandas_varianza_4_2.csv").set_index(["variable", "periodo", "transformacion", "banda"])["fraccion"]


def banda(v, tr, b, per="completo"):
    return 100 * _bd.loc[(v, per, tr, b)]


_me = leer(ES / "metadatos_espectros_4_1.csv")
RHO = _me[(_me.periodo == "completo") & (_me.transformacion == "anomalia")].set_index("variable")["rho1_AR1"]
OND = leer(ES / "onditas_resumen_4_3.csv").set_index("serie")
_pk = leer(ES / "picos_4_2.csv")
_pk = _pk[(_pk.periodo == "completo") & (_pk.transformacion == "anomalia")]
N_GLOBAL = int(_pk["supera_95_global"].astype(str).eq("True").sum())
t4 = _pk[_pk.groupby("variable").cumcount() < 3][["variable", "N_meses", "periodo_meses", "periodo_min_meses",
                                                  "periodo_max_meses", "k_ciclos_en_registro", "fraccion_varianza",
                                                  "cociente_fondo_AR1", "supera_95_puntual", "supera_95_global"]].copy()
t4["fraccion_varianza"] = (t4["fraccion_varianza"] * 100).round(1)
t4 = t4.round({"periodo_meses": 1, "periodo_min_meses": 0, "periodo_max_meses": 0, "cociente_fondo_AR1": 1})
t4.columns = ["Variable", "N", "Periodo (meses)", "Rango mín.", "Rango máx.", "Ciclos en el registro", "% varianza",
              "Cociente con AR(1)", "> 95 % puntual", "> 95 % global"]
_ls = leer(ES / "vacios_caudal_lombscargle_4_1.csv").set_index("banda")

# --- datos interactivos: evaluación fuera de muestra (2.3) y anomalías con tendencia de Sen (3.4)
_pr = leer(MO / "predicciones_2_3.csv", parse_dates=["fecha"])
_pr = _pr[_pr.conjunto == "evaluacion"]
OBS2 = {"P_L ← P_I": cam_full["P_L_mm_mes"], "Q̄ ← P_L": cam_full["Q_m3_s"]}
MOD2 = {"P_L ← P_I": [("ref", "Referencia: climatología"), ("lin", "Regresión lineal"),
                      ("mes", "Elegido: factor por mes calendario")],
        "Q̄ ← P_L": [("ref", "Referencia: climatología"), ("lin0", "Regresión lineal"),
                    ("logmK", "Elegido: ln Q̄ con término por mes y lluvia acumulada")]}
idx2 = pd.date_range(INI, FIN, freq="MS")
DATOS["modelos"] = {"fechas": [f"{f:%Y-%m}" for f in idx2]}
for obj, mods in MOD2.items():
    clave = "PL" if obj.startswith("P_L") else "Q"
    d2 = {"obs": lista(OBS2[obj].reindex(idx2), 2), "mods": []}
    for cod, nom in mods:
        s = _pr[(_pr.objetivo == obj) & (_pr.modelo == cod)].groupby("fecha")["estimado"].mean().reindex(idx2)
        d2["mods"].append({"nombre": nom, "y": lista(s, 2)})
    DATOS["modelos"][clave] = d2

_clr = leer(TE / "climatologia_referencia_3_2.csv")
_ser3 = {"P_L": cam_full["P_L_mm_mes"], "P_I": leer(SM / "imerg_cuenca_mensual.csv", index_col="fecha",
                                                    parse_dates=True)["P_I_mm_mes"],
         "Q": cam_full["Q_m3_s"], "T_PISCOt": cam_full["T_C"],
         "T_ERA5L": leer(SM / "era5land_t2m_cuenca_mensual.csv", index_col="fecha", parse_dates=True)["T_era5land_C"]}
DATOS["tend"] = {}
for v, s in _ser3.items():
    r = TD.loc[(v, "completo", "MK Hamed-Rao + Sen")]
    s = s.loc[pd.Timestamp(r.inicio + "-01"):pd.Timestamp(r.fin + "-01")]
    mu = _clr[_clr.variable == v].set_index("mes")["media"]
    a = (s - s.index.month.map(mu).values).dropna()
    t = a.index.year + (a.index.month - 0.5) / 12                      # años decimales, como el script 32
    b = r.pend / 10                                                    # pendiente por año
    c = float(np.median(a.values - b * t))                             # ordenada de Sen
    DATOS["tend"][v] = {"fechas": [f"{f:%Y-%m}" for f in a.index], "a": lista(a, 3),
                        "mm12": lista(a.rolling(12, center=True, min_periods=10).mean(), 3),
                        "sen": [round(c + b * t[0], 3), round(c + b * t[-1], 3)],
                        "sen_x": [f"{a.index[0]:%Y-%m}", f"{a.index[-1]:%Y-%m}"],
                        "txt": f"Sen {r.pend:+.2f} {r.unidad} [{r.lo:+.2f}, {r.hi:+.2f}], p = {r.p:.3f}",
                        "unid": r.unidad.split("/")[0] if v.startswith("T") else r.unidad.rsplit("/", 1)[0]}
(WEB / "datos.js").write_text("window.DATOS = " + json.dumps(DATOS, ensure_ascii=False, separators=(",", ":")) + ";\n",
                              encoding="utf-8")

pestana("p2", "2 Relaciones", "Punto 2 · Relaciones entre series y modelos estadísticos",
        f"Comparaciones mensuales con los meses coincidentes del periodo común ({PER}). El caudal usa la serie rellenada; "
        f"las métricas sin los meses rellenados están en los CSV como prueba de sensibilidad.",
        tarjeta("Dispersión entre lluvia y caudal",
                f"(a) IMERG frente a P<sub>L</sub>: muy correlacionadas (r = {R21['a']:.2f}) pero no concordantes: IMERG "
                f"queda bajo la línea 1:1 en los meses húmedos (sesgo {E21['sesgo']:+.1f} mm/mes, {E21['sesgo_pct']:+.0f} %) "
                f"y algo por encima en jun–ago. (b, c) La relación de la lluvia del mismo mes con el caudal es débil "
                f"(Spearman ρ = {R21['b']:.2f} con P<sub>L</sub> y {R21['c']:.2f} con IMERG) y muy dispersa: lluvias "
                f"parecidas dan caudales que difieren hasta 100 veces según la época.",
                "Pares mensuales coincidentes del periodo común, coloreados por estación de la cuenca (húmeda dic–abr, transición oct–nov, seca may–sep). IMERG–P<sub>L</sub> con línea 1:1 "
                "y escalas iguales; sesgo, MAE y RMSE de P<sub>I</sub> − P<sub>L</sub>. Pearson y Spearman. El caudal va en "
                "escala logarítmica porque varía tres órdenes de magnitud; (b') compara láminas (R frente a P<sub>L</sub>).",
                "30_relaciones_2_1.py", png=RE / "fig_dispersion_2_1.png",
                csvs=[RE / "metricas_2_1.csv", RE / "metricas_IMERG_por_estacion_2_1.csv"],
                leer_="En lámina, casi todos los meses quedan bajo la línea R = P<sub>L</sub>; los que la superan son de "
                      "may–ago (aporte de almacenamiento) y crecidas de El Niño.")
        + tarjeta("La lluvia de meses anteriores explica mejor el caudal",
                  f"El caudal se relaciona mejor con la lluvia del mes anterior (ρ = {RZ['k1']:.2f}) que con la del mismo "
                  f"mes ({RZ['k0']:.2f}), y aún mejor con la lluvia acumulada de los últimos meses (ρ = {RZ['acu']:.2f}): la "
                  f"cuenca almacena agua y la entrega con retraso. En anomalías la asociación se debilita pero persiste "
                  f"(ρ = {RZ['an1']:.2f} con un mes de rezago).",
                  "Correlación de Spearman entre el caudal del mes t y la lluvia del mes t − k (rezagos) o la acumulada de "
                  "t − k a t, en la serie original y en anomalías. La lluvia siempre antecede al caudal; nunca se usa lluvia "
                  "futura.", "30_relaciones_2_1.py", png=RE / "fig_rezagos_2_1.png", csvs=[RE / "rezagos_2_1.csv"])
        + tarjeta("Observado frente a modelado, fuera del periodo de ajuste",
                  "Cada modelo se ajustó con unos años y se evaluó con otros que no vio: partición B (ajuste 2007–2024, "
                  "evaluación 1998–2006) y partición A (ajuste 1998–2015, evaluación 2016–2024). El hueco 2007–2015 no se "
                  "evalúa. Para la lluvia local, el factor por mes calendario corrige el sesgo de IMERG en los meses "
                  "húmedos; para el caudal, el modelo logarítmico sigue la recesión y el estiaje, pero subestima la crecida "
                  "de El Niño costero de 2017.",
                  "Predicciones de la evaluación por bloques de años (script 31). Referencia = climatología del mes "
                  "calculada con los años de ajuste. Modelos elegidos por validación cruzada dentro del ajuste. Elija el "
                  "objetivo con los botones; las series se activan o desactivan en la leyenda.",
                  "31_modelos_2_2_2_3.py (página: 36_pagina_web.py)", grafica="modelos",
                  controles=selector("modelos", [("PL", "P<sub>L</sub> ← IMERG"), ("Q", "Q̄ ← P<sub>L</sub>")]),
                  csvs=[MO / "predicciones_2_3.csv", MO / "seleccion_cv_2_2.csv", MO / "evaluacion_2_3.csv"])
        + tarjeta("¿Mejoran los modelos a una referencia sencilla?",
                  "Para P<sub>L</sub> a partir de IMERG, un factor de corrección por mes calendario reduce el error típico "
                  "cerca de 40 %. Para el caudal, solo los modelos logarítmicos con término por mes y lluvia acumulada "
                  "(2–3 meses de rezago) mejoran la climatología; la regresión lineal simple es peor que la climatología.",
                  "Habilidad = 1 − MAE / MAE de la referencia (climatología), en las dos particiones por bloques de años. "
                  "★ = modelo elegido por validación cruzada dentro del ajuste.",
                  "31_modelos_2_2_2_3.py", png=MO / "fig_evaluacion_resumen_2_3.png",
                  csvs=[MO / "evaluacion_2_3.csv", MO / "coeficientes_2_2.csv"])
        + tarjeta("Modelo de lluvia local a partir de IMERG",
                  "Evaluación 2016–2024 del modelo elegido (factor por mes calendario) frente a IMERG sin corregir y a la "
                  "regresión lineal, con los residuos frente al tiempo, al valor estimado y al mes.",
                  "Ajuste 1998–2015; residuo = observado − estimado. Los residuos por mes muestran si queda sesgo "
                  "estacional sin corregir.", "31_modelos_2_2_2_3.py", png=MO / "fig_modelo_PL_2_3.png")
        + tarjeta("Modelo de caudal a partir de la lluvia local",
                  "Evaluación 2016–2024 del modelo elegido (ln Q̄ con intercepto por mes y lluvia de los últimos meses). "
                  "Sigue bien la recesión y el estiaje, pero subestima la crecida de El Niño costero de 2017 (residuo de "
                  "−310 m³/s en abril). La regresión lineal da caudales negativos.",
                  "Ajuste 1998–2015 en escala logarítmica; la transformación de vuelta incluye la corrección por sesgo.",
                  "31_modelos_2_2_2_3.py", png=MO / "fig_modelo_Q_2_3.png",
                  leer_="Una relación estadística lluvia–caudal no conserva masa ni sustituye el balance hídrico."))

pestana("p3", "3 Tendencias", "Punto 3 · Tendencias hidroclimáticas",
        f"Cada variable se analiza con su registro mensual completo (cambio de largo plazo) y, aparte, en el periodo común "
        f"{PER} (comparación entre fuentes). Las anomalías usan una climatología fija 1998–2020, el periodo más largo en que "
        f"las cinco series tienen datos. Pendientes por década; en precipitación son cambios del acumulado mensual, no del "
        f"anual.",
        tarjeta("Anomalías y tendencia de Sen, registro completo",
                f"La temperatura sube en las dos fuentes (PISCOt {pend3('T_PISCOt')} °C/década; ERA5-Land "
                f"{pend3('T_ERA5L')} °C/década) de forma casi lineal. P<sub>L</sub> no muestra tendencia "
                f"({pend3('P_L')} mm/mes/década) y el caudal tampoco ({pend3('Q')} m³/s/década). IMERG sí baja "
                f"({pend3('P_I')} mm/mes/década), aunque la lluvia de referencia en el mismo periodo no lo hace.",
                "Anomalía = valor del mes − media del mismo mes en 1998–2020. Barras = anomalía mensual; línea gris = media "
                "móvil de 12 meses; recta = tendencia de Sen con prueba de Mann–Kendall corregida por autocorrelación "
                "(Hamed–Rao), del script 32. La ordenada de la recta es la mediana de a − b·t. Elija la variable con los "
                "botones.",
                "32_tendencias_3.py (página: 36_pagina_web.py)", grafica="tend",
                controles=selector("tend", [("P_L", "P<sub>L</sub>"), ("P_I", "P<sub>I</sub>"), ("Q", "Q̄"),
                                            ("T_PISCOt", "T PISCOt"), ("T_ERA5L", "T ERA5-Land")]),
                csvs=[TE / "tendencias_todos_meses_3_4.csv", TE / "climatologia_referencia_3_2.csv"])
        + tarjeta("Series originales, anomalías y anomalías estandarizadas",
                  "Las tres representaciones de cada serie con sus tendencias: la conclusión no cambia entre ellas porque "
                  "restar la media del mes no cambia la pendiente y dividir por la desviación solo cambia la escala.",
                  "Izquierda: serie original con un modelo aditivo (efecto de cada mes + curva suave) y OLS con efectos de "
                  "mes. Centro: anomalía a = X − μ<sub>mes</sub> con banda de remuestreo por bloques. Derecha: "
                  "z = a / s<sub>mes</sub>. OLS con errores robustos a autocorrelación (HAC), Mann–Kendall con pendiente de "
                  "Sen y LOWESS como curva exploratoria.",
                  "32_tendencias_3.py", png=TE / "fig_series_tendencias_3_4.png",
                  leer_="El panel de caudal tiene el eje recortado por la crecida de 1998.")
        + tarjeta("Tendencia de cada mes calendario",
                  "Tras controlar la tasa de falsos descubrimientos (FDR) sobre 60 pruebas, las tendencias que se sostienen "
                  f"son de temperatura (ERA5-Land: {FDR.get('T_ERA5L', 'ninguno')}; PISCOt: {FDR.get('T_PISCOt', 'ninguno')}), "
                  "con el mayor calentamiento al final de la estación seca y en la transición a la húmeda (ago–nov). En lluvia "
                  f"y caudal solo quedan casos aislados (P<sub>L</sub>: {FDR.get('P_L', 'ninguno')}; P<sub>I</sub>: "
                  f"{FDR.get('P_I', 'ninguno')}; Q̄: {FDR.get('Q', 'ninguno')}) que no son consistentes entre métodos.",
                  "Doce subseries por variable (todos los eneros, todos los febreros…), con Mann–Kendall corregido y "
                  "pendiente de Sen en cada una; corrección de Benjamini–Hochberg por pruebas múltiples.",
                  "32_tendencias_3.py", png=TE / "fig_pendientes_mensuales_3_5.png",
                  csvs=[TE / "tendencias_por_mes_3_4.csv", TE / "verificacion_transformaciones_3_3.csv"])
        + tarjeta("Robustez frente a método, periodo y fuente",
                  "Las tendencias de temperatura persisten al cambiar el método, recortar los extremos del registro o retirar "
                  "los años de El Niño costero. En precipitación el signo depende de la fuente y del periodo: P<sub>L</sub> y "
                  "PISCOp v3 son ligeramente positivas en 1981–2025 y negativas, sin significancia, en 1998–2024, mientras "
                  "IMERG y CHIRPS son negativas. La tendencia de IMERG desaparece si se empieza en 2003.",
                  "Misma prueba repetida con otros métodos (● Sen con MK Hamed–Rao; ■ OLS-HAC), otros periodos y otras "
                  "fuentes de precipitación; relleno = p < 0.05.",
                  "32_tendencias_3.py", png=TE / "fig_robustez_3_5.png", csvs=[TE / "sensibilidad_3_5.csv"])
        + tarjeta("Sensibilidad a la fecha inicial y final",
                  "En lluvia y caudal el signo de la tendencia cambia según el año inicial, sobre todo si la ventana empieza o "
                  "termina en un año de El Niño (1983, 1998, 2017); en temperatura es positivo en casi todas las ventanas.",
                  "Pendiente de Sen de las anomalías anuales para todas las ventanas de 15 años o más (año inicial × año "
                  "final).", "32_tendencias_3.py", png=TE / "fig_ventanas_inicio_fin_3_5.png",
                  csvs=[TE / "segmentada_pettitt_3_5.csv", TE / "tramos_lowess_3_4.csv"])
        + tarjeta("¿A qué podrían deberse los cambios?",
                  f"Los años húmedos y de caudal alto coinciden con El Niño 1+2 cálido (r mensual con P<sub>L</sub> "
                  f"{_enso.loc['P_L', 'r_Nino12']:.2f}, con T PISCOt {_enso.loc['T_PISCOt', 'r_Nino12']:.2f}); retirar la "
                  f"señal ENSO no elimina el calentamiento. En años hidrológicos, el caudal dada la lluvia baja "
                  f"{_esc.loc['resid_R_dado_P', 'sen_dec']:+.0f} mm/año por década (p = {_esc.loc['resid_R_dado_P', 'p_mk']:.2f}), "
                  "algo compatible con más evapotranspiración o con usos del agua, pero que también depende de la crecida de "
                  "1998 al inicio del registro. Es una hipótesis por contrastar, no una atribución.",
                  "Correlación con el índice Niño 1+2 (ERSST v5, NOAA) y tendencia tras retirarlo por regresión; balance "
                  "anual por año hidrológico y residuo de la escorrentía dada la lluvia.",
                  "32_tendencias_3.py", png=TE / "fig_causas_3_6.png",
                  csvs=[TE / "enso_3_6.csv", TE / "escorrentia_anual_3_6.csv", TE / "balance_anual_hidrologico_3_6.csv"],
                  leer_="Para atribuir faltan datos de uso del agua, de cambios de cobertura y metadatos de la estación.")
        + tabla(t3, "Tendencia de las anomalías, todos los meses",
                "Pendiente por década con IC 95 %. OLS-HAC: Newey–West con 12 rezagos. MK Hamed–Rao + Sen: IC de Gilbert con "
                "la varianza corregida."))

pestana("p4", "4 Fourier", "Punto 4 · Escalas dominantes de variabilidad (Fourier)",
        f"Espectros de la secuencia mensual (Δt = 1 mes) de cada variable, en su registro completo y en el periodo común "
        f"{PER}. Se comparan la serie centrada (conserva el ciclo anual) y las anomalías respecto a la climatología "
        f"1998–2020, con y sin la tendencia del punto 3.",
        tarjeta("Qué periodos dominan (% de la varianza)",
                f"Es la lectura más directa del espectro. En las series centradas manda el ciclo anual: "
                f"{banda('P_L', 'centrada', 'anual 11–13 m'):.0f} % de la varianza de P<sub>L</sub> y "
                f"{banda('Q', 'centrada', 'anual 11–13 m'):.0f} % del caudal, más el semianual (6 meses) por la estación "
                f"húmeda concentrada. Al quitar la climatología ningún periodo domina: en la lluvia y el caudal cada pico "
                f"interanual reúne apenas 2–5 % de la varianza (2.1, 5 y 9 años), mientras que en la temperatura destaca "
                f"un pico de unos 3.7 años con 10–14 %. Los periodos largos se apoyan en muy pocos ciclos dentro del "
                f"registro (un pico de 9 años cabe 3 veces en 28 años).",
                "Periodograma de la FFT (registro completo) expresado como fracción de la varianza total en cada "
                "frecuencia k/N: % = S<sub>k</sub>·Δf / varianza. Eje de periodo lineal en años, creciente hacia la "
                "derecha; los periodos mayores de 20 años quedan fuera del eje y su % se indica en el panel. Se rotulan "
                "los cuatro máximos locales mayores; * = supera el 95 % puntual de un fondo AR(1) (no el umbral global, "
                "que ningún pico supera). Escala vertical propia de cada panel.",
                "33_espectros_4.py", png=ES / "fig_espectros_porcentaje_4_2.png",
                csvs=[ES / "espectros_4.csv", ES / "picos_4_2.csv"])
        + tarjeta("Onditas: en qué años aparece cada periodo",
                  "La variabilidad fuera del ciclo anual no es constante en el tiempo. En la lluvia, la banda de 4–5 años es "
                  "significativa entre 1983 y 2000 (El Niño 1983 y 1997–98) y después casi desaparece; por eso los mapas de "
                  "SST del punto 5 cambian entre 1981–2002 y 2003–2024. El caudal solo muestra pulsos cortos en 1998 y "
                  "2017. La temperatura mantiene una banda de 3–5 años durante todo el registro, igual que Niño 1+2.",
                  "Transformada continua con la ondita de Morlet (ω0 = 6) de las anomalías estandarizadas (Torrence y "
                  "Compo 1998), con la potencia corregida por sesgo (Liu et al. 2007: se divide por la escala, porque sin "
                  "corregir se inflan los periodos largos) y expresada en % de la varianza por octava de periodo. Contorno: "
                  "supera el 95 % de un ruido rojo AR(1); rayado: cono de influencia (efecto de los bordes); a la derecha, el "
                  "espectro global (promedio en el tiempo) sobre el periodograma de Fourier en la misma unidad: el espectro "
                  "global es un Fourier suavizado, por eso coinciden los picos. El relleno con ceros es interno a la "
                  "transformada; los datos no se rellenan.",
                  "38_onditas_4.py", png=ES / "fig_onditas_4_3.png", csvs=[ES / "onditas_resumen_4_3.csv"])
        + tarjeta("¿La banda de 2–7 años va con el ENSO?",
                  f"La componente de 2–7 años de la lluvia sigue a Niño 1+2 (r = {OND.loc['P_L', 'r_comp_2_7a_con_N12']:.2f}) "
                  f"y casi nada a Niño 3.4 (r = {OND.loc['P_L', 'r_comp_2_7a_con_N34']:.2f}): es el ENSO costero, no el "
                  f"del Pacífico central. El caudal la sigue menos (r = {OND.loc['Q', 'r_comp_2_7a_con_N12']:.2f}) y la "
                  f"temperatura mucho más (r = {OND.loc['T_ERA5L', 'r_comp_2_7a_con_N34']:.2f} con Niño 3.4). Pero esa "
                  f"banda es una parte pequeña de las anomalías de la cuenca: "
                  f"{100 * OND.loc['P_L', 'var_componente_2_7a']:.0f} % en la lluvia, "
                  f"{100 * OND.loc['Q', 'var_componente_2_7a']:.0f} % en el caudal y "
                  f"{100 * OND.loc['T_ERA5L', 'var_componente_2_7a']:.0f} % en la temperatura. Solo en 1997–98 la banda de "
                  f"la lluvia se acerca al umbral del 95 %.",
                  "(a) Varianza promediada en 2–7 años dividida por su umbral del 95 % (TC98 ec. 24–28). (b) Componente de "
                  "2–7 años reconstruida (ec. 29) y su correlación con la de Niño 1+2: es descriptiva, porque una serie "
                  "filtrada a 2–7 años tiene muy pocos grados de libertad.",
                  "38_onditas_4.py", png=ES / "fig_onditas_banda_4_3.png",
                  csvs=[ES / "onditas_resumen_4_3.csv", ES / "onditas_banda_4_3.csv"])
        + tarjeta("Espectros del registro completo",
                f"En las series centradas domina el ciclo anual en la lluvia (P<sub>L</sub> "
                f"{banda('P_L', 'centrada', 'anual 11–13 m'):.0f} % de la varianza; IMERG "
                f"{banda('P_I', 'centrada', 'anual 11–13 m'):.0f} %), con un armónico semianual que refleja la estación "
                f"húmeda concentrada en pocos meses. En el caudal el ciclo anual pesa menos "
                f"({banda('Q', 'centrada', 'anual 11–13 m'):.0f} %) porque las crecidas de El Niño reparten varianza en "
                f"todas las frecuencias; en la temperatura el ciclo anual es pequeño (PISCOt "
                f"{banda('T_PISCOt', 'centrada', 'anual 11–13 m'):.0f} %). Sin la climatología, la lluvia se parece a ruido "
                f"casi blanco (AR(1): ρ = {RHO['P_L']:.2f}); el caudal es más rojo (ρ = {RHO['Q']:.2f}) y la temperatura "
                f"mucho más (ρ = {RHO['T_PISCOt']:.2f}–{RHO['T_ERA5L']:.2f}).",
                "Periodograma de la FFT sin relleno con ceros: f<sub>k</sub> = k/N, Δf = 1/N ciclos/mes, densidad unilateral "
                "normalizada para que Σ S·Δf sea la varianza; se contrasta con ventana de Hann y con Welch (segmentos de 10 "
                "años). El eje horizontal muestra el periodo en años (periodo = 1 / (12 f)), con los periodos largos a la "
                "derecha. Línea gris continua: fondo AR(1); discontinua y punteada: umbrales al 95 % puntual y global (corregido por buscar entre todas las "
                "frecuencias). Las dos columnas de cada variable tienen la misma escala vertical. "
                + ("Ningún pico de las anomalías supera el umbral global" if N_GLOBAL == 0 else
                   f"Solo {N_GLOBAL} picos de las anomalías superan el umbral global")
                + ": los picos interanuales no son periodicidades demostradas.",
                "33_espectros_4.py", png=ES / "fig_espectros_4_2.png",
                csvs=[ES / "metadatos_espectros_4_1.csv", ES / "picos_4_2.csv"])
        + tarjeta("Los mismos espectros en frecuencia (ciclos/mes)",
                  "Es la figura anterior con el eje horizontal en frecuencia, como pide la guía: el ciclo anual está en "
                  "1/12 ≈ 0.083 ciclos/mes, el semianual en 1/6 ≈ 0.167 y la frecuencia de Nyquist en 0.5 ciclos/mes "
                  "(periodo mínimo resoluble de 2 meses). La banda sombreada de 2–7 años va de 0.012 a 0.042 ciclos/mes.",
                  "Mismos periodogramas, Welch y fondos AR(1) que en la figura en periodos; solo cambia el eje x "
                  "(escala logarítmica en ciclos/mes).",
                  "33_espectros_4.py", png=ES / "fig_espectros_frecuencia_4_2.png",
                  csvs=[ES / "espectros_4.csv"])
        + tarjeta("¿En qué escalas está la varianza?",
                  f"Al quitar la climatología, la banda anual cae casi a cero en la lluvia, pero el caudal conserva "
                  f"{banda('Q', 'anomalia', 'anual 11–13 m'):.0f} %: la amplitud del ciclo anual del caudal cambia mucho de un "
                  f"año a otro. La banda interanual de 2–7 años reúne {banda('P_L', 'anomalia', 'interanual 2–7 años'):.0f} % "
                  f"de las anomalías de P<sub>L</sub>, {banda('Q', 'anomalia', 'interanual 2–7 años'):.0f} % del caudal y "
                  f"{banda('T_PISCOt', 'anomalia', 'interanual 2–7 años'):.0f} % de la temperatura PISCOt.",
                  "Fracción del periodograma en cada banda de periodo; cada barra suma 100 %. Registros de distinta longitud "
                  "tienen distinta resolución: se comparan filas del mismo periodo.",
                  "33_espectros_4.py", png=ES / "fig_bandas_varianza_4_2.png", csvs=[ES / "bandas_varianza_4_2.csv"])
        + tarjeta("Fuentes y respuesta de la cuenca",
                  "CAMELS-PE e IMERG tienen la misma forma espectral en las series centradas; en anomalías IMERG tiene más "
                  "varianza relativa en escalas de 2–5 meses. PISCOt y ERA5-Land coinciden en casi todas las escalas. En las "
                  f"anomalías del periodo común, la escala de 2–5 meses reúne "
                  f"{banda('Q', 'anomalia', 'intraestacional 2–5 m', 'comun'):.0f} % de la varianza del caudal frente a "
                  f"{banda('P_L', 'anomalia', 'intraestacional 2–5 m', 'comun'):.0f} % de la lluvia: el almacenamiento de la "
                  f"cuenca suaviza las variaciones rápidas y da persistencia.",
                  "Formas espectrales normalizadas por la varianza (las alturas no son variabilidad absoluta), en el periodo "
                  "común para comparar fuentes con la misma resolución.",
                  "33_espectros_4.py", png=ES / "fig_comparacion_espectros_4_2.png",
                  leer_="Un espectro de potencia no contiene la fase: los desfases lluvia–caudal se estiman en el punto 2.")
        + tarjeta("Estabilidad de los resultados",
                  "La banda anual y la interanual cambian poco con la tendencia o al recortar extremos, pero el periodo del pico "
                  "interanual cambia con la ventana y con la mitad del registro analizada (P<sub>L</sub> pasa de unos 5 a unos "
                  "2.4 años). Con unos 8–13 ciclos en el registro, los periodos interanuales solo se pueden dar como bandas "
                  "amplias.",
                  "Espectros repetidos sin tendencia, con extremos recortados, con otras ventanas y con cada mitad del registro.",
                  "33_espectros_4.py", png=ES / "fig_estabilidad_4_2.png", csvs=[ES / "estabilidad_4_2.csv"])
        + tarjeta("Efecto de los vacíos del caudal",
                  f"Con solo los meses observados completos, la banda de 2–5 meses pasa de "
                  f"{100 * _ls.loc['intraestacional 2–5 m', 'relleno_FFT']:.0f} % a "
                  f"{100 * _ls.loc['intraestacional 2–5 m', 'observado_LombScargle']:.0f} % de la varianza y bajan las bandas "
                  "largas: las conclusiones sobre escalas cortas del caudal son las más inciertas.",
                  "Lomb–Scargle (estimador para muestreo irregular) con los meses observados completos frente a la FFT de la "
                  "serie rellenada; en la malla regular ambos métodos dan lo mismo, así que la diferencia la producen los "
                  "vacíos, no el método.",
                  "33_espectros_4.py", png=ES / "fig_vacios_caudal_4_1.png", csvs=[ES / "vacios_caudal_lombscargle_4_1.csv"])
        + tabla(t4, "Picos principales de las anomalías (registro completo)",
                "Rango = periodos que caben en ±½ bin de frecuencia (Δf = 1/N). Ciclos = número de oscilaciones completas en "
                "el registro."))

# ------------------------------------------------------------------ punto 5 (script 37)
CO = R / "correlaciones"
R5 = leer(CO / "resumen_mapas_5.csv")
I5 = leer(CO / "indices_5_4.csv")
TM5 = leer(CO / "todos_meses_5.csv").set_index(["variable", "campo"])
RB5 = leer(CO / "robustez_5_3.csv")


def idx5(var, ind, mes, col="pearson_r"):
    return float(I5[(I5.variable == var) & (I5.indice == ind) & (I5.mes == mes)][col].iloc[0])


def area5(var, campo, rez=0):
    g = R5[(R5.variable == var) & (R5.campo == campo) & (R5.rezago == rez)]
    b = g.loc[g.frac_area_FDR.idxmax()]
    return f"{100 * b.frac_area_FDR:.0f} % del área en {MESES[int(b.mes) - 1].lower()}"


def rob5(var, campo, variante, meses=range(1, 13)):
    g = RB5[(RB5.variable == var) & (RB5.campo == campo) & RB5.variante.str.startswith(variante) & RB5.mes.isin(list(meses))]
    return g.corr_patrones.median()


N12, N34, UA = "Niño 1+2 (SST)", "Niño 3.4 (SST)", "Andes norte de Perú (u200)"
METODO5 = ("Correlación entre años (27 valores de cada mes calendario, 1998–2024) de las anomalías de la cuenca y de "
           "cada celda (referencia 1998–2020), sin rezago. Malla de 2°. Prueba t con n efectivo según la persistencia "
           "entre años de ambas series y control FDR de Benjamini–Hochberg (α = 0.10, familia = las celdas de cada mapa "
           "en 60°S–60°N; Wilks 2016). Escala común de −1 a 1; gris = tierra en SST o sin dato; estrella = cuenca.")
pestana("p5", "5 Clima global", "Punto 5 · Mapas de correlación con el clima global",
        "Qué regiones oceánicas y patrones atmosféricos se asocian con la lluvia y el caudal de la cuenca, mes a mes. "
        "Campos: SST (ERSST v5), presión al nivel del mar (ERA5) y viento zonal en 200 hPa (ERA5). La SST la pide la "
        "guía; la presión representa el anticiclón del Pacífico sur (la subsidencia que frena la lluvia en la estación "
        "seca) y el dipolo de presión del ENSO; el viento en 200 hPa, los vientos del este en altura que acompañan el "
        "transporte de humedad desde la Amazonía. No se usó la altura geopotencial en 500 hPa porque en el trópico es casi "
        "uniforme y sigue a la SST, ni la humedad específica, que en los niveles bajos queda bajo el terreno sobre los Andes.",
        tarjeta("Caudal frente a SST",
                f"En enero y marzo el caudal crece con el calentamiento del Pacífico ecuatorial este, frente a la costa de "
                f"Perú y Ecuador (región Niño 1+2): r = {idx5('Q', N12, 1):.2f} en enero y {idx5('Q', N12, 3):.2f} en "
                f"marzo con el índice Niño 1+2, los únicos valores de SST que pasan el FDR de los índices. En los mapas "
                f"pasa el FDR como máximo el {area5('Q', 'sst')}. Pero la asociación depende de pocos años: con Spearman "
                f"la de enero baja a ρ = {idx5('Q', N12, 1, 'spearman_rho'):.2f}, y sin 1998, 2017 y 2023 el patrón de "
                f"febrero–marzo casi desaparece (correlación de patrones {rob5('Q', 'sst', 'sin 1998', [2, 3]):.1f}). Es la "
                f"huella de los Niños costeros extremos, no una relación que se repita todos los años.",
                METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_Q_sst_5.png",
                csvs=[CO / "resumen_mapas_5.csv", CO / "indices_5_4.csv"])
        + tarjeta("Lluvia local frente a SST",
                  f"P<sub>L</sub> muestra el mismo signo frente a Niño 1+2 en enero–abril (r = {idx5('P_L', N12, 2):.2f} a "
                  f"{idx5('P_L', N12, 3):.2f}), pero más débil que el caudal y sin pasar el FDR. Casi ninguna celda pasa "
                  f"el FDR ({area5('P_L', 'sst')}), y el patrón cambia entre 1981–2002 y 2003–2024 (correlación de patrones "
                  f"mediana {rob5('P_L', 'sst', '1981'):.1f}): la relación lluvia–SST no es estable.",
                  METODO5 + " En jun–ago P<sub>L</sub> ≈ 0 y r es inestable.", "37_correlaciones_5.py",
                  png=CO / "fig_corr_P_L_sst_5.png", csvs=[CO / "resumen_mapas_5.csv"])
        + tarjeta("Caudal frente a la presión al nivel del mar",
                  f"El caudal de enero–febrero se asocia con presión más baja frente a la costa de Perú y Ecuador y más alta "
                  f"en el Pacífico ecuatorial oeste: el dipolo del ENSO (hasta el {area5('Q', 'msl')} pasa el FDR). Con todos "
                  f"los meses juntos en anomalías es el campo más coherente: {100 * TM5.loc[('Q', 'msl'), 'frac_area_FDR']:.0f} % "
                  f"del área con el caudal y {100 * TM5.loc[('P_L', 'msl'), 'frac_area_FDR']:.0f} % con la lluvia.",
                  METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_Q_msl_5.png", csvs=[CO / "resumen_mapas_5.csv"])
        + tarjeta("Lluvia local frente a la presión al nivel del mar",
                  f"Pocas celdas pasan el FDR ({area5('P_L', 'msl')}); el patrón de la lluvia está menos organizado que el "
                  "del caudal.",
                  METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_P_L_msl_5.png", csvs=[CO / "resumen_mapas_5.csv"])
        + tarjeta("Lluvia local frente al viento zonal en 200 hPa",
                  f"Llueve más cuando hay más viento del este en altura sobre los Andes del norte de Perú (r negativo: u más "
                  f"negativa = más viento del este): r = {idx5('P_L', UA, 4):.2f} en abril y {idx5('P_L', UA, 9):.2f} en "
                  f"septiembre con la caja 0–15°S, 85–70°O (septiembre pasa el FDR de los índices). El efecto aparece en los "
                  f"bordes de la estación húmeda (abr–may y sep–oct); con IMERG sale lo mismo en abril "
                  f"(r = {idx5('P_I', UA, 4):.2f}).",
                  METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_P_L_u200_5.png",
                  csvs=[CO / "resumen_mapas_5.csv", CO / "indices_5_4.csv"])
        + tarjeta("Caudal frente al viento zonal en 200 hPa",
                  f"Asociaciones débiles y dispersas (máximo {area5('Q', 'u200')} con FDR).",
                  METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_Q_u200_5.png", csvs=[CO / "resumen_mapas_5.csv"])
        + tarjeta("Sensibilidad a la fuente: IMERG frente a SST",
                  f"Con IMERG la señal de Niño 1+2 en la estación húmeda se debilita (r = {idx5('P_I', N12, 2):.2f} en febrero y "
                  f"{idx5('P_I', N12, 3):.2f} en marzo, frente a {idx5('P_L', N12, 2):.2f} y {idx5('P_L', N12, 3):.2f} con P<sub>L</sub>), aunque el patrón global se parece al de "
                  f"P<sub>L</sub> (correlación de patrones mediana {rob5('P_L', 'sst', 'IMERG'):.1f}). Es coherente con "
                  "que IMERG subestima los meses muy lluviosos (puntos 1.2 y 2).",
                  METODO5, "37_correlaciones_5.py", png=CO / "fig_corr_P_I_sst_5.png", csvs=[CO / "resumen_mapas_5.csv"])
        + tarjeta("Todos los meses juntos (anomalías)",
                  "Al juntar los 324 meses en anomalías (sin el ciclo anual compartido), la presión al nivel del mar muestra "
                  "el patrón más extenso: presión baja en el Pacífico este y alta en el oeste cuando hay más caudal y lluvia. "
                  "Las correlaciones son bajas (|r| ≤ 0.36) porque mezclan meses secos y húmedos.",
                  "Pearson entre las 324 anomalías mensuales 1998–2024 de la cuenca y de cada celda; n efectivo según la "
                  "autocorrelación mensual; FDR α = 0.10.", "37_correlaciones_5.py", png=CO / "fig_corr_todos_meses_5.png",
                  csvs=[CO / "todos_meses_5.csv"])
        + tarjeta("Índices: Niño y cajas de cada campo",
                  "Resumen de los mapas en índices (una prueba por índice y mes). Solo tres pasan el FDR: el caudal con Niño "
                  "1+2 en enero y marzo, y P<sub>L</sub> con el viento del este sobre los Andes en septiembre. Niño 3.4 "
                  "(Pacífico central) se asocia menos que Niño 1+2 en la estación húmeda: lo que pesa es el mar frente a la "
                  "costa.",
                  "Niño 1+2 y Niño 3.4: anomalías de ERSST v5 publicadas por CPC/NOAA (base 1991–2020). Cajas: promedio "
                  "ponderado por área de las anomalías del campo. * p < 0.05 con n efectivo; ** además q FDR < 0.05 "
                  "(familia: 12 meses × 7 índices de cada variable).", "37_correlaciones_5.py",
                  png=CO / "fig_indices_5_4.png", csvs=[CO / "indices_5_4.csv"])
        + tarjeta("Robustez de los patrones",
                  "Los mapas casi no cambian al quitar la tendencia. Cambian mucho al quitar 1998, 2017 y 2023 en ene–abr, "
                  "con Spearman en la estación húmeda del caudal y entre los subperiodos 1981–2002 y 2003–2024: las "
                  "asociaciones de la estación húmeda dependen de los años El Niño extremos y no son estables en el tiempo. "
                  "Con el caudal, el rezago de un mes da el mismo patrón de SST todo el año; con presión y viento solo se mantiene en ene–mar.",
                  "Correlación de patrones (centrada y ponderada por área, 40°S–40°N) entre el mapa base y cada variante: "
                  "Spearman, series sin tendencia lineal (por mes), sin los años extremos, IMERG en lugar de P<sub>L</sub>, "
                  "rezago de un mes para el caudal (fijado por el desfase lluvia → caudal, no buscado) y, para P<sub>L</sub>, "
                  "los dos subperiodos del registro largo comparados entre sí.", "37_correlaciones_5.py",
                  png=CO / "fig_robustez_5_3.png", csvs=[CO / "robustez_5_3.csv"])
        + tarjeta("Tamaño de muestra por celda",
                  "Todas las celdas válidas tienen 27 pares; el n efectivo baja donde la SST persiste de un año a otro, lo "
                  "que exige correlaciones más altas para ser significativas.",
                  "Pares válidos y n efectivo = n (1 − ρ<sub>x</sub>ρ<sub>y</sub>)/(1 + ρ<sub>x</sub>ρ<sub>y</sub>) del mapa "
                  "P<sub>L</sub>–SST de marzo.", "37_correlaciones_5.py", png=CO / "fig_muestra_5_3.png"))

# ------------------------------------------------------------------ síntesis de todos los puntos
_ev = leer(MO / "evaluacion_2_3.csv")
_ev = _ev[(_ev.elegido_cv == True) & (_ev.muestra == "todos")].set_index(["particion", "objetivo"])["habilidad_MAE"]
_ar = ari.loc["P_L (CAMELS-PE)"]
R_ANUAL = cl[cl.variable == "R"].groupby("mes")["media"].first().sum()
EN = _enso
filas_s = [
    ("1.1–1.2 Series e IMERG",
     f"P_L {P_ANUAL:.0f} mm/año, R {R_ANUAL:.0f} mm/año; IMERG da {100 * IM['ratio']:.0f} % de P_L "
     f"(sesgo {IM['sesgo']:+.1f} mm/mes) aunque sigue su ritmo (r = {IM['r']:.2f}). 1998 y 2017 dominan los máximos de lluvia "
     "y caudal; en 1998-03 R ≈ 2·P_L.",
     "1.1, 1.2", "Alta para el ritmo; la magnitud de P depende de la fuente (CAMELS-PE > PISCOp > IMERG).",
     "IMERG subestima la lluvia orográfica cálida de los Andes; P_L puede subestimar las cabeceras."),
    ("1.3–1.4 Distribución y calidad",
     "Lluvia y caudal muy asimétricos (pocos meses muy altos); temperatura casi simétrica. Faltantes de caudal 3.2 % de "
     "los días, concentrados en estiaje; ningún dato descartado por ser extremo.",
     "1.3, 1.4", "Alta; el relleno del caudal se validó (error mediano 0.1–4 % en huecos cortos).",
     "Mediana e IQR describen mejor una condición típica que la media."),
    ("1.5 Ciclo anual",
     f"Unimodal: lluvia con máximo en marzo (SI {ip.loc['P_L', 'SI']:.2f}, {ip.loc['P_L', 'pct_en_dic_abr']:.0f} % en "
     f"dic–abr); caudal mar–abr, con el centroide {lag_centroide('P_L'):.1f} meses después de la lluvia; temperatura casi "
     f"isotermal (amplitud {ip.loc['T', 'amplitud']:.1f} °C). Aridez P/PET {_ar.AI_P_PET:.2f} ({_ar.clase_UNEP}).",
     "1.5.a–c", "Alta; estable entre subperiodos. La clase de aridez cambia con la fuente de P (semiárido con IMERG).",
     "Estación húmeda por ascenso sobre los Andes y flujo del este; estación seca por subsidencia e inversión; el caudal se "
     "retrasa y se sostiene en estiaje por almacenamiento."),
    ("Balance hídrico",
     f"R/P = {_ar.R_P_obs:.2f}, frente a {_ar.R_P_Budyko:.2f} esperado por Budyko con la misma PET: sale más agua de la que "
     "admite el balance con cualquier fuente de P.",
     "1.5.c", "El desajuste es grande y robusto frente a la fuente de P.",
     "P subestimada en las cabeceras, PET potencial ≫ ET real, aportes externos o sesgo de la curva de descarga."),
    ("2 Relaciones y modelos",
     f"IMERG–P_L r = {R21['a']:.2f} pero no concordantes. El caudal se asocia mejor con la lluvia del mes "
     f"anterior (ρ {RZ['k0']:.2f} → {RZ['k1']:.2f}) y con la acumulada (ρ {RZ['acu']:.2f}). El modelo logarítmico con "
     f"rezagos mejora la climatología del caudal en {100 * _ev[('A', 'Q̄ ← P_L')]:.0f} % y "
     f"{100 * _ev[('B', 'Q̄ ← P_L')]:.0f} % (dos particiones); con IMERG solo {100 * _ev[('A', 'Q̄ ← P_I')]:.0f}–"
     f"{100 * _ev[('B', 'Q̄ ← P_I')]:.0f} %.",
     "2.1–2.3", "Media: funciona en recesión y estiaje, falla en las crecidas de El Niño (2017).",
     "Memoria de 1–3 meses por almacenamiento en suelo y acuíferos fisurados."),
    ("3 Tendencias",
     f"La temperatura sube {pend3('T_ERA5L')} °C/década (ERA5-Land) y {pend3('T_PISCOt')} (PISCOt). Lluvia y caudal sin "
     "tendencia robusta: el signo cambia con el año inicial por los Niños en los extremos del registro. IMERG baja, pero la "
     "tendencia desaparece si se empieza en 2003.",
     "3.4–3.6", "Alta para T (dos fuentes; con ERA5-Land, los 12 meses tras FDR); baja para P y Q.",
     "Calentamiento regional; las «tendencias» de lluvia y caudal son variabilidad ENSO; la de IMERG sería un cambio del "
     "producto."),
    ("4 Escalas dominantes",
     f"Con el ciclo anual domina el año ({banda('P_L', 'centrada', 'anual 11–13 m'):.0f} % de la varianza de la lluvia). "
     f"En anomalías la lluvia es casi ruido blanco; ningún pico supera el umbral global. Onditas: la banda de 2–7 años de la "
     f"lluvia va con Niño 1+2 (r = {OND.loc['P_L', 'r_comp_2_7a_con_N12']:.2f}) pero solo pesa "
     f"{100 * OND.loc['P_L', 'var_componente_2_7a']:.0f} % y se concentra en 1983–2000.",
     "4.2, onditas", "Alta para el ciclo anual; los periodos interanuales son bandas con pocos ciclos, no periodicidades.",
     "El almacenamiento filtra las variaciones rápidas del caudal; el ENSO costero modula los años extremos."),
    ("5 Clima global",
     f"Caudal de ene–mar con Niño 1+2: r = {idx5('Q', N12, 1):.2f} y {idx5('Q', N12, 3):.2f} (pasan FDR), pero con "
     f"Spearman ρ = {idx5('Q', N12, 1, 'spearman_rho'):.2f} en enero: lo sostienen 1998 y 2017. Lluvia con viento del este "
     f"en 200 hPa sobre los Andes (abr r = {idx5('P_L', UA, 4):.2f}, sep {idx5('P_L', UA, 9):.2f}). Presión: patrón de la "
     "Oscilación del Sur con todos los meses. Mapas con poca área significativa.",
     "5.2–5.4", "Baja fuera de los años extremos; inestable entre 1981–2002 y 2003–2024.",
     "Niño costero: mar cálido frente a la costa debilita la inversión y dispara la convección; flujo del este en altura "
     "favorece la lluvia al inicio y al final de la estación húmeda."),
]
t_sint = pd.DataFrame(filas_s, columns=["Punto", "Resultado principal (datos)", "Figuras", "Solidez",
                                        "Hipótesis física a contrastar"])
pestana("sintesis", "Síntesis", "Síntesis de resultados",
        "Qué muestran los datos en cada punto, qué tan sólido es cada resultado y qué hipótesis física podría explicarlo. "
        "La columna de hipótesis es un borrador para contrastar con bibliografía, no una conclusión.",
        tabla(t_sint, "Resultados por punto")
        + '<div class="tabla-cont"><h3>Clasificación hidroclimática propuesta (borrador para el grupo)</h3><p>Régimen '
          'pluvial tropical andino de vertiente pacífica: <b>unimodal y estacional</b> (lluvia dic–abr con máximo en marzo; '
          'seca may–sep; transición oct–nov), <b>isotermal</b>, <b>subhúmedo seco</b> por P/PET con P<sub>L</sub> '
          '(semiárido con IMERG), con <b>caudal unimodal desfasado 1–1.5 meses</b> y estiaje sostenido por almacenamiento. '
          'La variabilidad entre años la dominan los <b>Niños costeros extremos</b> (1983, 1998, 2017), no una oscilación '
          'regular; la temperatura sube de forma robusta y la lluvia y el caudal no muestran tendencia.</p>'
          '<h3>Lo que falta para el informe</h3><p>Sustentar cada hipótesis con fuentes leídas y verificadas; esquema '
          'conceptual propio (circulación → lluvia → almacenamiento → pérdidas → caudal, con escalas de tiempo); revisar la '
          'hipótesis inicial del punto 1.4; declarar el uso de IA.</p></div>')

pestana("datos", "Datos", "Datos y reproducibilidad",
        "Fuentes usadas y cómo regenerar todos los productos.",
        tabla(fuentes, "Fuentes de datos")
        + '<div class="tabla-cont"><h3>Cómo reproducir</h3><p>Con Python 3 y las dependencias de <code>requirements.txt</code>, '
          'ejecute en <code>Hidrologiat1/Codigos/</code>, en este orden: <code>09 → 06 → 07a → 13 → 14 → 10 → 28 → 26 → 07b → '
          '11 → 12 → 17 → 15 → 16 → 18 → 19 → 20 → 21 → 23 → 24 → 25 → 29 → 27 → 30 → 31 → 32 → 33 → 34a → 34b → 35 → 36</code>. Antes del 06 hay que descargar las dos '
          'teselas de GLO-30 (ver <code>README.md</code>). Las descargas de IMERG y ERA5/ERA5-Land requieren cuentas '
          'personales (NASA Earthdata y Copernicus CDS), cuyas credenciales no se incluyen en el repositorio. El detalle de '
          'cada conjunto de datos está en <a href="DATOS.md">DATOS.md</a>.</p></div>')

# ------------------------------------------------------------------ página
CSS = (WEB / "estilo.css").read_text(encoding="utf-8")
JS = (WEB / "graficas.js").read_text(encoding="utf-8")
nav = "".join(f'<button type="button" role="tab" data-ir="{i}" aria-selected="false">{c}</button>' for i, c, _ in pestanas)
paneles = "".join(p for _, _, p in pestanas)
pa = cl[cl.variable == "P_L"].media.sum()
pi = cl[cl.variable == "P_I"].media.sum()

pagina = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cuenca El Tambo</title>
<meta name="description" content="Clasificación hidroclimática mensual de la cuenca del río Chicama hasta El Tambo (Perú).">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Clasificación hidroclimática de la cuenca del río Chicama hasta El Tambo</h1>
  <p class="sub">Tarea 1 · Hidrología 2026-2S · Universidad Nacional de Colombia, sede Medellín</p>
  <div class="datos-clave">
    <div class="dato">Estación<b>El Tambo · PE_47E0A2A8</b></div>
    <div class="dato">Área<b>2 170 km²</b></div>
    <div class="dato">Periodo común<b>{PER} ({N_MESES} meses)</b></div>
    <div class="dato">P<sub>L</sub> media anual<b>{pa:.0f} mm/año</b></div>
    <div class="dato">P<sub>I</sub> media anual<b>{pi:.0f} mm/año</b></div>
    <div class="dato">Régimen (propuesto)<b>{ip.loc['P_L', 'regimen']}, máximo en marzo</b></div>
  </div>
</div></header>
<nav aria-label="Puntos de la tarea"><div class="wrap">
  <div class="tabs" role="tablist">{nav}</div>
  <button class="tema" type="button" aria-label="Cambiar tema claro u oscuro">◐ Tema</button>
</div></nav>
<main><div class="wrap">{paneles}</div></main>
<footer><div class="wrap">
Página generada el {date.today():%Y-%m-%d} con <code>Hidrologiat1/Codigos/36_pagina_web.py</code> a partir de los archivos
de resultados. Las gráficas marcadas «interactiva» se dibujan con Plotly desde los CSV; las marcadas «imagen» son las figuras
PNG de los scripts (clic para ampliar). Las descripciones distinguen lo que muestran los datos de las hipótesis, que el grupo
debe sustentar con bibliografía.
</div></footer>
<div id="visor" role="dialog" aria-modal="true" aria-label="Figura ampliada">
  <button type="button" class="cerrar" aria-label="Cerrar">✕</button>
  <a class="full" target="_blank" rel="noopener">Abrir en resolución completa ↗</a>
  <img alt="">
</div>
<script src="{PLOTLY}"></script>
<script src="web/datos.js"></script>
<script>{JS}</script>
</body>
</html>"""

SALIDA = PROY / "index.html"
SALIDA.write_text(pagina, encoding="utf-8")
print(f"Página: {SALIDA} ({SALIDA.stat().st_size / 2**10:.0f} kB), {len(pestanas)} pestañas, "
      f"{pagina.count('data-plot=')} gráficas interactivas, {pagina.count('class=\"zoom\"')} imágenes; "
      f"web/img {sum(f.stat().st_size for f in IMG.glob('*.png')) / 2**20:.1f} MB")
