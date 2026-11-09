// Self-play of MWU and optimistic MWU on rock-paper-scissors, drawn on the simplex.
// Same dynamics and starting point as code/mwu_rps.py (player 1's strategy is drawn).
(function () {
  "use strict";
  var A = [[0, -1, 1], [1, 0, -1], [-1, 1, 0]];
  var X0 = [0.634731506313261, 0.24247562209952123, 0.12279287158721759];
  var Y0 = [0.06211401342478154, 0.26564355107707865, 0.6722424354981398];
  var TMAX = 80;                       // continuous-time horizon: steps = TMAX / eta
  var V = [[0.5, Math.sqrt(3) / 2], [0, 0], [1, 0]];   // rock (top), paper, scissors

  var canvas = document.getElementById("sim");
  var slider = document.getElementById("eta"), out = document.getElementById("eta-out");
  var replay = document.getElementById("replay");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");
  var pcanvas = document.getElementById("probs"), pctx = pcanvas && pcanvas.getContext("2d");
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
  function simulate(eta) {
    var n = Math.round(TMAX / eta);
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
  function draw(upto) {
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var red = css("--sk-red", "#d55e00"), blue = css("--sk-blue", "#0072b2"), green = css("--sk-green", "#009e73");
    var grey = css("--sk-grey", "#8a8a8a"), faint = css("--sk-faint", "#d9d9d9"), fg = css("--text", "#1a1a1a"), bg = css("--bg", "#fff");
    var side = Math.min(w * 0.7, (h - 70) / 0.866);
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
      ctx.textAlign = align; ctx.fillText(text, q[0] + dx, q[1] + dy);
    }
    tag(data.M, red, "MWU", 9, -14, "left");
    tag(data.O, green, "optimistic MWU", -12, 24, "right");
    tag(data.A, blue, "average", 12, 18, "left");
    drawProbs(upto);
  }


  // Right-hand canvas: probability of each move over time, one row per method.
  function drawProbs(upto) {
    if (!pctx) return;
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
    pctx.fillText("time", w - right, h - 4);
  }

  function frame() {
    var per = Math.max(1, Math.round(0.45 / (TMAX / data.n)));   // about 0.45 time units per frame
    k = Math.min(data.n, k + per);
    draw(k);
    raf = k < data.n ? requestAnimationFrame(frame) : 0;
  }
  function start() {
    cancelAnimationFrame(raf);
    var eta = parseFloat(slider.value);
    out.textContent = eta.toFixed(2);
    data = simulate(eta); k = 0;
    if (reduce) { k = data.n; draw(k); raf = 0; return; }
    draw(0); raf = requestAnimationFrame(frame);
  }
  slider.addEventListener("input", start);
  replay.addEventListener("click", start);
  window.addEventListener("resize", function () { if (data) draw(k); });
  // Start when visible (saves work if the page is opened in the background).
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (e) { if (e[0].isIntersecting) { io.disconnect(); start(); } }, { threshold: 0.3 });
    io.observe(canvas);
  } else start();
})();
