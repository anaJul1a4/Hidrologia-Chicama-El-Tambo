(function () {
  "use strict";
  const D = window.DATOS;
  const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
  const UNID = { P_L: "mm/mes", P_I: "mm/mes", R: "mm/mes", Q: "m³/s", T: "°C" };
  const NOMBRE = { P_L: "P<sub>L</sub>", P_I: "P<sub>I</sub>", R: "R", Q: "Q̄", T: "T" };
  const estado = { clim: "P_L", anom: "P_L" };
  const dibujadas = new Set();

  // ------------------------------------------------------------ tema (tokens de estilo.css)
  function tema() {
    const cs = getComputedStyle(document.documentElement);
    const v = (n) => cs.getPropertyValue(n).trim();
    return { card: v("--card"), ink: v("--ink"), ink2: v("--ink2"), muted: v("--muted"), line: v("--line"),
             axis: v("--axis"), s1: v("--s1"), s2: v("--s2"), s3: v("--s3"), pos: v("--pos"), neg: v("--neg"),
             excl: v("--excl") };
  }
  function rgba(hex, a) {
    const h = hex.replace("#", "");
    const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  function eje(t, extra) {
    return Object.assign({ gridcolor: t.line, linecolor: t.axis, zerolinecolor: t.axis, showline: true,
      ticks: "outside", tickcolor: t.axis, ticklen: 4, tickfont: { color: t.muted }, automargin: true,
      title: { font: { color: t.ink2, size: 12 } } }, extra || {});
  }
  function base(t, extra) {
    return Object.assign({
      paper_bgcolor: t.card, plot_bgcolor: t.card,
      font: { family: 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif', size: 12, color: t.ink2 },
      margin: { l: 60, r: 18, t: 40, b: 40 }, hovermode: "x unified",
      hoverlabel: { bgcolor: t.card, bordercolor: t.line, font: { color: t.ink, size: 12 } },
      legend: { orientation: "h", x: 0, y: 1.02, yanchor: "bottom", font: { color: t.ink2 }, bgcolor: "rgba(0,0,0,0)" },
    }, extra);
  }
  const CONFIG = { responsive: true, displaylogo: false, scrollZoom: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
    toImageButtonOptions: { format: "png", scale: 2, filename: "el_tambo" } };
  function ejeTiempo(t, extra) {
    return eje(t, Object.assign({ type: "date", hoverformat: "%Y-%m", tickformat: "%Y" }, extra || {}));
  }
  function slider(t) {
    return { visible: true, thickness: 0.07, bgcolor: t.card, bordercolor: t.line, borderwidth: 1 };
  }
  function mesSiguiente(f) {
    let [y, m] = f.split("-").map(Number);
    m += 1; if (m > 12) { m = 1; y += 1; }
    return `${y}-${String(m).padStart(2, "0")}`;
  }
  function linea(x, y, nombre, color, extra) {
    return Object.assign({ type: "scatter", mode: "lines", x, y, name: nombre, line: { color, width: 2 },
      connectgaps: false }, extra || {});
  }

  // ------------------------------------------------------------ gráficas
  const G = {};

  // 1.1 · cuatro paneles alineados
  G.serie11 = function (t) {
    const x = D.fechas;
    const dom = [[0.79, 1], [0.54, 0.74], [0.29, 0.49], [0.04, 0.24]];
    const banderas = [["interpolado_diario", "circle-open", "días interpolados"], ["escalado", "square", "mes escalado"],
                      ["modelo_mensual", "diamond", "modelo mensual"]];
    const data = [
      { type: "bar", x, y: D.P_L, name: "P<sub>L</sub>", yaxis: "y", marker: { color: t.s1 }, showlegend: false,
        hovertemplate: "%{y:.1f} mm/mes" },
      linea(x, D.Q, "Q̄", t.s1, { yaxis: "y2", showlegend: false, line: { color: t.s1, width: 1.6 },
        hovertemplate: "%{y:.2f} m³/s" }),
      linea(x, D.R, "R", t.s1, { yaxis: "y3", showlegend: false, line: { color: t.s1, width: 1.6 },
        hovertemplate: "%{y:.1f} mm/mes" }),
      linea(x, D.T_piscot, "T PISCOt", t.s1, { yaxis: "y4", line: { color: t.s1, width: 1.6 },
        hovertemplate: "%{y:.2f} °C" }),
      linea(x, D.T_est, "T estimada (ERA5-Land + sesgo)", t.s3, { yaxis: "y4",
        line: { color: t.s3, width: 1.8, dash: "dash" }, hovertemplate: "%{y:.2f} °C" }),
    ];
    banderas.forEach(([cod, sim, txt]) => {
      const xi = [], yq = [], yr = [];
      D.R_flag.forEach((f, i) => { if (f === cod) { xi.push(x[i]); yq.push(D.Q[i]); yr.push(D.R[i]); } });
      if (!xi.length) return;
      const mk = { color: t.s2, size: 8, symbol: sim, line: { color: t.s2, width: 1.5 } };
      data.push({ type: "scatter", mode: "markers", x: xi, y: yq, yaxis: "y2", name: "Q̄ rellenado: " + txt,
        legendgroup: cod, marker: mk, hovertemplate: txt });
      data.push({ type: "scatter", mode: "markers", x: xi, y: yr, yaxis: "y3", name: txt, legendgroup: cod,
        showlegend: false, marker: mk, hoverinfo: "skip" });
    });
    const shapes = [];
    D.R_flag_obs.forEach((f, i) => {
      if (f === "excluido" || f === "sin_dato") {
        shapes.push({ type: "rect", xref: "x", yref: "paper", x0: x[i], x1: mesSiguiente(x[i]), y0: 0, y1: 1,
          fillcolor: t.excl, line: { width: 0 }, layer: "below" });
      }
    });
    const titulos = ["P<sub>L</sub> · precipitación acumulada mensual (CAMELS-PE)", "Q̄ · caudal medio mensual (SENAMHI, rellenado)",
                     "R · escorrentía en lámina", "T · temperatura media mensual"];
    const annotations = titulos.map((txt, i) => ({ text: txt, xref: "paper", yref: "paper", x: 0, y: dom[i][1],
      xanchor: "left", yanchor: "bottom", showarrow: false, font: { color: t.ink, size: 12.5 } }));
    return { data, layout: base(t, {
      height: 860, margin: { l: 62, r: 18, t: 56, b: 30 }, bargap: 0.15, shapes, annotations,
      legend: { orientation: "h", x: 0, y: 1.035, yanchor: "bottom", font: { color: t.ink2 } },
      xaxis: ejeTiempo(t, { anchor: "y4", rangeslider: slider(t) }),
      yaxis: eje(t, { domain: dom[0], title: { text: "mm/mes" }, rangemode: "tozero" }),
      yaxis2: eje(t, { domain: dom[1], title: { text: "m³/s" }, rangemode: "tozero" }),
      yaxis3: eje(t, { domain: dom[2], title: { text: "mm/mes" }, rangemode: "tozero" }),
      yaxis4: eje(t, { domain: dom[3], title: { text: "°C" } }),
    }) };
  };

  // 1.1 · temperatura
  G.temp = function (t) {
    const x = D.fechas;
    return { data: [
      linea(x, D.T_piscot, "PISCOt v1.2 (CAMELS-PE)", t.s1, { hovertemplate: "%{y:.2f} °C" }),
      linea(x, D.T_era5, "ERA5-Land sin corregir", t.s2, { line: { color: t.s2, width: 1.6 }, hovertemplate: "%{y:.2f} °C" }),
      linea(x, D.T_est, "Estimada: ERA5-Land + sesgo mensual", t.s3, { line: { color: t.s3, width: 2, dash: "dash" },
        hovertemplate: "%{y:.2f} °C" }),
    ], layout: base(t, { height: 470, xaxis: ejeTiempo(t, { rangeslider: slider(t) }),
      yaxis: eje(t, { title: { text: "Temperatura media mensual (°C)" } }) }) };
  };

  // 1.2 · fuentes de precipitación
  G.precip = function (t) {
    const x = D.fechas;
    const h = "%{y:.1f} mm/mes";
    return { data: [
      linea(x, D.P_L, "P<sub>L</sub> CAMELS-PE", t.s1, { hovertemplate: h }),
      linea(x, D.P_I, "P<sub>I</sub> IMERG V07", t.s2, { hovertemplate: h }),
      linea(x, D.chirps, "CHIRPS v2.0", t.s3, { visible: "legendonly", line: { color: t.s3, width: 1.6 }, hovertemplate: h }),
      linea(x, D.piscop, "PISCOp v3.0", t.muted, { visible: "legendonly", line: { color: t.muted, width: 1.6, dash: "dot" },
        hovertemplate: h }),
    ], layout: base(t, { height: 480, xaxis: ejeTiempo(t, { rangeslider: slider(t) }),
      yaxis: eje(t, { title: { text: "Precipitación (mm/mes)" }, rangemode: "tozero" }) }) };
  };

  // 1.2 · totales anuales
  G.anual = function (t) {
    const a = D.anual;
    const h = "%{y:.0f} mm/año";
    return { data: [
      { type: "bar", x: a.anios, y: a.P_L, name: "P<sub>L</sub> CAMELS-PE", marker: { color: t.s1, cornerradius: 3 }, hovertemplate: h },
      { type: "bar", x: a.anios, y: a.P_I, name: "P<sub>I</sub> IMERG V07", marker: { color: t.s2, cornerradius: 3 }, hovertemplate: h },
    ], layout: base(t, { height: 420, barmode: "group", bargap: 0.25, bargroupgap: 0.1,
      xaxis: eje(t, { dtick: 2, tickangle: 0 }),
      yaxis: eje(t, { title: { text: "Precipitación anual (mm/año)" }, rangemode: "tozero" }) }) };
  };

  // 1.5.a · climatología con bandas
  G.clim = function (t) {
    const v = estado.clim, c = D.clim[v], u = UNID[v];
    const f = v === "T" ? ".2f" : (v === "Q" ? ".1f" : ".0f");
    const ht = (n) => `${n}: %{y:${f}} ${u}<extra></extra>`;
    const sin = { width: 0 };
    return { data: [
      { type: "scatter", mode: "lines", x: MESES, y: c.P90, line: sin, name: "P90", hovertemplate: ht("P90"), showlegend: false },
      { type: "scatter", mode: "lines", x: MESES, y: c.P10, line: sin, fill: "tonexty", fillcolor: rgba(t.s1, 0.14),
        name: "Percentiles 10–90", hovertemplate: ht("P10") },
      { type: "scatter", mode: "lines", x: MESES, y: c.Q3, line: sin, name: "Q3", hovertemplate: ht("Q3"), showlegend: false },
      { type: "scatter", mode: "lines", x: MESES, y: c.Q1, line: sin, fill: "tonexty", fillcolor: rgba(t.s1, 0.30),
        name: "Rango intercuartílico", hovertemplate: ht("Q1") },
      { type: "scatter", mode: "lines", x: MESES, y: c.mediana, name: "Mediana",
        line: { color: t.s1, width: 2, dash: "dash" }, hovertemplate: ht("Mediana") },
      { type: "scatter", mode: "lines+markers", x: MESES, y: c.media, name: "Media",
        line: { color: t.s1, width: 2.4 }, marker: { size: 8, color: t.s1, line: { color: t.card, width: 2 } },
        hovertemplate: ht("Media") },
    ], layout: base(t, { height: 440, xaxis: eje(t, { type: "category" }),
      yaxis: eje(t, { title: { text: `${NOMBRE[v]} (${u})` }, rangemode: v === "T" ? "normal" : "tozero" }) }) };
  };

  function colorSigno(t, v, y) {
    return y.map((a) => (a == null ? t.muted : ((a >= 0) !== (v === "T") ? t.pos : t.neg)));
  }

  // 1.5.b · anomalías mensuales
  G.anom = function (t) {
    const v = estado.anom, a = D.anom[v], u = UNID[v];
    const f = v === "T" ? ".2f" : ".1f";
    return { data: [
      { type: "bar", x: D.fechas, y: a.m, name: "Anomalía mensual", marker: { color: colorSigno(t, v, a.m) },
        hovertemplate: `%{y:+${f}} ${u}` },
      linea(D.fechas, a.mm12, "Media móvil de 12 meses", t.ink, { line: { color: t.ink, width: 1.8 },
        hovertemplate: `%{y:+${f}} ${u}` }),
    ], layout: base(t, { height: 440, bargap: 0, xaxis: ejeTiempo(t, { rangeslider: slider(t) }),
      yaxis: eje(t, { title: { text: `Anomalía de ${NOMBRE[v]} (${u})` }, zeroline: true }) }) };
  };

  // 1.5.b · anomalía anual
  G.anomanual = function (t) {
    const v = estado.anom, aa = D.anom_anual;
    const u = v === "T" ? "°C (media del año)" : "mm/año";
    const f = v === "T" ? ".2f" : ".0f";
    return { data: [
      { type: "bar", x: aa.anios, y: aa[v], name: "Anomalía anual", marker: { color: colorSigno(t, v, aa[v]), cornerradius: 3 },
        hovertemplate: `%{y:+${f}} ${v === "T" ? "°C" : "mm"}<extra></extra>` },
    ], layout: base(t, { height: 400, hovermode: "closest", showlegend: false, bargap: 0.2,
      xaxis: eje(t, { dtick: 2 }), yaxis: eje(t, { title: { text: `Anomalía de ${NOMBRE[v]} (${u})` }, zeroline: true }) }) };
  };

  // ------------------------------------------------------------ dibujo
  function dibujar(el) {
    const f = G[el.dataset.plot];
    if (!f || !window.Plotly) return;
    const g = f(tema());
    Plotly.react(el, g.data, g.layout, CONFIG);
    dibujadas.add(el);
  }
  function redibujarTodo() { dibujadas.forEach(dibujar); }

  document.querySelectorAll(".selector").forEach((sel) => {
    sel.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      sel.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      estado[sel.dataset.para] = b.dataset.v;
      document.querySelectorAll(`.plot[data-plot="${sel.dataset.para}"], .plot[data-plot="${sel.dataset.para}anual"]`)
        .forEach(dibujar);
    });
  });

  // ------------------------------------------------------------ pestañas
  const botones = [...document.querySelectorAll(".tabs button")];
  const paneles = [...document.querySelectorAll(".panel")];
  const ALIAS = { p15: "p15a", temp: "p11" };
  function mostrar(id, empujar) {
    id = ALIAS[id] || id;
    if (!paneles.some((p) => p.dataset.tab === id)) id = paneles[0].dataset.tab;
    paneles.forEach((p) => { p.hidden = p.dataset.tab !== id; });
    botones.forEach((b) => {
      const s = b.dataset.ir === id;
      b.setAttribute("aria-selected", String(s));
      b.tabIndex = s ? 0 : -1;
      if (s) {                                          // solo desplaza la barra de pestañas, no la página
        const bar = b.parentElement;
        if (b.offsetLeft < bar.scrollLeft || b.offsetLeft + b.offsetWidth > bar.scrollLeft + bar.clientWidth) {
          bar.scrollLeft = b.offsetLeft - 16;
        }
      }
    });
    const panel = document.getElementById("tab-" + id);
    panel.querySelectorAll(".plot").forEach((el) => {
      if (dibujadas.has(el)) Plotly.Plots.resize(el); else dibujar(el);
    });
    if (empujar) history.replaceState(null, "", "#" + id);
  }
  botones.forEach((b) => b.addEventListener("click", () => { mostrar(b.dataset.ir, true); window.scrollTo({ top: 0 }); }));
  document.querySelector(".tabs").addEventListener("keydown", (e) => {
    const i = botones.findIndex((b) => b.getAttribute("aria-selected") === "true");
    let j = null;
    if (e.key === "ArrowRight") j = (i + 1) % botones.length;
    if (e.key === "ArrowLeft") j = (i - 1 + botones.length) % botones.length;
    if (j !== null) { e.preventDefault(); botones[j].focus(); mostrar(botones[j].dataset.ir, true); }
  });
  window.addEventListener("hashchange", () => mostrar(location.hash.slice(1), false));
  mostrar(location.hash.slice(1), false);

  // ------------------------------------------------------------ tema claro/oscuro
  const raiz = document.documentElement, bt = document.querySelector(".tema");
  function aplicar(tm) { if (tm) raiz.setAttribute("data-theme", tm); else raiz.removeAttribute("data-theme"); }
  try { aplicar(localStorage.getItem("tema")); } catch (e) { /* sin almacenamiento */ }
  bt.addEventListener("click", () => {
    const oscuro = raiz.getAttribute("data-theme") === "dark" ||
      (!raiz.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    const tm = oscuro ? "light" : "dark";
    aplicar(tm);
    try { localStorage.setItem("tema", tm); } catch (e) { /* sin almacenamiento */ }
    redibujarTodo();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redibujarTodo);
  redibujarTodo();

  // ------------------------------------------------------------ visor de imágenes
  const visor = document.getElementById("visor"), vimg = visor.querySelector("img"), vfull = visor.querySelector(".full");
  document.querySelectorAll(".zoom").forEach((b) => b.addEventListener("click", () => {
    const i = b.querySelector("img");
    vimg.src = i.src; vimg.alt = i.alt; vfull.href = b.dataset.full;
    visor.classList.add("abierto"); visor.querySelector(".cerrar").focus();
  }));
  function cerrar() { visor.classList.remove("abierto"); vimg.removeAttribute("src"); }
  visor.addEventListener("click", (e) => { if (e.target !== vfull) cerrar(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
})();
