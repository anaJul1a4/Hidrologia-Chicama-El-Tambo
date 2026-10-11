(function () {
  "use strict";
  const D = window.DATOS;
  const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
  const UNID = { P_L: "mm/mes", P_I: "mm/mes", R: "mm/mes", Q: "m³/s", T: "°C" };
  const NOMBRE = { P_L: "P<sub>L</sub>", P_I: "P<sub>I</sub>", R: "R", Q: "Q̄", T: "T" };
  const estado = { clim: "P_L", anom: "P_L", qc: "P_L", anios: false, serie11: new Set(["P_L", "Q", "R", "T"]) };
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
    const orden = ["P_L", "Q", "R", "T"].filter((v) => estado.serie11.has(v));
    const k = orden.length, gap = 0.05, h = (1 - 0.02 - gap * (k - 1)) / k;
    const dom = {}, ax = {};
    orden.forEach((v, i) => {                                   // de arriba hacia abajo
      const top = 1 - i * (h + gap);
      dom[v] = [top - h, top];
      ax[v] = i === 0 ? "y" : "y" + (i + 1);
    });
    const abajo = ax[orden[k - 1]];
    const data = [];
    const PANEL = {
      P_L: ["P<sub>L</sub> · precipitación acumulada mensual (CAMELS-PE)", "mm/mes"],
      Q: ["Q̄ · caudal medio mensual (SENAMHI, rellenado)", "m³/s"],
      R: ["R · escorrentía en lámina", "mm/mes"],
      T: ["T · temperatura media mensual", "°C"],
    };
    if (ax.P_L) data.push({ type: "bar", x, y: D.P_L, name: "P<sub>L</sub>", yaxis: ax.P_L, marker: { color: t.s1 },
      showlegend: false, hovertemplate: "%{y:.1f} mm/mes" });
    if (ax.Q) data.push(linea(x, D.Q, "Q̄", t.s1, { yaxis: ax.Q, showlegend: false, line: { color: t.s1, width: 1.6 },
      hovertemplate: "%{y:.2f} m³/s" }));
    if (ax.R) data.push(linea(x, D.R, "R", t.s1, { yaxis: ax.R, showlegend: false, line: { color: t.s1, width: 1.6 },
      hovertemplate: "%{y:.1f} mm/mes" }));
    if (ax.T) {
      data.push(linea(x, D.T_piscot, "T PISCOt", t.s1, { yaxis: ax.T, line: { color: t.s1, width: 1.6 },
        hovertemplate: "%{y:.2f} °C" }));
      data.push(linea(x, D.T_est, "T estimada (ERA5-Land + sesgo)", t.s3, { yaxis: ax.T,
        line: { color: t.s3, width: 1.8, dash: "dash" }, hovertemplate: "%{y:.2f} °C" }));
    }
    const banderas = [["interpolado_diario", "circle-open", "días interpolados"], ["escalado", "square", "mes escalado"],
                      ["modelo_mensual", "diamond", "modelo mensual"]];
    banderas.forEach(([cod, sim, txt]) => {
      const xi = [], yq = [], yr = [];
      D.R_flag.forEach((f, i) => { if (f === cod) { xi.push(x[i]); yq.push(D.Q[i]); yr.push(D.R[i]); } });
      if (!xi.length) return;
      const mk = { color: t.s2, size: 8, symbol: sim, line: { color: t.s2, width: 1.5 } };
      let leyenda = true;
      [["Q", yq], ["R", yr]].forEach(([v, yy]) => {
        if (!ax[v]) return;
        data.push({ type: "scatter", mode: "markers", x: xi, y: yy, yaxis: ax[v], name: "Caudal rellenado: " + txt,
          legendgroup: cod, showlegend: leyenda, marker: mk, hovertemplate: txt });
        leyenda = false;
      });
    });
    const shapes = [];                                          // solo caudal y escorrentía tienen meses excluidos
    ["Q", "R"].filter((v) => ax[v]).forEach((v) => {
      D.R_flag_obs.forEach((f, i) => {
        if (f === "excluido" || f === "sin_dato") {
          shapes.push({ type: "rect", xref: "x", yref: "paper", x0: x[i], x1: mesSiguiente(x[i]), y0: dom[v][0],
            y1: dom[v][1], fillcolor: t.excl, line: { width: 0 }, layer: "below" });
        }
      });
    });
    const annotations = orden.map((v) => ({ text: PANEL[v][0], xref: "paper", yref: "paper", x: 0, y: dom[v][1],
      xanchor: "left", yanchor: "bottom", showarrow: false, font: { color: t.ink, size: 12.5 } }));
    const layout = base(t, {
      height: 150 + 190 * k, margin: { l: 62, r: 18, t: 56, b: 30 }, bargap: 0.15, shapes, annotations,
      legend: { orientation: "h", x: 0, y: 1 + 34 / (150 + 190 * k), yanchor: "bottom", font: { color: t.ink2 } },
      xaxis: ejeTiempo(t, { anchor: abajo, rangeslider: slider(t) }),
    });
    orden.forEach((v) => {
      const nom = ax[v] === "y" ? "yaxis" : "yaxis" + ax[v].slice(1);
      layout[nom] = eje(t, { domain: dom[v], title: { text: PANEL[v][1] }, rangemode: v === "T" ? "normal" : "tozero" });
    });
    return { data, layout };
  };

  // 1.4 · disponibilidad (año × mes) y serie diaria de la variable elegida
  G.qc = function (t) {
    const v = estado.qc, dsp = D.disp[v], dd = D.diario;
    const anios = D.disp.anios;
    const nombreCond = { completo: "completo", escalado: "escalado (incompleto)", excluido: "excluido (> 10 % faltante)",
                         sin_dato: "sin dato" };
    const texto = dsp.f.map((fila, i) => fila.map((f, j) => {
      if (f == null) return "fuera del periodo común";
      const c = dsp.c[i][j];
      return `${anios[i]}-${String(j + 1).padStart(2, "0")}<br>${Math.round(100 * f)} % de días con dato<br>` +
             `condición: ${nombreCond[c] || c || "—"}`;
    }));
    const data = [{
      type: "heatmap", x: MESES, y: anios, z: dsp.f, text: texto, hovertemplate: "%{text}<extra></extra>",
      zmin: 0, zmax: 1, xgap: 1, ygap: 1, xaxis: "x", yaxis: "y",
      colorscale: [[0, rgba(t.neg, 0.85)], [0.5, rgba(t.neg, 0.35)], [0.9, rgba(t.s1, 0.25)], [1, t.s1]],
      colorbar: { title: { text: "fracción de días<br>con dato", font: { size: 11, color: t.ink2 } }, len: 0.52, y: 1,
                  yanchor: "top", thickness: 12, tickvals: [0, 0.5, 0.9, 1], ticktext: ["0", "0.5", "0.9", "1"],
                  tickfont: { color: t.muted }, outlinewidth: 0 },
    }];
    const layout = base(t, {
      height: 640, hovermode: "closest", margin: { l: 56, r: 18, t: 30, b: 40 }, showlegend: v === "Q",
      legend: { orientation: "h", x: 0, y: 0.36, yanchor: "bottom", font: { color: t.ink2 } },
      xaxis: eje(t, { type: "category", domain: [0, 1], anchor: "y", showgrid: false, side: "top" }),
      yaxis: eje(t, { domain: [0.48, 1], autorange: "reversed", dtick: 2, showgrid: false, title: { text: "Año" } }),
      annotations: [],
    });
    if (v === "P_I") {
      layout.annotations.push({ text: `IMERG es un producto mensual: no tiene serie diaria. Los ${D.fechas.length} meses están completos.`,
        xref: "paper", yref: "paper", x: 0, y: 0.18, showarrow: false, xanchor: "left", font: { color: t.ink2, size: 13 } });
      return { data, layout };
    }
    const f0 = new Date(dd.ini + "T00:00:00Z");
    const xd = Array.from({ length: dd.n }, (_, i) => new Date(f0.getTime() + i * 864e5).toISOString().slice(0, 10));
    const u = { P_L: "mm/día", Q: "m³/s", T: "°C" }[v];
    const etq = { P_L: "P<sub>L</sub> diaria (PISCOp v2.1)", Q: "Caudal diario observado (vacíos sin rellenar)",
                  T: "T media diaria (PISCOt; termina en 2020-12)" }[v];
    data.push({ type: "scattergl", mode: "lines", x: xd, y: dd[v], name: v === "Q" ? "observado" : etq,
      xaxis: "x2", yaxis: "y2", connectgaps: false, line: { color: t.s1, width: 1 },
      hovertemplate: `%{x}<br>%{y:.2f} ${u}<extra></extra>` });
    if (v === "Q") {
      data.push({ type: "scattergl", mode: "markers", x: xd, y: dd.Q_int, name: "días interpolados (relleno)",
        xaxis: "x2", yaxis: "y2", marker: { color: t.s2, size: 4 },
        hovertemplate: `%{x}<br>%{y:.2f} ${u} (interpolado)<extra></extra>` });
    }
    layout.xaxis2 = ejeTiempo(t, { domain: [0, 1], anchor: "y2", hoverformat: "%Y-%m-%d" });
    layout.yaxis2 = eje(t, { domain: [0, 0.34], title: { text: u }, rangemode: v === "T" ? "normal" : "tozero" });
    layout.annotations.push({ text: etq, xref: "paper", yref: "paper", x: 0, y: 0.345, xanchor: "left",
      yanchor: "bottom", showarrow: false, font: { color: t.ink, size: 12.5 } });
    return { data, layout };
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
    const anios = [];                                           // curvas anuales superpuestas (años individuales)
    if (estado.anios) {
      const serie = v === "T" ? D.T_piscot.map((y, i) => (y == null ? D.T_est[i] : y)) : D[v];
      const porAnio = {};
      D.fechas.forEach((f, i) => {
        const [y, m] = f.split("-").map(Number);
        (porAnio[y] = porAnio[y] || Array(12).fill(null))[m - 1] = serie[i];
      });
      Object.keys(porAnio).forEach((y) => anios.push({ type: "scatter", mode: "lines", x: MESES, y: porAnio[y],
        name: "Años individuales", legendgroup: "anios", showlegend: anios.length === 0, connectgaps: false,
        line: { color: rgba(t.muted, 0.55), width: 1 }, hovertemplate: `${y}: %{y:${f}} ${u}<extra></extra>` }));
    }
    return { data: anios.concat([
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
    ]), layout: base(t, { height: 460, hovermode: estado.anios ? "closest" : "x unified", xaxis: eje(t, { type: "category" }),
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
    const para = sel.dataset.para;
    sel.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.classList.contains("anios")) {                      // mostrar u ocultar los años individuales
        estado.anios = !estado.anios;
        b.setAttribute("aria-pressed", String(estado.anios));
      } else if (sel.classList.contains("multi")) {             // varios a la vez; siempre queda al menos uno
        const on = b.getAttribute("aria-pressed") === "true";
        if (on && estado[para].size === 1) return;
        b.setAttribute("aria-pressed", String(!on));
        if (on) estado[para].delete(b.dataset.v); else estado[para].add(b.dataset.v);
      } else {
        sel.querySelectorAll("button[data-v]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        estado[para] = b.dataset.v;
        if (para === "qc") {
          document.querySelectorAll(".qc-var").forEach((d) => { d.hidden = d.dataset.var !== b.dataset.v; });
        }
      }
      document.querySelectorAll(`.plot[data-plot="${para}"], .plot[data-plot="${para}anual"]`).forEach(dibujar);
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
