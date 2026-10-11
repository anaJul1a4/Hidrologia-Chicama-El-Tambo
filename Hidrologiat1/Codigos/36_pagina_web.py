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


def pestana(id_, corto, titulo, intro, cuerpo):
    pestanas.append((id_, corto, f'<section class="panel" id="tab-{id_}" data-tab="{id_}" hidden>'
                                 f'<h2>{titulo}</h2><p class="intro">{intro}</p>{cuerpo}</section>'))


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
                f"El caudal y la escorrentía tienen sus faltantes rellenados: los marcadores indican el método "
                f"({RL['interp']} meses con días interpolados, {RL['esc']} escalados y {RL['mod']} reconstruido con modelo, "
                f"{RL['mes_mod']}), y el fondo naranja los {RL['excl']} meses que sin relleno quedaban excluidos. Desde 2021 "
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
                  f"{val['evaluacion']}. Las dos fuentes no se unen en una sola serie.",
                  "ERA5-Land T2m mensual (0.1°) descargado del CDS y promediado sobre la cuenca ponderando por área (30 celdas). "
                  "El sesgo de cada mes calendario frente a PISCOt se calculó en 1998–2010 y se evaluó fuera de muestra en "
                  "2011–2020; con él se estima T desde 2021: T<sub>est</sub> = ERA5-Land + sesgo del mes. Solo unos 0.5 °C del "
                  "desfase se explican por la altitud del relieve del modelo.",
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
    <div><h4>Qué muestra</h4><p>Arriba, la fracción de días con dato de cada mes (año × mes), antes de cualquier relleno: los
    meses claros tienen faltantes. Abajo, la serie diaria del mismo periodo con los vacíos sin rellenar; en el caudal, los días
    interpolados se marcan en naranja. A la derecha, lo que se comprobó y se decidió con esa variable, para leerlo junto a la
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
        qc_html
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
                  "a la malla del DEM y con una escala discreta común de naranja (seco) a azul (húmedo). El recuadro de cada "
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

PENDIENTES = [
    ("p2", "2 Relaciones", "Punto 2 · Relaciones entre series y modelos estadísticos",
     "Diagramas de dispersión entre P<sub>L</sub>, P<sub>I</sub> y caudal, y modelos para estimar la lluvia local desde "
     "IMERG y el caudal desde la lluvia."),
    ("p3", "3 Tendencias", "Punto 3 · Tendencias hidroclimáticas y sus posibles causas",
     "Tendencias de P<sub>L</sub>, P<sub>I</sub>, caudal y temperatura con métodos lineales y no lineales, paramétricos y no "
     "paramétricos. El tramo de temperatura estimado con ERA5-Land debe tratarse aparte."),
    ("p4", "4 Fourier", "Punto 4 · Análisis de frecuencias mediante Fourier",
     "Espectros de las series mensuales originales y de sus anomalías para identificar los periodos dominantes."),
    ("p5", "5 Clima global", "Punto 5 · Mapas de correlación con el clima global",
     "Regiones oceánicas y patrones atmosféricos asociados con la variabilidad mensual de la lluvia y el caudal."),
]
for id_, corto, titulo, txt in PENDIENTES:
    pestana(id_, corto, titulo, txt, '<div class="pendiente">En construcción: los resultados se agregarán aquí.</div>')

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
