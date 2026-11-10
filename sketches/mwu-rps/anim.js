// Self-play of MWU and optimistic MWU on rock-paper-scissors, drawn on the simplex.
// Same dynamics and starting point as code/mwu_rps.py (player 1's strategy is drawn).
(function () {
  "use strict";
  var A = [[0, -1, 1], [1, 0, -1], [-1, 1, 0]];
  var X0 = [0.634731506313261, 0.24247562209952123, 0.12279287158721759];
  var Y0 = [0.06211401342478154, 0.26564355107707865, 0.6722424354981398];
  var V = [[0.5, Math.sqrt(3) / 2], [0, 0], [1, 0]];   // rock (top), paper, scissors

  var canvas = document.getElementById("sim");
  var etaSl = document.getElementById("eta"), etaOut = document.getElementById("eta-out");
  var nSl = document.getElementById("rounds"), nOut = document.getElementById("rounds-out");
  var replay = document.getElementById("replay");
  if (!canvas || !canvas.getContext) return;
  var pcanvas = document.getElementById("probs");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mv(M, v, sign, transpose) {
    var r = [0, 0, 0];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) r[i] += sign * (transpose ? M[j][i] : M[i][j]) * v[j];
    return r;
  }
  function step(p, g, eta) {
    var q = [p[0] * Math.exp(eta * g[0]), p[1] * Math.exp(eta * g[1]), p[2] * Math.exp(eta * g[2])];
    var s = q[0] + q[1] + q[2];
    return [q[0] / s, q[1] / s, q[2] / s];
  }
  // All paths for a given eta (arrays of strategies of player 1).
  function simulate(eta, n) {
    var xm = X0, ym = Y0, xo = X0, yo = Y0;
    var gxo = mv(A, yo, 1, false), gyo = mv(A, xo, -1, true);
    var M = [xm], O = [xo], Av = [xm], sum = xm.slice();
    for (var t = 1; t <= n; t++) {
      var gx = mv(A, ym, 1, false), gy = mv(A, xm, -1, true);
      xm = step(xm, gx, eta); ym = step(ym, gy, eta);
      var hx = mv(A, yo, 1, false), hy = mv(A, xo, -1, true);
      var ex = [2 * hx[0] - gxo[0], 2 * hx[1] - gxo[1], 2 * hx[2] - gxo[2]];
      var ey = [2 * hy[0] - gyo[0], 2 * hy[1] - gyo[1], 2 * hy[2] - gyo[2]];
      gxo = hx; gyo = hy;
      xo = step(xo, ex, eta); yo = step(yo, ey, eta);
      M.push(xm); O.push(xo);
      sum = [sum[0] + xm[0], sum[1] + xm[1], sum[2] + xm[2]];
      Av.push([sum[0] / (t + 1), sum[1] / (t + 1), sum[2] / (t + 1)]);
    }
    return { M: M, A: Av, O: O, n: n };
  }

  var data, k = 0, raf = 0;
  function css(name, fallback) {
    var v = getComputedStyle(canvas).getPropertyValue(name).trim();
    return v || fallback;
  }
  function draw(cv, upto) {
    var canvas = cv, ctx = cv.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var red = css("--sk-red", "#d55e00"), blue = css("--sk-blue", "#0072b2"), green = css("--sk-green", "#009e73");
    var grey = css("--sk-grey", "#8a8a8a"), faint = css("--sk-faint", "#d9d9d9"), fg = css("--text", "#1a1a1a"), bg = css("--bg", "#fff");
    var side = Math.min(w * 0.8, (h - 60) / 0.866);
    var ox = w / 2 - side / 2, oy = h - 34;
    function P(p) { return [ox + side * (p[0] * V[0][0] + p[1] * V[1][0] + p[2] * V[2][0]), oy - side * (p[0] * V[0][1] + p[1] * V[1][1] + p[2] * V[2][1])]; }
    var fs = Math.max(13, Math.min(18, w / 28));
    ctx.font = fs + "px 'STIX Two Text', Georgia, serif";
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    // triangle
    ctx.strokeStyle = faint; ctx.lineWidth = 2; ctx.beginPath();
    for (var i = 0; i < 4; i++) { var q = P([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]][i]); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }
    ctx.stroke();
    ctx.fillStyle = grey; ctx.textBaseline = "alphabetic";
    ctx.textAlign = "center"; ctx.fillText("Rock", P([1, 0, 0])[0], P([1, 0, 0])[1] - 12);
    ctx.textAlign = "center"; ctx.fillText("Paper", P([0, 1, 0])[0], P([0, 1, 0])[1] + fs + 4);
    ctx.textAlign = "center"; ctx.fillText("Scissors", P([0, 0, 1])[0], P([0, 0, 1])[1] + fs + 4);
    var c0 = P([1 / 3, 1 / 3, 1 / 3]);
    // paths
    function trail(path, color, lw) {
      // older part faint, recent part vivid: draw in chunks of increasing opacity
      var chunks = 24, len = upto + 1, size = Math.max(2, Math.ceil(len / chunks));
      ctx.strokeStyle = color; ctx.lineWidth = lw;
      for (var a0 = 0; a0 < upto; a0 += size) {
        var a1 = Math.min(upto, a0 + size);
        ctx.globalAlpha = 0.25 + 0.75 * (a1 / Math.max(1, upto));
        ctx.beginPath();
        for (var j = a0; j <= a1; j++) { var q = P(path[j]); j > a0 ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    // soft tint towards the edge (distance to Nash), then trails
    var g = ctx.createRadialGradient(c0[0], c0[1], 0, c0[0], c0[1], side * 0.62);
    g.addColorStop(0, "rgba(196,214,245,0)"); g.addColorStop(1, "rgba(196,214,245,.55)");
    ctx.save(); ctx.beginPath();
    for (var m2 = 0; m2 < 3; m2++) { var vq = P([[1, 0, 0], [0, 1, 0], [0, 0, 1]][m2]); m2 ? ctx.lineTo(vq[0], vq[1]) : ctx.moveTo(vq[0], vq[1]); }
    ctx.closePath(); ctx.clip(); ctx.fillStyle = g; ctx.fillRect(0, 0, w, h); ctx.restore();
    ctx.shadowBlur = 10;
    ctx.shadowColor = red; trail(data.M, red, 2.4);
    ctx.shadowColor = green; trail(data.O, green, 2.4);
    ctx.shadowColor = blue; trail(data.A, blue, 2.8);
    ctx.shadowBlur = 0;
    // Nash and start
    var c = P([1 / 3, 1 / 3, 1 / 3]);
    ctx.fillStyle = "#ffd23f"; ctx.strokeStyle = fg; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(c[0], c[1], 7, 0, 6.2832); ctx.fill(); ctx.stroke();
    var s0 = P(X0); ctx.fillStyle = grey; ctx.beginPath(); ctx.arc(s0[0], s0[1], 3.5, 0, 6.2832); ctx.fill();
    // direct labels at the current points
    ctx.font = "600 " + fs + "px 'STIX Two Text', Georgia, serif";
    function tag(path, color, text, dx, dy, align) {
      var q = P(path[upto]);
      ctx.shadowBlur = 12; ctx.shadowColor = color; ctx.fillStyle = color; ctx.beginPath(); ctx.arc(q[0], q[1], 5, 0, 6.2832); ctx.fill(); ctx.shadowBlur = 0;
      if (align === "left" && q[0] > w * 0.7) { align = "right"; dx = -dx; }
      var tw = ctx.measureText(text).width, tx = q[0] + dx;           // keep the label inside the canvas
      if (align === "right") tx = Math.max(tx, tw + 4); else tx = Math.min(tx, w - tw - 4);
      ctx.textAlign = align; ctx.fillText(text, tx, q[1] + dy);
    }
    tag(data.M, red, "MWU", 9, -14, "left");
    tag(data.O, green, "optimistic MWU", -14, 46, "right");
    tag(data.A, blue, "average", 12, 18, "left");
  }


  // Right-hand canvas: probability of each move over time, one row per method.
  function drawProbs(cv, upto) {
    var pcanvas = cv, pctx = cv.getContext("2d");
    var dpr = window.devicePixelRatio || 1, w = pcanvas.clientWidth, h = pcanvas.clientHeight;
    if (pcanvas.width !== Math.round(w * dpr) || pcanvas.height !== Math.round(h * dpr)) { pcanvas.width = Math.round(w * dpr); pcanvas.height = Math.round(h * dpr); }
    pctx.setTransform(dpr, 0, 0, dpr, 0, 0); pctx.clearRect(0, 0, w, h);
    var fg = css("--text", "#111"), grey = css("--sk-grey", "#8a8a8a"), faint = css("--sk-faint", "#d9d9d9");
    var rows = [["MWU: swings wider and wider", data.M, css("--sk-red", "#d55e00")],
                ["Its average: settles at 1/3", data.A, css("--sk-blue", "#0072b2")],
                ["Optimistic MWU: settles at 1/3", data.O, css("--sk-green", "#009e73")]];
    var fs = Math.max(12, Math.min(16, w / 26)), left = 30, right = 6, top0 = 4, gap = 8;
    var rh = (h - top0 - gap * 2 - 22) / 3, alphas = [1, 0.62, 0.38];
    pctx.lineJoin = "round"; pctx.lineCap = "round";
    for (var r = 0; r < 3; r++) {
      var y0 = top0 + r * (rh + gap), ty = y0 + fs + 4, py0 = ty + 4, ph = rh - (fs + 8);
      function X(t) { return left + (w - left - right) * t / data.n; }
      function Yp(p) { return py0 + ph * (1 - p); }
      pctx.font = "600 " + fs + "px 'STIX Two Text', Georgia, serif"; pctx.fillStyle = rows[r][2]; pctx.textAlign = "left"; pctx.textBaseline = "alphabetic";
      pctx.fillText(rows[r][0], left, ty);
      pctx.strokeStyle = faint; pctx.lineWidth = 1; pctx.beginPath(); pctx.moveTo(left, py0); pctx.lineTo(left, py0 + ph); pctx.lineTo(w - right, py0 + ph); pctx.stroke();
      pctx.font = (fs - 2) + "px 'STIX Two Text', Georgia, serif"; pctx.fillStyle = grey; pctx.textAlign = "right";
      pctx.fillText("1", left - 4, Yp(1) + 4); pctx.fillText("1/3", left - 4, Yp(1 / 3) + 4); pctx.fillText("0", left - 4, Yp(0) + 4);
      pctx.setLineDash([4, 3]); pctx.strokeStyle = fg; pctx.lineWidth = 1; pctx.beginPath(); pctx.moveTo(left, Yp(1 / 3)); pctx.lineTo(w - right, Yp(1 / 3)); pctx.stroke(); pctx.setLineDash([]);
      for (var i = 0; i < 3; i++) {
        pctx.globalAlpha = alphas[i]; pctx.strokeStyle = rows[r][2]; pctx.lineWidth = 2; pctx.beginPath();
        for (var t = 0; t <= upto; t++) { var q = rows[r][1][t][i]; t ? pctx.lineTo(X(t), Yp(q)) : pctx.moveTo(X(t), Yp(q)); }
        pctx.stroke();
      }
      pctx.globalAlpha = 1;
    }
    pctx.font = (fs - 2) + "px 'STIX Two Text', Georgia, serif"; pctx.fillStyle = grey; pctx.textAlign = "right";
    pctx.fillText("round " + data.n, w - right, h - 4);
  }

  // Log scales: eta from 0.01 to 0.5, rounds from 50 to 5000 (slider value 0..100), two significant digits.
  function nice(x) { return parseFloat(x.toPrecision(2)); }
  function etaOf(v) { return nice(0.01 * Math.pow(50, v / 100)); }
  function roundsOf(v) { return Math.round(nice(50 * Math.pow(100, v / 100))); }

  var zoom = null;                      // {cv, kind} while a figure is enlarged
  function redraw(upto) {
    draw(canvas, upto); drawProbs(pcanvas, upto);
    if (zoom) (zoom.kind === "sim" ? draw : drawProbs)(zoom.cv, upto);
  }
  function compute() {
    cancelAnimationFrame(raf); raf = 0;
    var eta = etaOf(parseFloat(etaSl.value)), n = roundsOf(parseFloat(nSl.value));
    etaOut.textContent = eta; nOut.textContent = n;
    data = simulate(eta, n); k = n;
    redraw(k);
  }
  function frame() {
    k = Math.min(data.n, k + Math.max(1, Math.ceil(data.n / 300)));   // about 5 seconds whatever the length
    redraw(k);
    raf = k < data.n ? requestAnimationFrame(frame) : 0;
  }
  function play() {
    cancelAnimationFrame(raf);
    if (reduce) { k = data.n; redraw(k); raf = 0; return; }
    k = 0; redraw(0); raf = requestAnimationFrame(frame);
    replay.textContent = "Replay";
  }
  etaSl.addEventListener("input", compute);
  nSl.addEventListener("input", compute);
  replay.addEventListener("click", play);
  window.addEventListener("resize", function () { if (data) redraw(k); });

  // Click on a figure: enlarged view (Escape, x or a click outside closes it).
  var host = document.querySelector(".sk") || document.body, overlay = null;
  function closeZoom() { if (overlay) { overlay.remove(); overlay = null; zoom = null; } }
  function openZoom(cv) {
    closeZoom();
    var kind = cv === canvas ? "sim" : "probs";
    overlay = document.createElement("div"); overlay.className = "sk-zoom";
    var box = document.createElement("div"); box.className = "sk-zoom-box"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Enlarged figure");
    var x = document.createElement("button"); x.type = "button"; x.className = "sk-zoom-x"; x.textContent = "\u00d7"; x.setAttribute("aria-label", "Close");
    var big = document.createElement("canvas");
    var cap = cv.parentNode.querySelector("figcaption");
    box.appendChild(x); box.appendChild(big);
    if (cap) { var p = document.createElement("p"); p.textContent = cap.textContent; box.appendChild(p); }
    overlay.appendChild(box); host.appendChild(overlay);
    overlay.addEventListener("click", function (e) { if (e.target === overlay || e.target === x) closeZoom(); });
    zoom = { cv: big, kind: kind };
    redraw(k); x.focus();
  }
  [canvas, pcanvas].forEach(function (cv) {
    cv.tabIndex = 0; cv.style.cursor = "zoom-in";
    cv.addEventListener("click", function () { openZoom(cv); });
    cv.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openZoom(cv); } });
  });
  // Static figures open the same way.
  Array.prototype.forEach.call(document.querySelectorAll(".sk figure img"), function (img) {
    img.classList.add("zoomable");
    img.addEventListener("click", function () {
      closeZoom();
      overlay = document.createElement("div"); overlay.className = "sk-zoom";
      var box = document.createElement("div"); box.className = "sk-zoom-box"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Enlarged figure");
      var x = document.createElement("button"); x.type = "button"; x.className = "sk-zoom-x"; x.textContent = "\u00d7"; x.setAttribute("aria-label", "Close");
      var big = document.createElement("img"); big.src = img.src; big.alt = img.alt;
      box.appendChild(x); box.appendChild(big);
      var cap = img.parentNode.querySelector("figcaption");
      if (cap) { var p = document.createElement("p"); p.textContent = cap.textContent; box.appendChild(p); }
      overlay.appendChild(box); host.appendChild(overlay);
      overlay.addEventListener("click", function (e) { if (e.target === overlay || e.target === x) closeZoom(); });
      x.focus();
    });
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeZoom(); });

  compute();                            // final state on load; the button plays it
})();
