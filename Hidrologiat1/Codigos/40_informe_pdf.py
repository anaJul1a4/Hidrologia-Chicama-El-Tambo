"""
Informe final en PDF (Tarea 1). Reúne el texto, las figuras de resultados/ y las tablas leídas de los CSV.
Requiere reportlab. Fuente DejaVu Sans (incluida en matplotlib) para los símbolos griegos y matemáticos.

Salida: Informe_Tarea1_Chicama_El_Tambo.pdf (raíz del proyecto)
"""
from pathlib import Path

import matplotlib
import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak,
                                KeepTogether, CondPageBreak)

PROY = Path(__file__).resolve().parents[2]
R = PROY / "Tarea 1" / "El_Tambo" / "resultados"
SALIDA = PROY / "Informe_Tarea1_Chicama_El_Tambo.pdf"

TTF = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
for nombre, archivo in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                        ("DV-BI", "DejaVuSans-BoldOblique.ttf")):
    pdfmetrics.registerFont(TTFont(nombre, str(TTF / archivo)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

AZUL = colors.HexColor("#184f95")
GRIS = colors.HexColor("#52514e")
st = {
    "titulo": ParagraphStyle("titulo", fontName="DV-B", fontSize=17, leading=22, alignment=TA_CENTER, spaceAfter=6),
    "subtitulo": ParagraphStyle("sub", fontName="DV", fontSize=11, leading=15, alignment=TA_CENTER, textColor=GRIS),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=13.5, leading=18, spaceBefore=14, spaceAfter=6, textColor=AZUL, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=11, leading=15, spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9.4, leading=13.6, alignment=TA_JUSTIFY, spaceAfter=6),
    "bul": ParagraphStyle("bul", fontName="DV", fontSize=9.4, leading=13.4, alignment=TA_JUSTIFY, leftIndent=14,
                          bulletIndent=4, spaceAfter=3),
    "cap": ParagraphStyle("cap", fontName="DV", fontSize=8.2, leading=11, textColor=GRIS, alignment=TA_JUSTIFY,
                          spaceBefore=3, spaceAfter=10),
    "celda": ParagraphStyle("celda", fontName="DV", fontSize=7.8, leading=10),
    "celdab": ParagraphStyle("celdab", fontName="DV-B", fontSize=7.8, leading=10),
    "ref": ParagraphStyle("ref", fontName="DV", fontSize=8.3, leading=11.2, leftIndent=14, firstLineIndent=-14,
                          spaceAfter=3),
    "aviso": ParagraphStyle("aviso", fontName="DV-I", fontSize=8.6, leading=12, textColor=GRIS, alignment=TA_JUSTIFY,
                            borderColor=GRIS, borderWidth=0.5, borderPadding=6, spaceBefore=6, spaceAfter=10),
}
ANCHO = letter[0] - 4 * cm
story = []


def P(t, s="p"):
    story.append(Paragraph(t, st[s]))


def B(t):
    story.append(Paragraph(t, st["bul"], bulletText="•"))


def H1(t):
    story.append(Paragraph(t, st["h1"]))


def H2(t):
    story.append(CondPageBreak(7 * cm))                      # no dejar un subtítulo solo al pie de página
    story.append(Paragraph(t, st["h2"]))


N_FIG = [0]


def FIG(ruta, leyenda, ancho=1.0, alto_max=17 * cm):
    N_FIG[0] += 1
    w, h = PILImage.open(ruta).size
    W = ANCHO * ancho
    H = W * h / w
    if H > alto_max:
        H, W = alto_max, alto_max * w / h
    story.append(KeepTogether([Image(str(ruta), width=W, height=H),
                               Paragraph(f"<b>Figura {N_FIG[0]}.</b> {leyenda}", st["cap"])]))


N_TAB = [0]


def TAB(filas, leyenda, anchos, cabecera=True):
    N_TAB[0] += 1
    datos = [[Paragraph(str(c), st["celdab" if (i == 0 and cabecera) else "celda"]) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=[a * ANCHO for a in anchos], repeatRows=1 if cabecera else 0)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f3ef")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    story.append(Paragraph(f"<b>Tabla {N_TAB[0]}.</b> {leyenda}", st["cap"]))
    story.append(t)
    story.append(Spacer(1, 8))


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, "Hidrología 2026-2 · Tarea 1 · Río Chicama hasta El Tambo")
    canvas.drawRightString(letter[0] - 2 * cm, 1.2 * cm, f"{doc.page}")
    canvas.restoreState()


# ====================================================================== portada
story += [Spacer(1, 2.2 * cm),
          Paragraph("Clasificación hidroclimática mensual de la cuenca del río Chicama hasta la estación El Tambo", st["titulo"]),
          Spacer(1, 4),
          Paragraph("¿Por qué hay una estación seca de cinco meses si la cuenca está en el trópico, al alcance de la "
                    "Zona de Convergencia Intertropical?", st["subtitulo"]),
          Spacer(1, 1.2 * cm),
          Paragraph("Hidrología · Semestre 2026-2 · Universidad Nacional de Colombia, Sede Medellín<br/>"
                    "Profesor: Carlos David Hoyos", st["subtitulo"]),
          Spacer(1, 0.6 * cm),
          Paragraph("Integrantes: Juan [apellido por completar] · Marlin Julie Schwebel · [tercer integrante por completar]",
                    st["subtitulo"]),
          Spacer(1, 1.2 * cm),
          Paragraph("Cuenca: río Chicama hasta la estación hidrométrica El Tambo (SENAMHI 211003; CAMELS-PE PE_47E0A2A8), "
                    "7.574° S, 78.707° O, 684 m s.n.m., La Libertad, Perú · Área de drenaje 2 170 km² (delimitación propia "
                    "con GLO-30; 2 171.6 km² en CAMELS-PE) · Periodo común de análisis: enero de 1998 a diciembre de 2024 "
                    "(324 meses, 27 años completos)", st["subtitulo"]),
          Spacer(1, 1.0 * cm),
          Paragraph("Código, datos y página de resultados: https://github.com/anaJul1a4/Hidrologia-Chicama-El-Tambo · "
                    "https://anajul1a4.github.io/Hidrologia-Chicama-El-Tambo/", st["subtitulo"]),
          PageBreak()]

# ====================================================================== 1. Introducción
H1("1. Introducción")
P("El río Chicama nace en la Cordillera Occidental del norte del Perú y desemboca en el Pacífico al norte de Trujillo. "
  "Hasta la estación El Tambo drena 2 170 km² de vertiente andina entre 678 y 4 308 m s.n.m. (mediana 2 578 m, "
  "pendiente media 27°; Figura 1). La cuenca no incluye la franja costera desértica: el 97 % de su área está por "
  "encima de 1 000 m. No tiene glaciares ni nieve permanente (cota máxima 4 308 m), de modo que el caudal depende "
  "solo de la lluvia y del agua almacenada en suelos y rocas.")
P("La cuenca está a 7.6° S, dentro de la franja tropical en la que, en los libros de texto, la lluvia sigue a la "
  "Zona de Convergencia Intertropical (ZCIT). Sin embargo, el registro muestra una estación seca casi absoluta de mayo a "
  "septiembre (P ≈ 3 mm/mes en julio–agosto) y años muy secos entre años muy húmedos. Este contraste motiva la "
  "pregunta guía del trabajo: <b>¿por qué hay sequía —estacional y entre años— si la cuenca está en la zona de influencia "
  "de la ZCIT?</b>")
P("<b>Hipótesis inicial (H0).</b> La lluvia de la cuenca la controla el paso estacional de la ZCIT: llueve cuando la "
  "ZCIT se desplaza hacia el sur (verano austral) y hay sequía cuando se retira al norte. Los años secos serían años en "
  "que la ZCIT no alcanza la latitud de la cuenca.")
P("<b>Hipótesis alternativa (H1).</b> Sobre el Pacífico oriental la ZCIT permanece al norte del ecuador durante todo el "
  "año, porque el agua fría de la lengua ecuatorial y de la corriente costera inhibe la convección al sur (Mitchell y "
  "Wallace, 1992; Xie y Philander, 1994). La lluvia de la cuenca llegaría entonces desde el este, con la convección de "
  "verano sobre los Andes asociada al sistema monzónico sudamericano (Vera et al., 2006; Garreaud et al., 2009), y la "
  "estación seca se debería a la subsidencia del anticiclón del Pacífico sur y a la inversión térmica asociada (Klein y "
  "Hartmann, 1993; Garreaud, 2009). La variabilidad entre años la modularía el calentamiento del mar frente a la costa "
  "(Niño costero), que debilita la inversión (Takahashi et al., 2011; Garreaud, 2018).")
P("<b>Objetivos.</b> (1) Construir y validar las series mensuales de precipitación, caudal y temperatura y compararlas "
  "con IMERG; (2) caracterizar el ciclo anual y proponer una clasificación hidroclimática con criterios explícitos; "
  "(3) cuantificar la relación lluvia–caudal; (4) evaluar tendencias; (5) identificar las escalas dominantes de "
  "variabilidad; (6) relacionar la cuenca con el clima global, y con todo ello contrastar H0 y H1.")
FIG(R / "delimitacion" / "mapa_cuenca_el_tambo.png",
    "Cuenca del río Chicama hasta El Tambo delimitada con el DEM Copernicus GLO-30 (D8): relieve, red de drenaje "
    "(Strahler, umbral 5 km²), río principal, punto de cierre y estaciones de SENAMHI. La delimitación coincide con el "
    "polígono de CAMELS-PE (IoU 0.994). Script 06.", alto_max=13 * cm)
P("El contexto físico de la Figura 2 resume los rasgos que pueden explicar los resultados. La cobertura es sobre todo "
  "pastizal y pajonal (55 %), arbustal (23 %) y bosque (17 %); la agricultura ocupa 2.4 %. En la geología predominan las "
  "areniscas cuarzosas fisuradas de las formaciones Chimú y Farrat (40 %), que pueden almacenar y liberar agua lentamente, "
  "y las secuencias de lutitas que actúan como acuitardo (37 %); los depósitos cuaternarios porosos ocupan solo 2.5 %. Las "
  "laderas se reparten en todas las orientaciones (10–14 % cada una), así que la orientación respecto al flujo del este "
  "no favorece una vertiente en particular. La lluvia media de CHIRPS aumenta desde el cierre (≈ 400 mm/año) hacia las "
  "cabeceras del sureste (≈ 900 mm/año).")
FIG(R / "contexto_fisico" / "panel_contexto_fisico.png",
    "Contexto físico: (a) orientación de laderas (GLO-30), (b) cobertura ESA WorldCover 2021, (c) unidades "
    "hidrogeológicas agrupadas a partir de la geología 1:100 000 de INGEMMET (agrupación propia, por contrastar con la "
    "cartografía hidrogeológica oficial) y (d) precipitación media anual de CHIRPS v2.0 en el periodo común. Script 07b.")

# ====================================================================== 2. Metodología
H1("2. Metodología")
H2("2.1 Datos")
TAB([["Variable", "Fuente", "Resolución y periodo", "Uso"],
     ["P<sub>L</sub> (lluvia de referencia)", "CAMELS-PE v1.0.1, campo prec (PISCOp v2.1; Aybar et al., 2020)",
      "Diaria, promedio de cuenca, 1981–2025; 0 % faltantes", "Serie principal de lluvia"],
     ["Q y R (caudal y lámina)", "CAMELS-PE v1.0.1, campo flow_obs (SENAMHI, El Tambo)",
      "Diaria, mm/d; 3.2 % de días faltantes en 1998–2024", "Respuesta de la cuenca"],
     ["T (temperatura)", "CAMELS-PE (PISCOt v1.2) y ERA5-Land (Muñoz-Sabater et al., 2021)",
      "PISCOt 1981–2020; ERA5-Land mensual 0.1°, 1981–2025", "Ciclo, tendencias, PET"],
     ["P<sub>I</sub> (satélite)", "GPM IMERG V07 Final mensual (doi:10.5067/GPM/IMERG/3B-MONTH/07)",
      "0.1°, 1998-01 a 2025-08; 31 celdas en la cuenca", "Comparación con P<sub>L</sub>"],
     ["Apoyo de lluvia", "CHIRPS v2.0 (Funk et al., 2015); PISCOp v3.0", "0.05° y 0.1°", "Patrón espacial, sensibilidad"],
     ["Circulación", "ERA5 mensual (Hersbach et al., 2020): IVT, viento, ω, T por niveles; radiosondeos de Trujillo",
      "0.25–2°, 1998–2025", "Mecanismos (H0 y H1)"],
     ["Clima global", "ERSST v5 (Huang et al., 2017); ERA5 presión al nivel del mar y u en 200 hPa; Niño 1+2 y 3.4 (CPC)",
      "2°, 1981–2025", "Punto 5"]],
    "Fuentes de datos. P<sub>L</sub> no es una observación independiente de IMERG: PISCOp combina pluviómetros con "
    "CHIRPS e IMERG Final incorpora pluviómetros (GPCC).", [0.17, 0.35, 0.28, 0.20])
H2("2.2 Control de calidad, agregación y relleno")
P("Las series diarias se revisaron por fechas, duplicados, códigos de faltante, negativos, secuencias constantes, tramos "
  "lineales y picos aislados (17 entradas en el registro de anomalías, script 19). La agregación mensual es "
  "P<sub>L,m</sub> = ΣP<sub>d</sub>, Q<sub>m</sub> (en el texto, Q: caudal medio mensual) = media de Q<sub>d</sub>, R<sub>m</sub> = Σq<sub>d</sub> (q ya está "
  "en mm/d) y T<sub>m</sub> = media de T<sub>d</sub>; Q en m³/s = q·A/86.4. Se comprobó a mano la agregación de 2010-03 "
  "(P 165.6 mm, R 49.3 mm, Q 39.97 m³/s). Los faltantes de caudal (3.2 % de los días antes de cualquier relleno, por "
  "debajo del 10 % admitido) se concentran en el estiaje (Figura 5). Se rellenaron en tres pasos: interpolación de "
  "ln q en huecos de hasta 15 días (error mediano del total mensual 0.1–4 % con huecos sintéticos), escalado de la media "
  "en meses con al menos 50 % de días y un modelo mensual en un solo mes (1998-08). La temperatura posterior a 2020 se "
  "estimó con ERA5-Land corregido por el sesgo de cada mes (MAE 0.19 °C fuera de muestra) y se mantiene separada de "
  "PISCOt. IMERG se promedió ponderando cada celda por su área dentro de la cuenca (≈ 18 celdas equivalentes).")
H2("2.3 Procedimientos de los cinco puntos")
B("<b>Puntos 1.1–1.5:</b> series alineadas, estadísticos y distribuciones, climatología de 12 meses con cuartiles y "
  "percentiles 10–90, índices de estacionalidad (SI de Walsh y Lawler, 1981; PCI de Oliver, 1980), aridez P/PET y "
  "Köppen–Geiger (Peel et al., 2007).")
B("<b>Punto 2:</b> Pearson y Spearman en series y anomalías, rezagos de 0–6 meses, y modelos P<sub>L</sub> ← IMERG y "
  "Q ← lluvia elegidos por validación cruzada dentro del ajuste y evaluados en bloques de años no usados (2016–2024 y "
  "1998–2006) frente a referencias sencillas.")
B("<b>Punto 3:</b> anomalías respecto a 1998–2020; OLS con errores HAC y Mann–Kendall de Hamed y Rao (1998) con "
  "pendiente de Sen (1968), por mes y para todos los meses; control FDR (Benjamini y Hochberg, 1995); sensibilidad a "
  "ventanas, extremos y fuente.")
B("<b>Punto 4:</b> periodograma (FFT), Hann y Welch con fondo de ruido rojo AR(1) y umbrales del 95 % puntual y "
  "global; onditas de Morlet (Torrence y Compo, 1998) con corrección de sesgo (Liu et al., 2007).")
B("<b>Punto 5:</b> correlación entre años, para cada mes calendario (27 años), entre la cuenca y cada celda de SST, "
  "presión al nivel del mar y viento zonal en 200 hPa; n efectivo por persistencia (Bretherton et al., 1999) y FDR por "
  "mapa con α = 0.10 (Wilks, 2016); robustez con Spearman, sin tendencia, sin 1998/2017/2023, con IMERG y entre "
  "subperiodos.")
P("Todas las figuras se generan con los scripts numerados del repositorio (Python 3, dependencias en requirements.txt); "
  "cada leyenda indica el script.")

# ====================================================================== 3. Resultados y discusión
H1("3. Resultados y discusión")
H2("3.1 Series mensuales, IMERG y control de calidad (punto 1.1–1.4)")
FIG(R / "series_mensuales" / "fig_series_mensuales_1_1.png",
    "Series mensuales 1998–2024: P<sub>L</sub>, Q, R y T en paneles alineados. P<sub>L</sub> y R comparten escala "
    "(mm/mes). Sombreado rojo: meses de caudal que sin relleno quedaban excluidos; sombreado gris en T: estimación con "
    "ERA5-Land desde 2021. Script 15.", alto_max=15 * cm)
P("<b>Resultado.</b> La lluvia y el caudal tienen un ciclo anual muy marcado y dos eventos extremos: marzo de 1998 "
  "(P<sub>L</sub> 414 mm, Q 691 m³/s, R 852 mm) y marzo–abril de 2017 (Q 450 m³/s) (Figura 3). Los mínimos de caudal "
  "llegan a 0.36 m³/s (septiembre de 2005). En 100 de los 324 meses R supera a P<sub>L</sub>, casi siempre en mayo–agosto "
  "y en las crecidas de 1998.")
P("<b>Interpretación.</b> R > P en la estación seca no es un error por sí mismo: indica que el río drena agua almacenada "
  "durante la estación húmeda, coherente con los acuíferos fisurados de la Figura 2. En marzo de 1998, en cambio, R ≈ "
  "2·P<sub>L</sub> en un solo mes no puede explicarse solo por almacenamiento; son plausibles una P<sub>L</sub> "
  "subestimada en el evento (pocas estaciones en las cabeceras) o un error de la curva de descarga en crecida. No tenemos "
  "datos para distinguir estas dos explicaciones.")
FIG(R / "series_mensuales" / "fig_P_L_vs_IMERG_mensual.png",
    "Lluvia de referencia P<sub>L</sub> frente a IMERG V07 en el periodo común. Script 10.", alto_max=9 * cm)
P("IMERG sigue el ritmo de P<sub>L</sub> (r = 0.90) pero da solo 65 % del total (539 frente a 833 mm/año; sesgo "
  "−24.5 mm/mes): subestima 42 % en dic–feb y 39 % en mar–may y sobrestima los meses casi secos (Figura 4). Una "
  "explicación propuesta en la literatura de los Andes es que los sensores de microondas detectan mal la lluvia "
  "orográfica de nubes cálidas y poco profundas; no la verificamos con datos propios. La lluvia de referencia tampoco "
  "es segura: las versiones públicas de PISCOp dan 15–25 % menos que CAMELS-PE, una diferencia que no pudimos "
  "reproducir y que reportamos como incertidumbre.")
FIG(R / "control_calidad" / "fig_disponibilidad_1_4.png",
    "Disponibilidad diaria por año y mes (antes del relleno) de cada variable. Script 19.", alto_max=11 * cm)
P("<b>Hipótesis inicial, revisada con 1.4.</b> La primera lectura de las series (H0) atribuía todo a la ZCIT. El control de "
  "calidad añade dos cautelas: los faltantes de caudal son sistemáticos en estiaje y en 2019–2021, y los dos eventos que "
  "dominan la varianza (1998, 2017) son también los más inciertos. Por eso las conclusiones que siguen se comprueban "
  "sin los meses rellenados y sin esos años.")

H2("3.2 Distribución y ciclo anual (puntos 1.3 y 1.5)")
est = pd.read_csv(R / "series_mensuales" / "estadisticos_1_3_periodo_comun.csv").set_index("variable")
fil = [["Variable", "n", "Media", "Mediana", "Desv. est.", "P10–P90", "Mín.–máx.", "Asimetría"]]
for v, nom in (("P_L", "P<sub>L</sub> (mm/mes)"), ("P_I", "P<sub>I</sub> (mm/mes)"), ("Q", "Q (m³/s)"),
               ("R", "R (mm/mes)"), ("T", "T (°C)")):
    if v in est.index:
        e = est.loc[v]
        f = 2 if v == "T" else 1
        fil.append([nom, int(e.n_meses_validos), f"{e.media:.{f}f}", f"{e.mediana:.{f}f}", f"{e.desv_est:.{f}f}",
                    f"{e.P10:.{f}f}–{e.P90:.{f}f}", f"{e.minimo:.{f}f}–{e.maximo:.{f}f}", f"{e.asimetria_G1:.2f}"])
TAB(fil, "Estadísticos mensuales del periodo común 1998–2024 (script 18). T: solo PISCOt (hasta 2020).",
    [0.18, 0.07, 0.10, 0.11, 0.11, 0.16, 0.16, 0.11])
P("La lluvia y el caudal son muy asimétricos (Tabla 2): la media de P<sub>L</sub> (69 mm/mes) supera a la mediana "
  "(47 mm/mes) y el caudal tiene asimetría cercana a 7.5 por las crecidas de El Niño. Para describir un mes típico se usan "
  "mediana e intercuartil; la temperatura es casi simétrica.")
FIG(R / "climatologia" / "fig_climatologia_1_5a.png",
    "Climatología de 12 meses en el periodo común: media, mediana, rango intercuartílico y percentiles 10–90 entre años. "
    "Las bandas son dispersión entre años, no intervalos de confianza. Script 20.", alto_max=13 * cm)
P("<b>Resultado.</b> El régimen es unimodal (Figura 6): P<sub>L</sub> tiene su máximo en marzo (213 mm) y su mínimo en "
  "agosto (3 mm); 81 % de la lluvia cae de diciembre a abril (SI = 0.78, estacional en el límite con «marcadamente "
  "estacional»). El caudal alcanza su máximo en marzo–abril y el mínimo en septiembre–octubre; su centroide va 1.3 meses "
  "detrás del de la lluvia, y es más concentrado que la lluvia (SI de R 0.89). La temperatura casi no varía en el año "
  "(amplitud 0.6 °C, máximo en septiembre y mínimo en junio). El máximo de lluvia cae en febrero–abril en 93 % de los "
  "años, y la forma del ciclo es la misma en 1998–2011 y en 2012–2024.")
FIG(R / "climatologia" / "fig_sintesis_ciclo_1_5c.png",
    "Síntesis del ciclo anual: P<sub>L</sub>, IMERG, R y PET de Penman–Monteith por mes, y clasificación de cada mes "
    "(FAO P/PET, meses secos de Gaussen, aguas altas, R > P y mes del pico por año). Script 23.", alto_max=12 * cm)
P("<b>Mecanismo y contraste de hipótesis.</b> Si la lluvia dependiera del paso de la ZCIT (H0), cabría esperar dos máximos "
  "o al menos una estación de lluvias desplazada hacia el equinoccio en cada paso. El ciclo observado es un solo máximo "
  "en marzo, con lluvia que empieza en octubre–noviembre, culmina al final del verano austral y desaparece en mayo. Ese "
  "calendario coincide con el de la convección de verano sobre los Andes y con la convergencia de humedad que calculamos "
  "con ERA5 sobre la cuenca (Figura 8): la convergencia del transporte de humedad es de +4.1 mm/d en marzo y de −2.1 mm/d "
  "en junio, y el movimiento vertical en 500 hPa pasa de ascenso (−0.087 Pa/s en marzo) a descenso (+0.039 Pa/s en "
  "agosto). La humedad llega del este en ambas estaciones (dirección del transporte ≈ 270°); en la estación seca el "
  "transporte es incluso mayor (50 frente a 33 kg m⁻¹ s⁻¹), pero el aire diverge y desciende. <b>La sequía estacional "
  "no se debe a falta de humedad disponible sino a falta de ascenso.</b>")
FIG(R / "inversion" / "fig_temporadas_humedad_inversion.png",
    "Transporte de humedad integrado (IVT, ERA5) y perfiles de temperatura de los radiosondeos de Trujillo en la estación "
    "seca y en la húmeda: la inversión es casi permanente de mayo a diciembre y su tope queda bajo la cuenca. Scripts 24 "
    "y 35.", alto_max=14 * cm)
P("La inversión térmica costera es casi permanente de mayo a diciembre (94–100 % de los sondeos de Trujillo) y su "
  "estabilidad (LTS) es máxima en septiembre (24.2 K) y mínima en febrero (17.0 K). Sin embargo, su tope está a 1.0–1.3 km "
  "en la estación seca, por debajo de casi toda la cuenca. Por eso la inversión explica la ausencia de lluvia en la costa, "
  "pero sobre la cuenca lo que pesa es la subsidencia de gran escala del anticiclón del Pacífico sur, de la que la "
  "inversión es la manifestación en niveles bajos (Klein y Hartmann, 1993; Garreaud, 2009). En las anomalías de "
  "dic–abr, la lluvia se correlaciona con el ascenso (r = −0.78 con ω500) y con la convergencia de humedad (r = 0.82) "
  "más que con la inversión (r = −0.47 con la LTS). Como ω, la convergencia y la lluvia de ERA5 vienen del mismo "
  "reanálisis, estas correlaciones muestran coherencia física, no causalidad.")
P("Sobre el máximo de temperatura en septiembre proponemos una explicación por comprobar: es el final de la estación "
  "seca, con cielos despejados y suelos secos que favorecen el calentamiento antes de que lleguen las nubes y la "
  "evaporación de la estación húmeda. Una explicación alternativa sería el efecto de la temperatura del mar en la parte "
  "baja de la cuenca; no la evaluamos.")
P("<b>Clasificación hidroclimática.</b> Con los criterios de la Figura 7: régimen pluvial tropical andino de vertiente "
  "pacífica, <b>unimodal y estacional</b> (estación húmeda dic–abr, seca may–sep, transición oct–nov), <b>isotermal</b>, "
  "<b>subhúmedo seco</b> según P/PET = 0.62 (Köppen Cwb), con caudal unimodal desfasado 1–1.5 meses y estiaje sostenido "
  "por almacenamiento. La clase depende de la fuente de lluvia: con IMERG sería semiárida (P/PET 0.42, Köppen BSk). El "
  "balance de largo plazo no cierra: R/P observado es 0.48, frente a 0.16 esperado por la curva de Budyko con la misma "
  "PET. Explicaciones posibles: lluvia subestimada en las cabeceras, PET potencial muy superior a la evapotranspiración "
  "real, aportes de fuera de la divisoria o sesgo de la curva de descarga. No podemos discriminarlas con los datos "
  "disponibles.")

H2("3.3 Relaciones lluvia–caudal y modelos (punto 2)")
FIG(R / "relaciones" / "fig_dispersion_2_1.png",
    "Dispersión mensual por estación de la cuenca: (a) IMERG frente a P<sub>L</sub> con línea 1:1; (b) y (c) caudal "
    "frente a la lluvia (eje logarítmico, mismos ejes); (b′) lámina R frente a P<sub>L</sub>. Script 30.", alto_max=15 * cm)
P("<b>Resultado.</b> La correlación alta entre IMERG y P<sub>L</sub> (r = 0.90) no implica concordancia: la nube cae bajo "
  "la línea 1:1 (Figura 9a). El caudal se relaciona débilmente con la lluvia del mismo mes (ρ = 0.52), pero mucho mejor con "
  "la del mes anterior (ρ = 0.81) y con la acumulada de cuatro meses (ρ = 0.91; Figura 10). En anomalías la relación "
  "persiste (ρ = 0.61 con un mes de rezago), así que no se debe solo al ciclo anual compartido. Los meses secos (triángulos "
  "ocres) tienen caudal alto con lluvia casi nula: es el flujo base.")
FIG(R / "relaciones" / "fig_rezagos_2_1.png",
    "Correlación de Spearman entre el caudal del mes t y la lluvia del mes t−k o acumulada de t−k a t, en series y en "
    "anomalías. Script 30.", alto_max=7 * cm)
P("<b>Modelos.</b> El modelo logarítmico de caudal con rezagos de la lluvia y efecto de mes mejora la climatología del "
  "caudal en 41 % (evaluación 2016–2024) y 26 % (1998–2006); con IMERG la mejora es de solo 8–12 %. Para la lluvia, un "
  "factor por mes calendario corrige IMERG y mejora en 37–40 % frente a IMERG sin corregir. El modelo funciona en recesión "
  "y estiaje, pero subestima mucho la crecida de 2017 (−310 m³/s en abril; Figura 11).")
FIG(R / "modelos" / "fig_modelo_Q_2_3.png",
    "Modelo de caudal a partir de P<sub>L</sub>: observado frente a estimado fuera del periodo de ajuste y residuos en "
    "el tiempo, frente al valor estimado y por mes. Script 31.", alto_max=12 * cm)
P("<b>Mecanismo.</b> La memoria de 1–3 meses y la no linealidad (escala logarítmica) indican que la cuenca primero "
  "rellena el almacenamiento de suelos y rocas fisuradas y después responde, y que en estiaje drena ese almacenamiento. "
  "La falla en 2017 sugiere que en los Niños costeros opera otro mecanismo —lluvia intensa sobre suelos ya saturados, "
  "escorrentía rápida— que la relación mensual promedio no representa.")

H2("3.4 Tendencias (punto 3)")
FIG(R / "tendencias" / "fig_series_tendencias_3_4.png",
    "Series originales, anomalías y anomalías estandarizadas con las tendencias de Sen. Script 32.", alto_max=13 * cm)
P("<b>Resultado.</b> La temperatura aumenta de forma robusta: +0.23 °C por década con ERA5-Land (1981–2025, IC 95 % "
  "0.21–0.26) y +0.18 °C por década con PISCOt (1981–2020, 0.11–0.25); la tendencia de ERA5-Land es significativa en los "
  "12 meses tras el control FDR y persiste al retirar los años de El Niño. La lluvia y el caudal no tienen tendencia "
  "robusta: P<sub>L</sub> +1.2 mm/mes por década (p = 0.12) y Q −0.6 m³/s por década (p = 0.53). IMERG baja −3.0 mm/mes "
  "por década, pero la tendencia desaparece si se empieza en 2003. El signo de las tendencias de lluvia y caudal cambia "
  "con el año inicial y final (Figura 13), porque los Niños de 1983, 1998, 2017 y 2023 caen cerca de los extremos.")
FIG(R / "tendencias" / "fig_ventanas_inicio_fin_3_5.png",
    "Pendiente de Sen de las anomalías anuales para todas las combinaciones de año inicial y final (ventanas ≥ 15 años). "
    "Escala de color común para las dos lluvias y para las dos temperaturas; puntos: p < 0.05 sin corregir. Script 32.",
    alto_max=6 * cm)
P("<b>Interpretación.</b> El calentamiento coincide en dos fuentes construidas de forma distinta y es coherente con el "
  "calentamiento regional; queda como explicación alternativa un cambio en las observaciones que asimilan los productos. "
  "Las «tendencias» de lluvia y caudal son, más simplemente, variabilidad ENSO mal muestreada por la longitud del registro. "
  "La tendencia de IMERG sin equivalente en P<sub>L</sub> ni en el caudal apunta a un cambio del producto, no del clima.")

H2("3.5 Escalas dominantes: Fourier y onditas (punto 4)")
FIG(R / "espectros" / "fig_espectros_porcentaje_4_2.png",
    "Periodograma en % de la varianza total por periodo (registro completo), series con ciclo anual (izquierda) y "
    "anomalías (derecha). Línea discontinua: 95 % puntual frente a un ruido rojo AR(1). Script 33.", alto_max=17 * cm)
P("<b>Resultado.</b> Con el ciclo anual, el periodo de un año reúne 52 % de la varianza de la lluvia y 28 % de la del "
  "caudal, más un armónico de seis meses por la estación húmeda concentrada (Figura 14). Sin el ciclo anual, la lluvia es "
  "casi ruido blanco (autocorrelación de un mes 0.32) y el caudal algo más persistente (0.51); los picos interanuales de "
  "2, 5 y 9 años reúnen 2–5 % de la varianza cada uno y ninguno supera el umbral global. La temperatura sí muestra un "
  "pico de unos 3.7 años con 10–14 % de la varianza.")
FIG(R / "espectros" / "fig_onditas_4_3.png",
    "Onditas de Morlet de las anomalías estandarizadas (potencia corregida por sesgo, % de la varianza por octava). "
    "Contorno: 95 % frente a ruido rojo; rayado: cono de influencia. A la derecha, espectro global de onditas sobre el "
    "periodograma de Fourier. Script 38.", alto_max=16 * cm)
P("Las onditas muestran <i>cuándo</i> aparece cada periodo (Figura 15). En la lluvia, la banda de 4–5 años es "
  "significativa solo entre 1983 y 2000, alrededor de los Niños de 1982–83 y 1997–98, y después casi desaparece; el caudal "
  "solo tiene pulsos cortos en 1998 y 2017. La componente de 2–7 años de la lluvia sigue a Niño 1+2 (r = 0.59) y casi "
  "nada a Niño 3.4 (r = 0.22), pero reúne solo 12 % de las anomalías (7 % en el caudal; Figura 16). La temperatura, en "
  "cambio, sigue a Niño 3.4 (r = 0.86) durante todo el registro. Estas correlaciones entre componentes filtradas tienen "
  "muy pocos grados de libertad y son descriptivas.")
FIG(R / "espectros" / "fig_onditas_banda_4_3.png",
    "(a) Varianza en la banda de 2–7 años dividida por su umbral del 95 %; (b) componente de 2–7 años reconstruida de la "
    "cuenca y de Niño 1+2. Script 38.", alto_max=10 * cm)
P("<b>Interpretación.</b> La cuenca no tiene una oscilación interanual regular: la variabilidad entre años es episódica "
  "y la concentran los Niños costeros. Esto responde a la segunda parte de la pregunta guía: los años secos no son años "
  "en que «falta» la ZCIT, sino años sin el forzamiento del mar cálido frente a la costa.")

H2("3.6 Asociaciones con el clima global (punto 5)")
P("Se eligieron tres campos con mecanismo propuesto: la SST (exigida por la guía), la presión al nivel del mar, que "
  "representa al anticiclón del Pacífico sur y al dipolo de presión del ENSO, y el viento zonal en 200 hPa, que representa "
  "el flujo del este en altura sobre los Andes. Se descartaron la altura geopotencial en 500 hPa, casi uniforme en el "
  "trópico, y la humedad específica, que en niveles bajos queda bajo el relieve del modelo.")
FIG(R / "correlaciones" / "fig_corr_Q_sst_5.png",
    "Correlación entre años (1998–2024, 27 pares por mes) del caudal con la SST de cada celda, para cada mes. Puntos: "
    "celdas que pasan el control FDR (α = 0.10, n efectivo por persistencia). Estrella: cuenca. Script 37.", alto_max=13 * cm)
P("<b>Resultado.</b> El caudal de enero y marzo crece con el calentamiento del Pacífico frente a Perú y Ecuador (Figura "
  "17): r = 0.68 en enero y 0.62 en marzo con el índice Niño 1+2, que pasan el FDR (Figura 19). Pero con Spearman la "
  "correlación de enero baja a 0.06 y, sin 1998, 2017 y 2023, el patrón de febrero–marzo desaparece: la asociación la "
  "sostienen los Niños costeros extremos. La lluvia muestra el mismo signo con Niño 1+2 en enero–abril (r = 0.41–0.47), "
  "sin pasar el FDR, y su patrón cambia entre 1981–2002 y 2003–2024, coherente con las onditas. Con Niño 3.4 (Pacífico "
  "central) la asociación es menor: el Niño canónico de 2015–16 (Niño 3.4 +2.2 °C en ene–mar) dio el cuarto año más seco "
  "(−273 mm), mientras que el Niño costero de 2017 (Niño 3.4 ≈ 0) dio crecidas. Esta distinción entre Niños es la que "
  "describen los índices E y C de Takahashi et al. (2011).")
FIG(R / "correlaciones" / "fig_corr_P_L_u200_5.png",
    "Correlación entre años de P<sub>L</sub> con el viento zonal en 200 hPa (positivo hacia el este). Script 37.",
    alto_max=13 * cm)
P("La lluvia aumenta cuando sopla más viento del este en altura sobre los Andes del norte de Perú, sobre todo al inicio "
  "y al final de la estación húmeda: r = −0.56 en abril y −0.64 en septiembre (este último pasa el FDR; Figuras 18 y 19), "
  "y lo mismo sale con IMERG en abril (r = −0.61). Es la huella del flujo del este que trae la humedad amazónica (H1). La "
  "presión al nivel del mar muestra, con todos los meses juntos, el patrón más extenso (19 % del área con el caudal): "
  "presión baja en el Pacífico este y alta en el oeste, el patrón de la Oscilación del Sur.")
FIG(R / "correlaciones" / "fig_indices_5_4.png",
    "Correlación por mes con índices (Niño 1+2, Niño 3.4 y promedios de cajas de cada campo). * p < 0.05 con n "
    "efectivo; ** además q FDR < 0.05. Script 37.", alto_max=8 * cm)
P("<b>Limitaciones.</b> Con 27 años por mes solo sobreviven correlaciones |r| ≳ 0.6; pocas celdas pasan el FDR (como "
  "máximo 3–8 % del área en algún mes). La SST y la presión comparten la señal del ENSO, por lo que no son evidencias "
  "independientes. Una correlación no demuestra el mecanismo: la conexión física la aportan el ascenso, la convergencia "
  "de humedad y la inversión de la sección 3.2.")

H2("3.7 Síntesis física: esquema conceptual y tabla de evidencias")
FIG(R / "sintesis" / "esquema_conceptual.png",
    "Esquema conceptual de la cuenca: circulación regional, lluvia, almacenamiento, pérdidas y caudal, con sus escalas de "
    "tiempo. Script 39.", alto_max=13 * cm)
TAB([["Resultado principal", "Mecanismo propuesto", "Evidencia propia", "Fuente consultada", "Limitación o alternativa"],
     ["Estación seca may–sep (P ≈ 3 mm/mes) en latitud tropical",
      "ZCIT del Pacífico oriental al norte del ecuador; subsidencia del anticiclón del Pacífico sur",
      "ω500 > 0 y divergencia de humedad jun–ago; IVT mayor pero divergente (Fig. 8)",
      "Mitchell y Wallace (1992); Xie y Philander (1994); Garreaud (2009)",
      "No medimos la posición de la ZCIT; ERA5 suaviza los Andes"],
     ["Lluvia unimodal con máximo en marzo",
      "Convección de verano sobre los Andes con humedad del este (monzón sudamericano)",
      "Ascenso y convergencia máximos en marzo; u200 del este asociado a más lluvia en abr y sep (Figs. 6, 8, 18)",
      "Vera et al. (2006); Garreaud et al. (2009)",
      "Correlaciones con variables del mismo reanálisis"],
     ["Caudal desfasado 1–1.5 meses y estiaje con R > P",
      "Almacenamiento en suelos y acuíferos fisurados",
      "ρ 0.52 → 0.81 con un mes; modelo con rezagos +26–41 % (Figs. 10–11)",
      "Lavado-Casimiro et al. (2012)",
      "Sin datos de agua subterránea; R/P > Budyko sin explicar"],
     ["Años extremos húmedos (1998, 2017)",
      "Niño costero: mar cálido debilita la inversión y dispara la convección",
      "Q ene–mar con Niño 1+2 r 0.62–0.68; banda 2–7 años activa en 1983–2000 (Figs. 15–19)",
      "Takahashi et al. (2011); Garreaud (2018)",
      "Lo sostienen 2–3 eventos; no robusto con Spearman"],
     ["Años secos (2003–05, 2016)",
      "Ausencia de forzamiento costero; Niño canónico del Pacífico central no trae lluvia",
      "2016 (Niño 3.4 +2.2) −273 mm; correlación con Niño 3.4 débil",
      "Lagos et al. (2008); Takahashi et al. (2011)",
      "Pocos casos; 2022 (La Niña) solo −126 mm"],
     ["Calentamiento +0.18 a +0.23 °C/década",
      "Calentamiento regional",
      "Dos fuentes, robusto a método y a años El Niño (Fig. 12)",
      "Hersbach et al. (2020); Muñoz-Sabater et al. (2021)",
      "Cambios en las observaciones asimiladas"]],
    "Tabla de evidencias: resultado, mecanismo, evidencia propia, fuente y limitación.",
    [0.18, 0.21, 0.24, 0.18, 0.19])

# ====================================================================== 4. Conclusiones
H1("4. Conclusiones")
B("<b>La pregunta guía.</b> La hipótesis inicial (H0: la lluvia sigue a la ZCIT) no se sostiene. Sobre el Pacífico "
  "oriental la ZCIT se mantiene al norte del ecuador, y la lluvia de la cuenca proviene de la convección de verano sobre "
  "los Andes con humedad del este. La sequía de mayo a septiembre no se debe a falta de humedad —el transporte es incluso "
  "mayor— sino a la subsidencia del anticiclón del Pacífico sur, que impide el ascenso. Los datos (ERA5, radiosondeos) "
  "apoyan H1, con la salvedad de que no medimos directamente la posición de la ZCIT.")
B("<b>Clasificación.</b> Régimen pluvial tropical andino de vertiente pacífica, unimodal y estacional, isotermal y "
  "subhúmedo seco (P/PET 0.62), con caudal desfasado 1–1.5 meses y estiaje sostenido por almacenamiento. La clase de "
  "aridez cambia con la fuente de lluvia (semiárida con IMERG).")
B("<b>Variabilidad entre años.</b> La dominan los Niños costeros (1983, 1998, 2017), no una oscilación regular: la banda "
  "de 2–7 años explica 7–12 % de las anomalías de lluvia y caudal y solo fue activa en 1983–2000. Los años secos son años "
  "sin forzamiento costero, incluido el Niño canónico de 2016.")
B("<b>Cambios en el tiempo.</b> La temperatura sube de forma robusta (+0.18 a +0.23 °C por década); la lluvia y el "
  "caudal no tienen tendencia demostrable con este registro.")
B("<b>Límites.</b> El balance hídrico no cierra (R/P 0.48 frente a 0.16 de Budyko), la lluvia de referencia difiere "
  "15–25 % entre versiones de PISCOp e IMERG la subestima 35 %, y las asociaciones con el clima global dependen de dos o "
  "tres eventos. Los resultados mejor sustentados son el ciclo anual, el desfase lluvia–caudal y el calentamiento.")

# ====================================================================== 5. Uso de IA
H1("5. Uso de inteligencia artificial")
P("Nivel A (abierto) de la política del curso. Herramienta: Claude (Anthropic), mediante Claude Code en VS Code, modelos "
  "Claude Opus 5.5 y Fable 5.1, octubre de 2026.")
B("<b>Tareas en que intervino:</b> programación y depuración de los scripts en Python (descarga, agregación, relleno, "
  "estadísticos, tendencias, espectros, onditas, correlaciones con campos globales), diseño de la paleta común de figuras, "
  "la página web de resultados, el esquema conceptual y un borrador de este informe a partir de los resultados del grupo. "
  "[El grupo debe precisar qué scripts y secciones escribió cada integrante.]")
B("<b>Verificaciones:</b> revisión manual de la agregación de 2010-03 y 1998-03; Parseval (Σ S·Δf = varianza) y "
  "contraste con scipy.signal.periodogram; pendientes OLS y de Sen invariantes al restar la climatología; validación del "
  "relleno con huecos sintéticos; comprobación de que cada cifra del texto coincide con los CSV de resultados. [El grupo "
  "debe añadir sus propias comprobaciones.]")
B("<b>Propuestas corregidas o rechazadas:</b> en un borrador previo del grupo, generado con apoyo de IA, aparecían cifras y "
  "afirmaciones que no coinciden con los datos y se corrigieron: coordenadas de la estación, cuenca extendida hasta el "
  "nivel del mar (empieza en 678 m), caudal mínimo de 1.2 m³/s (es 0.36 m³/s), correlación con Niño 1+2 «> 0.70» (es "
  "0.62–0.68 y no robusta), análisis de doble masa y relleno con estaciones vecinas (no se hicieron), independencia entre "
  "P<sub>L</sub> e IMERG (comparten pluviómetros) y 2007 como año seco (anomalía −27 mm). También se descartó como "
  "explicación del máximo térmico de septiembre la menor surgencia costera, porque la cuenca está sobre la inversión.")
B("<b>Contribución de los integrantes:</b> [completar por el grupo].")
P("Las referencias de la sección 6 son las que sustentan la discusión. El grupo debe leer cada una y comprobar su DOI y "
  "páginas antes de la entrega; una referencia propuesta por la IA no sustituye esa lectura.", "aviso")

# ====================================================================== 6. Referencias
H1("6. Referencias")
REFS = [
    "Aybar, C., Fernández, C., Huerta, A., Lavado, W., Vega, F. y Felipe-Obando, O. (2020). Construction of a high-resolution gridded rainfall dataset for Peru from 1981 to the present day. <i>Hydrological Sciences Journal</i>, 65(5), 770–785. doi:10.1080/02626667.2019.1649411",
    "Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. <i>Journal of the Royal Statistical Society B</i>, 57(1), 289–300. doi:10.1111/j.2517-6161.1995.tb02031.x",
    "Bretherton, C. S., Widmann, M., Dymnikov, V. P., Wallace, J. M. y Bladé, I. (1999). The effective number of spatial degrees of freedom of a time-varying field. <i>Journal of Climate</i>, 12(7), 1990–2009. doi:10.1175/1520-0442(1999)012&lt;1990:TENOSD&gt;2.0.CO;2",
    "CAMELS-PE v1.0.1 (2026). Conjunto de datos de cuencas del Perú. Zenodo. doi:10.5281/zenodo.21195425",
    "Funk, C. et al. (2015). The climate hazards infrared precipitation with stations — a new environmental record for monitoring extremes. <i>Scientific Data</i>, 2, 150066. doi:10.1038/sdata.2015.66",
    "Garreaud, R. D. (2009). The Andes climate and weather. <i>Advances in Geosciences</i>, 22, 3–11. doi:10.5194/adgeo-22-3-2009",
    "Garreaud, R. D. (2018). A plausible atmospheric trigger for the 2017 coastal El Niño. <i>International Journal of Climatology</i>, 38, e1296–e1302. doi:10.1002/joc.5426",
    "Garreaud, R. D., Vuille, M., Compagnucci, R. y Marengo, J. (2009). Present-day South American climate. <i>Palaeogeography, Palaeoclimatology, Palaeoecology</i>, 281, 180–195. doi:10.1016/j.palaeo.2007.10.032",
    "Hamed, K. H. y Rao, A. R. (1998). A modified Mann–Kendall trend test for autocorrelated data. <i>Journal of Hydrology</i>, 204, 182–196. doi:10.1016/S0022-1694(97)00125-X",
    "Hersbach, H. et al. (2020). The ERA5 global reanalysis. <i>Quarterly Journal of the Royal Meteorological Society</i>, 146, 1999–2049. doi:10.1002/qj.3803",
    "Huang, B. et al. (2017). Extended Reconstructed Sea Surface Temperature, version 5 (ERSSTv5). <i>Journal of Climate</i>, 30, 8179–8205. doi:10.1175/JCLI-D-16-0836.1",
    "Huffman, G. J. et al. (2023). GPM IMERG Final Precipitation L3 1 month 0.1° × 0.1° V07. NASA GES DISC. doi:10.5067/GPM/IMERG/3B-MONTH/07",
    "Klein, S. A. y Hartmann, D. L. (1993). The seasonal cycle of low stratiform clouds. <i>Journal of Climate</i>, 6, 1587–1606. doi:10.1175/1520-0442(1993)006&lt;1587:TSCOLS&gt;2.0.CO;2",
    "Lagos, P., Silva, Y., Nickl, E. y Mosquera, K. (2008). El Niño-related precipitation variability in Perú. <i>Advances in Geosciences</i>, 14, 231–237. doi:10.5194/adgeo-14-231-2008",
    "Lavado-Casimiro, W. S., Ronchail, J., Labat, D., Espinoza, J. C. y Guyot, J. L. (2012). Basin-scale analysis of rainfall and runoff in Peru (1969–2004): Pacific, Titicaca and Amazonas drainages. <i>Hydrological Sciences Journal</i>, 57(4), 625–642. doi:10.1080/02626667.2012.672985",
    "Liu, Y., Liang, X. S. y Weisberg, R. H. (2007). Rectification of the bias in the wavelet power spectrum. <i>Journal of Atmospheric and Oceanic Technology</i>, 24, 2093–2102. doi:10.1175/2007JTECHO511.1",
    "Mitchell, T. P. y Wallace, J. M. (1992). The annual cycle in equatorial convection and sea surface temperature. <i>Journal of Climate</i>, 5, 1140–1156. doi:10.1175/1520-0442(1992)005&lt;1140:TACIEC&gt;2.0.CO;2",
    "Muñoz-Sabater, J. et al. (2021). ERA5-Land: a state-of-the-art global reanalysis dataset for land applications. <i>Earth System Science Data</i>, 13, 4349–4383. doi:10.5194/essd-13-4349-2021",
    "Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. <i>The Professional Geographer</i>, 32(3), 300–309. doi:10.1111/j.0033-0124.1980.00300.x",
    "Peel, M. C., Finlayson, B. L. y McMahon, T. A. (2007). Updated world map of the Köppen–Geiger climate classification. <i>Hydrology and Earth System Sciences</i>, 11, 1633–1644. doi:10.5194/hess-11-1633-2007",
    "Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. <i>Journal of the American Statistical Association</i>, 63, 1379–1389. doi:10.1080/01621459.1968.10480934",
    "Takahashi, K., Montecinos, A., Goubanova, K. y Dewitte, B. (2011). ENSO regimes: reinterpreting the canonical and Modoki El Niño. <i>Geophysical Research Letters</i>, 38, L10704. doi:10.1029/2011GL047364",
    "Torrence, C. y Compo, G. P. (1998). A practical guide to wavelet analysis. <i>Bulletin of the American Meteorological Society</i>, 79, 61–78. doi:10.1175/1520-0477(1998)079&lt;0061:APGTWA&gt;2.0.CO;2",
    "Vera, C. et al. (2006). Toward a unified view of the American monsoon systems. <i>Journal of Climate</i>, 19, 4977–5000. doi:10.1175/JCLI3896.1",
    "Walsh, R. P. D. y Lawler, D. M. (1981). Rainfall seasonality: description, spatial patterns and change through time. <i>Weather</i>, 36(7), 201–208. doi:10.1002/j.1477-8696.1981.tb05400.x",
    "Wilks, D. S. (2016). “The stippling shows statistically significant grid points”: how research results are routinely overstated and overinterpreted, and what to do about it. <i>Bulletin of the American Meteorological Society</i>, 97, 2263–2273. doi:10.1175/BAMS-D-15-00267.1",
    "Xie, S.-P. y Philander, S. G. H. (1994). A coupled ocean–atmosphere model of relevance to the ITCZ in the eastern Pacific. <i>Tellus A</i>, 46(4), 340–350. doi:10.3402/tellusa.v46i4.15484",
]
for r_ in REFS:
    P(r_, "ref")

doc = SimpleDocTemplate(str(SALIDA), pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.8 * cm, title="Clasificación hidroclimática del río Chicama hasta El Tambo",
                        author="Grupo Tarea 1 Hidrología 2026-2")
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print(f"{SALIDA} · {N_FIG[0]} figuras · {N_TAB[0]} tablas")
