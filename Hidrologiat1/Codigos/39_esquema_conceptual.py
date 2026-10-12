"""
Síntesis: esquema conceptual de la cuenca (circulación regional → lluvia → almacenamiento → pérdidas → caudal),
con las escalas de tiempo y las cifras del análisis. Las cifras vienen de los CSV de los puntos 1–5 (ver informe).

Salida: Tarea 1/El_Tambo/resultados/sintesis/esquema_conceptual.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from estilo_figuras import VAR, EST, TINTA, TINTA2, GRIS, aplicar_estilo

aplicar_estilo()
OUT = Path(__file__).resolve().parents[2] / "Tarea 1" / "El_Tambo" / "resultados" / "sintesis"
OUT.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(15, 9.4))
ax.set_xlim(0, 15); ax.set_ylim(0, 9.4); ax.axis("off")


def caja(x, y, w, h, titulo, texto, color, alfa=0.10):
    for fc, ec, a in ((color, color, alfa), ("none", color, 1)):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec,
                                    alpha=a, lw=0 if fc != "none" else 1.4))
    ax.text(x + 0.15, y + h - 0.15, titulo, ha="left", va="top", fontsize=10.5, fontweight="bold", color=TINTA)
    ax.text(x + 0.15, y + h - 0.55, texto, ha="left", va="top", fontsize=8.6, color=TINTA2, linespacing=1.35)


def flecha(x0, y0, x1, y1, color=TINTA):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16, lw=1.6, color=color))


def nota(x, y, txt, ha="left"):
    ax.text(x, y, txt, fontsize=8.2, style="italic", color=TINTA2, ha=ha, va="center")


ax.text(0.1, 9.3, "Esquema conceptual · cuenca del río Chicama hasta El Tambo (2 170 km², 678–4 308 m s.n.m.)",
        fontsize=13, fontweight="bold", va="top")
ax.text(0.1, 8.9, "Arriba: circulación (hipótesis contrastadas con ERA5, radiosondeos y SST). Abajo: balance de la cuenca "
        "(CAMELS-PE, 1998–2024). En cursiva, escalas de tiempo.", fontsize=9, color=TINTA2, va="top")

# ---- circulación
caja(0.1, 5.85, 4.7, 2.75, "Estación húmeda (dic–abr)",
     "• ZCIT del Pacífico oriental al norte del\n  ecuador todo el año: no llega a 7.6°S\n"
     "• Ascenso sobre los Andes (ω500 −0.09 Pa/s\n  en marzo) y convergencia de humedad\n  (+4.1 mm/d)\n"
     "• Humedad del este (IVT 270°, agua\n  precipitable 28 kg/m²); u200 del este\n• Inversión costera débil (LTS 17 K)",
     EST["húmeda"])
caja(5.15, 5.85, 4.7, 2.75, "Estación seca (may–sep)",
     "• Anticiclón del Pacífico sur: subsidencia\n  sobre la cuenca (ω500 +0.04 Pa/s)\n"
     "• Divergencia de humedad (−2.1 mm/d)\n  aunque el IVT es mayor (50 kg m⁻¹ s⁻¹)\n"
     "• Inversión fuerte (LTS 24 K; tope\n  1.0–1.3 km en Trujillo, bajo la cuenca)\n• Lluvia P$_L$ ≈ 3 mm/mes",
     EST["seca"])
caja(10.2, 5.85, 4.7, 2.75, "Variabilidad entre años (ENSO)",
     "• Niño costero (1998, 2017): SST cálida\n  en Niño 1+2 → inversión débil, más\n  lluvia y crecidas (Q̄ ene r = 0.68)\n"
     "• Niño canónico del Pacífico central\n  (2016, Niño 3.4 +2.2): año seco\n"
     "• Banda de 2–7 años: solo 7–12 % de la\n  varianza; activa en 1983–2000",
     TINTA, alfa=0.05)

# ---- balance
caja(0.1, 2.3, 3.4, 2.75, "Precipitación P$_L$",
     "833 mm/año; 81 % en dic–abr\nmáximo en marzo (213 mm)\n\nIMERG: 539 mm/año (65 %),\nsubestima los meses\nmuy lluviosos",
     VAR["P_L"])
caja(4.3, 2.3, 3.7, 2.75, "Almacenamiento",
     "Suelo, coluviales y acuíferos\nfisurados (areniscas 40 %)\n\nρ(Q̄, P) 0.52 → 0.81 con un mes;\n0.91 con 4 meses acumulados\n"
     "estiaje sostenido: R > P en may–ago", GRIS)
caja(11.5, 2.3, 3.4, 2.75, "Caudal en El Tambo",
     "R 391 mm/año (Q̄ 27 m³/s)\nmáximo mar–abr, mínimo sep–oct\nsin tendencia\n\nNiño costero: crecidas rápidas\n"
     "(días–semanas): 1998 691 m³/s,\n2017 450 m³/s", VAR["Q"])
caja(4.3, 0.3, 3.7, 1.6, "Pérdidas (evapotranspiración)",
     "PET 1 344 mm/año (P/PET 0.62)\nP − R ≈ 440 mm/año\nBudyko espera R/P 0.16; observado 0.48", EST["seca"], alfa=0.08)
ax.text(8.6, 1.95, "¿Por qué R/P supera a Budyko? (no resuelto)\n• P subestimada en las cabeceras\n"
        "• PET potencial ≫ ET real\n• aportes de fuera de la divisoria\n• sesgo de la curva de descarga",
        fontsize=8.6, color=TINTA2, va="top", linespacing=1.4)

flecha(2.2, 5.8, 1.8, 5.1, EST["húmeda"]); nota(2.15, 5.45, "meses")
flecha(6.6, 5.8, 3.1, 5.1, EST["seca"]); nota(4.95, 5.6, "suprime la lluvia", ha="center")
flecha(12.8, 5.8, 13.2, 5.1, TINTA); nota(13.15, 5.45, "años (2–7, episódico)")
flecha(3.55, 3.7, 4.25, 3.7)
flecha(8.05, 3.7, 11.45, 3.7); nota(9.75, 3.95, "recesión y flujo base: 1–3 meses", ha="center")
flecha(6.15, 2.25, 6.15, 1.95, EST["seca"])
fig.savefig(OUT / "esquema_conceptual.png", dpi=170, bbox_inches="tight")
print(OUT / "esquema_conceptual.png")
