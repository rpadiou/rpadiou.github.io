"""Intuition figure for the post: a one-variable polynomial of degree four with two minima.
A local solver slides downhill from where it starts; the certificate is a flat lower bound that the best point touches.

Usage:  uv run landscape.py     (writes ../figure-landscape.png)
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parent.parent
RED, GREEN, FG, GREY, FAINT = "#d55e00", "#009e73", "#111111", "#8a8a8a", "#d9d9d9"

f = lambda x: x**4 - 2 * x**2 + 0.45 * x
df = lambda x: 4 * x**3 - 4 * x + 0.45
x = np.linspace(-1.75, 1.75, 600)
roots = np.roots([4, 0, -4, 0.45]); roots = np.sort(roots.real[np.abs(roots.imag) < 1e-9])
xg, xl = roots[0], roots[2]                      # global (left) and local (right) minima

def descend(x0, lr=0.03, n=400):
    p = [x0]
    for _ in range(n):
        p.append(p[-1] - lr * df(p[-1]))
    return np.array(p)

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(10, 4.4), dpi=160)
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
for s_ in ("left", "bottom"):
    ax.spines[s_].set_color(FAINT)
ax.tick_params(colors=GREY, labelsize=12)
ax.plot(x, f(x), color=FG, lw=3, zorder=3)
ax.axhline(f(xg), color=GREEN, lw=2, ls=(0, (5, 3)), zorder=1)
ax.text(1.74, f(xg) + .08, "certified lower bound = lowest risk", color=GREEN, fontsize=13, fontweight="bold", ha="right", va="bottom")
for x0, col in ((1.55, RED), (-0.35, GREEN)):
    p = descend(x0)[::6]
    ax.plot(p, f(p) + .0, "o", color=col, ms=4.5, alpha=.55, zorder=4)
    ax.plot(x0, f(x0), "o", color=FG, ms=9, mfc="white", mew=2, zorder=6)
ax.plot(xl, f(xl), "o", color=RED, ms=13, mec="white", mew=2, zorder=7)
ax.plot(xg, f(xg), "o", color=GREEN, ms=13, mec="white", mew=2, zorder=7)
ax.annotate("a local solver started here\nstops at this worse minimum", xy=(xl, f(xl)), xytext=(1.38, 1.15), color=RED, fontsize=13, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=RED, lw=1.6, shrinkB=8), ha="right")
ax.annotate("started here, it finds\nthe lowest risk", xy=(xg, f(xg)), xytext=(-1.2, 1.1), color=GREEN, fontsize=13, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=GREEN, lw=1.6, shrinkB=8), ha="left")
ax.text(-0.3, 2.35, "white dots: starting points", color=GREY, fontsize=11, ha="left")
ax.set_xlim(-1.8, 1.8); ax.set_ylim(-1.65, 2.6)
ax.set_xlabel("portfolio (one weight)", color=GREY, fontsize=13); ax.set_ylabel("risk  f", color=GREY, fontsize=13)
fig.tight_layout(); fig.savefig(OUT / "figure-landscape.png"); plt.close(fig)
print("minima", xg, f(xg), xl, f(xl))
