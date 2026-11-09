"""Multiplicative Weights in rock-paper-scissors self-play.

Two players, zero-sum game, payoff matrix A for the row player.
  MWU  (Hedge):  x_{t+1} ∝ x_t · exp(η g_t)
  OMWU:          x_{t+1} ∝ x_t · exp(η (2 g_t − g_{t−1}))
where g_t is the payoff vector of the player at time t. Both players use the
same rule, simultaneously. Everything below is deterministic given the seed.

Usage:  uv run mwu_rps.py            (writes ../tweet.png, ../figure-*.png, results.json)
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 3
ETA = 0.2
T = 400
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent

A = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]], float)  # rock, paper, scissors
NASH = np.full(3, 1 / 3)
RED, BLUE, GREEN = "#d55e00", "#0072b2", "#009e73"  # Okabe-Ito


def simulate(eta, T, optimistic, x0, y0):
    """Return the iterates (T+1, 3) of both players."""
    x, y = x0.copy(), y0.copy()
    px, py = A @ y, -A.T @ x          # "previous" gradient: g_{-1} := g_0
    X, Y = [x], [y]
    for _ in range(T):
        gx, gy = A @ y, -A.T @ x
        ex, ey = (2 * gx - px, 2 * gy - py) if optimistic else (gx, gy)
        px, py = gx, gy
        x = x * np.exp(eta * ex); x /= x.sum()
        y = y * np.exp(eta * ey); y /= y.sum()
        X.append(x); Y.append(y)
    return np.array(X), np.array(Y)


def running_mean(P):
    return np.cumsum(P, axis=0) / np.arange(1, len(P) + 1)[:, None]


def kl_nash(P):
    """KL(Nash || p) for each row p (blows up at the boundary)."""
    return np.sum(NASH * np.log(NASH / P), axis=1)


def exploitability(x, y):
    """Sum of both players' best-response gains; 0 iff (x, y) is a Nash equilibrium."""
    return float(np.max(A @ y) + np.max(-A.T @ x))


def run_all(eta=ETA, T=T, seed=SEED):
    rng = np.random.default_rng(seed)
    x0, y0 = rng.dirichlet([2, 2, 2]), rng.dirichlet([2, 2, 2])
    Xm, Ym = simulate(eta, T, False, x0, y0)
    Xo, Yo = simulate(eta, T, True, x0, y0)
    return dict(x0=x0, y0=y0, Xm=Xm, Ym=Ym, Xo=Xo, Yo=Yo,
                Xa=running_mean(Xm), Ya=running_mean(Ym))


# ---------------------------------------------------------------- verification
def verify(r):
    """Check every claim made on the page; raise if one fails. Returns the numbers."""
    Dm = kl_nash(r["Xm"]) + kl_nash(r["Ym"])
    Do = kl_nash(r["Xo"]) + kl_nash(r["Yo"])
    Da = kl_nash(r["Xa"]) + kl_nash(r["Ya"])
    # Figure run. 1. MWU moves away from Nash: the KL divergence increases at every step ...
    assert np.all(np.diff(Dm) > 0), "KL of MWU not monotonically increasing"
    assert Dm[-1] > 5 * Dm[0]
    # ... and ends close to the boundary of the simplex
    assert r["Xm"][-1].min() < 1e-2
    # 2. The time average of MWU gets close to Nash; OMWU's last iterate too.
    assert np.abs(r["Xa"][-1] - NASH).max() < 0.05
    assert np.abs(r["Xo"][-1] - NASH).max() < 0.05
    assert Do[-1] < 0.1 * Do[0], "KL of OMWU does not decrease"
    # Long runs (same continuous-time horizon for each step size, several seeds).
    rob = []
    for eta in (0.05, 0.1, 0.2):
        for seed in range(5):
            q = run_all(eta, int(600 / eta), seed)
            dm = kl_nash(q["Xm"]) + kl_nash(q["Ym"])
            do = kl_nash(q["Xo"]) + kl_nash(q["Yo"])
            assert np.all(np.diff(dm) > 0), (eta, seed)                      # MWU: KL increases
            assert dm[-1] > 5 * dm[0] or q["Xm"][-1].min() < 1e-2, (eta, seed)
            assert do[-1] < 0.01 * do[0] and do[-1] < 1e-2, (eta, seed)      # OMWU: KL decreases to 0
            tail = do[len(do) // 4:]; tail = tail[tail > 1e-10]   # below that: float round-off
            assert np.all(np.diff(tail) < 0), (eta, seed)
            assert np.abs(q["Xa"][-1] - NASH).max() < 0.02, (eta, seed)      # average -> Nash
            assert exploitability(q["Xa"][-1], q["Ya"][-1]) < 0.06, (eta, seed)
            rob.append((eta, seed))
    long = run_all(0.1, 20000)   # the average keeps getting closer as t grows
    assert np.abs(long["Xa"][-1] - NASH).max() < 0.005
    assert exploitability(long["Xa"][-1], long["Ya"][-1]) < 0.02
    n = len(Dm) - 1
    return dict(
        eta=ETA, T=T, seed=SEED, x0=r["x0"].tolist(), y0=r["y0"].tolist(),
        kl_mwu=[float(Dm[0]), float(Dm[n // 2]), float(Dm[-1])],
        kl_avg=[float(Da[0]), float(Da[n // 2]), float(Da[-1])],
        kl_omwu=[float(Do[0]), float(Do[n // 2]), float(Do[-1])],
        mwu_last=r["Xm"][-1].tolist(), avg_last=r["Xa"][-1].tolist(), omwu_last=r["Xo"][-1].tolist(),
        exploitability_avg=exploitability(r["Xa"][-1], r["Ya"][-1]),
        exploitability_avg_T20000_eta0p1=exploitability(long["Xa"][-1], long["Ya"][-1]),
        exploitability_mwu_last=exploitability(r["Xm"][-1], r["Ym"][-1]),
        robustness_cases=len(rob),
    )


# ---------------------------------------------------------------------- drawing
THEMES = {
    "light": dict(bg="#ffffff", fg="#1a1a1a", grey="#8a8a8a", faint="#d9d9d9"),
    "dark":  dict(bg="#14161a", fg="#ececec", grey="#8c8c8c", faint="#3a3d44"),
}
V = np.array([[0.5, np.sqrt(3) / 2], [0.0, 0.0], [1.0, 0.0]])  # rock (top), paper, scissors


def xy(P):
    return P @ V


def draw_simplex(ax, th, r, fs, lw):
    ax.set_aspect("equal"); ax.axis("off")
    tri = np.vstack([V, V[:1]])
    ax.plot(tri[:, 0], tri[:, 1], color=th["faint"], lw=lw * 1.2, solid_joinstyle="round", zorder=1)
    ax.text(*V[0] + [0, .05], "Rock", ha="center", va="bottom", color=th["grey"], fontsize=fs)
    ax.text(*V[1] + [-.02, -.03], "Paper", ha="right", va="top", color=th["grey"], fontsize=fs)
    ax.text(*V[2] + [.02, -.03], "Scissors", ha="left", va="top", color=th["grey"], fontsize=fs)
    m, a, o = xy(r["Xm"]), xy(r["Xa"]), xy(r["Xo"])
    ax.plot(*m.T, color=RED, lw=lw, zorder=3, solid_capstyle="round")
    ax.plot(*o.T, color=GREEN, lw=lw, zorder=4, solid_capstyle="round")
    ax.plot(*a.T, color=BLUE, lw=lw * 1.3, zorder=5, solid_capstyle="round")
    c = xy(NASH[None])[0]
    ax.plot(*c, marker="o", ms=fs * .55, mfc=th["bg"], mec=th["fg"], mew=lw * 1.1, zorder=6)
    ax.plot(*m[0], marker="o", ms=fs * .4, color=th["grey"], zorder=6)
    return m, a, o, c


def label(ax, txt, xy_, xytext, color, fs, th, ha="left"):
    ax.annotate(txt, xy=xy_, xytext=xytext, color=color, fontsize=fs, fontweight="bold", ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=1.6, shrinkA=3, shrinkB=2), zorder=7)


def tweet(r, path):
    th = THEMES["light"]
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(12, 6.75), dpi=1600 / 12, facecolor=th["bg"])
    kw = dict(fontsize=32, fontweight="bold", va="top", linespacing=1.15)
    fig.text(.05, .90, "Plain MWU never\nsettles in rock-\npaper-scissors.", color=th["fg"], **kw)
    fig.text(.05, .50, "Its average does.", color=BLUE, **kw)
    fig.text(.05, .39, "Optimistic MWU\ndoes too.", color=GREEN, **kw)
    ax = fig.add_axes([.34, .03, .65, .94], facecolor=th["bg"])
    m, a, o, c = draw_simplex(ax, th, r, 19, 3.2)
    ax.set_xlim(-.28, 1.5); ax.set_ylim(-.14, 1.0)
    n = len(m) - 1
    label(ax, "MWU spirals\nto the edge", m[int(.55 * n)], (1.0, .62), RED, 21, th)
    label(ax, "optimistic MWU\nspirals in", o[int(.25 * n)], (-.28, .62), GREEN, 21, th)
    label(ax, "average", a[int(.5 * n)], (1.03, .27), BLUE, 21, th)
    ax.annotate("Nash", xy=c, xytext=(c[0], c[1] - .32), color=th["fg"], fontsize=19, ha="center",
                arrowprops=dict(arrowstyle="-", color=th["fg"], lw=1.4, shrinkA=2, shrinkB=7))
    fig.savefig(path, facecolor=th["bg"])
    plt.close(fig)


def page_figure(r, path, theme):
    th = THEMES[theme]
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(11, 5), dpi=160, facecolor=th["bg"])
    ax = fig.add_axes([.01, .02, .46, .94], facecolor=th["bg"])
    m, a, o, c = draw_simplex(ax, th, r, 19, 2.6)
    ax.set_xlim(-.3, 1.3); ax.set_ylim(-.14, 1.0)
    ax2 = fig.add_axes([.57, .17, .41, .70], facecolor=th["bg"])
    t = np.arange(len(m))
    D = {}
    for k, (P, Q, col) in dict(mwu=(r["Xm"], r["Ym"], RED), avg=(r["Xa"], r["Ya"], BLUE), omwu=(r["Xo"], r["Yo"], GREEN)).items():
        D[k] = kl_nash(P) + kl_nash(Q)
        ax2.plot(t, D[k], color=col, lw=2.6)
    ax2.set_yscale("log"); ax2.set_ylim(1e-4, 3e1)
    for s_ in ("top", "right"):
        ax2.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax2.spines[s_].set_color(th["faint"])
    ax2.tick_params(colors=th["grey"], labelsize=14)
    ax2.set_xlabel("iteration t", color=th["grey"], fontsize=15)
    ax2.set_title("Distance to Nash (KL, both players)", loc="left", color=th["fg"], fontsize=15, pad=12)
    n = len(t) - 1
    kw = dict(fontsize=17, fontweight="bold", ha="left", va="bottom")
    ax2.text(.55 * n, D["mwu"][int(.55 * n)] * 1.5, "MWU", color=RED, **kw)
    ax2.text(.5 * n, D["omwu"][int(.5 * n)] * 1.7, "optimistic MWU", color=GREEN, **kw)
    ax2.text(.3 * n, D["avg"][int(.3 * n)] * .1, "average of MWU", color=BLUE, **{**kw, "va": "top"})
    fig.savefig(path, facecolor=th["bg"])
    plt.close(fig)


if __name__ == "__main__":
    r = run_all()
    res = verify(r)
    (HERE / "results.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    tweet(r, OUT / "tweet.png")
    for th in ("light", "dark"):
        page_figure(r, OUT / f"figure-{th}.png", th)
    print("wrote", OUT / "tweet.png")
