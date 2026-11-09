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
DUEL_T = 3000
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


def duel(eta, T, opt1, opt2, x0, y0):
    """Player 1 uses optimistic MWU if opt1, player 2 if opt2 (plain MWU otherwise).
    Returns both players' iterates and player 1's cumulative expected payoff."""
    x, y = x0.copy(), y0.copy()
    px, py = A @ y, -A.T @ x
    X, Y, tot = [x], [y], [0.0]
    for _ in range(T):
        gx, gy = A @ y, -A.T @ x
        tot.append(tot[-1] + x @ A @ y)
        ex, ey = (2 * gx - px if opt1 else gx), (2 * gy - py if opt2 else gy)
        px, py = gx, gy
        x = x * np.exp(eta * ex); x /= x.sum()
        y = y * np.exp(eta * ey); y /= y.sum()
        X.append(x); Y.append(y)
    return np.array(X), np.array(Y), np.array(tot)


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



OPP = np.array([0.5, 0.3, 0.2])   # an opponent who favours rock, for the "why not play uniformly?" figure


def vs_fixed_opponent(eta, T, opp=OPP):
    """MWU player against a fixed (exploitable) opponent. Returns cumulative expected payoff and best fixed move's."""
    x = NASH.copy(); G = np.zeros(3); cum = np.zeros(T + 1)
    g = A @ opp
    for t in range(T):
        cum[t + 1] = cum[t] + x @ g
        x = x * np.exp(eta * g); x /= x.sum()
    return cum, np.arange(T + 1)[:, None] * g[None, :]


def exploitability_curve(X, Y):
    n = np.arange(1, len(X) + 1)[:, None]
    xb, yb = np.cumsum(X, 0) / n, np.cumsum(Y, 0) / n
    return np.max(yb @ A.T, 1) + np.max(-(xb @ A), 1)


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
    # Why not play uniformly? Uniform guarantees 0 against anyone; MWU profits from a biased opponent
    assert np.allclose(NASH @ A, 0) and np.allclose(A @ NASH, 0)
    cum, bestfixed = vs_fixed_opponent(0.2, 600)
    bound = np.log(3) / 0.2 + 0.2 * 600 / 2
    assert cum[-1] > 0.4 * 600 * 0.3 * 1.0                          # clearly positive (uniform: exactly 0)
    assert bestfixed[-1].max() - cum[-1] <= bound                  # regret bound of Hedge holds
    # Speed of the averaged strategies, eta = 0.1: optimistic vs plain
    lm = run_all(0.1, 20000)
    em, eo = exploitability_curve(lm["Xm"], lm["Ym"]), exploitability_curve(lm["Xo"], lm["Yo"])
    assert eo[-1] < 0.2 * em[-1]
    # Head to head: optimistic player (1) against plain MWU player (2), 4 step sizes x 20 starting points
    duel_rates = {}
    for eta in (0.05, 0.1, 0.2, 0.4):
        T_ = int(600 / eta); rates = []
        for sd in range(20):
            g = np.random.default_rng(100 + sd)
            xa, ya = g.dirichlet([2, 2, 2]), g.dirichlet([2, 2, 2])
            _, _, tot = duel(eta, T_, True, False, xa, ya)
            assert tot[-1] > 0, (eta, sd)                                      # optimistic player ends ahead
            assert tot[-1] < np.log(3) / eta + eta * T_ / 2, (eta, sd)         # plain MWU's loss within Hedge's regret bound
            rates.append(tot[-1] / T_)
        duel_rates[str(eta)] = dict(T=T_, mean=float(np.mean(rates)), min=float(np.min(rates)), max=float(np.max(rates)))
    Xd, Yd, totd = duel(ETA, DUEL_T, True, False, r["x0"], r["y0"])
    tail = slice(DUEL_T // 2, None)
    kx, ky = kl_nash(Xd)[tail], kl_nash(Yd)[tail]
    assert kx.min() > 0.05 and ky.min() > 0.05                                 # neither player converges to Nash
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
        vs_biased_opponent=dict(opponent=OPP.tolist(), eta=0.2, T=600, mwu_total=float(cum[-1]), best_fixed_total=float(bestfixed[-1].max()),
                                regret=float(bestfixed[-1].max() - cum[-1]), regret_bound=float(bound), uniform_total=0.0),
        head_to_head=dict(eta=ETA, T=DUEL_T, optimistic_total=float(totd[-1]),
                          kl_optimistic_second_half=[float(kx.min()), float(kx.max())],
                          kl_plain_second_half=[float(ky.min()), float(ky.max())],
                          per_round_by_eta_20_starts=duel_rates),
        exploitability_of_average_T20000_eta0p1=dict(mwu=float(em[-1]), omwu=float(eo[-1])),
    )


# ---------------------------------------------------------------------- drawing
THEMES = {
    "light": dict(bg="#ffffff", fg="#111111", grey="#8a8a8a", faint="#d9d9d9", tint="#e6eefb"),
}
V = np.array([[0.5, np.sqrt(3) / 2], [0.0, 0.0], [1.0, 0.0]])  # rock (top), paper, scissors


def xy(P):
    return P @ V


def fade_line(ax, P, color, lw, z, glow=True):
    """Trail whose opacity ramps up along time (old = faint, recent = vivid), with a soft glow."""
    from matplotlib.collections import LineCollection
    seg = np.stack([P[:-1], P[1:]], axis=1)
    alpha = np.linspace(0.3, 1.0, len(seg))
    from matplotlib.colors import to_rgba
    if glow:
        for w, a_ in ((lw * 3.6, 0.10),):
            rgba = np.array([to_rgba(color, a_) for _ in alpha]); rgba[:, 3] = alpha * a_
            ax.add_collection(LineCollection(seg, colors=rgba, linewidths=w, capstyle="butt", zorder=z - .1))
    rgba = np.array([to_rgba(color, a_) for a_ in alpha])
    ax.add_collection(LineCollection(seg, colors=rgba, linewidths=lw, capstyle="butt", zorder=z))


def draw_simplex(ax, th, r, fs, lw, only=("m", "o", "a")):
    import matplotlib.tri as mtri
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Polygon
    ax.set_aspect("equal"); ax.axis("off")
    # soft background: distance to Nash (KL), pale blue near the edge, white at the centre
    n = 90
    pts = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    pts = np.clip(pts, 1e-3, None); pts /= pts.sum(1, keepdims=True)
    z = np.clip(kl_nash(pts), 0, 2.2)
    P2 = xy(pts)
    tri_ = mtri.Triangulation(P2[:, 0], P2[:, 1])
    cm = LinearSegmentedColormap.from_list("t", ["#ffffff", "#eaf1fd", "#c4d6f5"])
    ax.tricontourf(tri_, z, levels=np.linspace(0, 2.2, 12), cmap=cm, zorder=0)
    outline = Polygon(V, closed=True, fill=False, ec=th["faint"], lw=lw * 1.0, joinstyle="round", zorder=1)
    ax.add_patch(outline)
    for v, (txt, off, ha, va) in zip(V, (("Rock", (0, .05), "center", "bottom"), ("Paper", (-.02, -.03), "right", "top"), ("Scissors", (.02, -.03), "left", "top"))):
        ax.text(*(v + off), txt, ha=ha, va=va, color=th["grey"], fontsize=fs)
    m, a, o = xy(r["Xm"]), xy(r["Xa"]), xy(r["Xo"])
    if "m" in only: fade_line(ax, m, RED, lw, 3)
    if "o" in only: fade_line(ax, o, GREEN, lw, 4)
    if "a" in only: fade_line(ax, a, BLUE, lw * 1.25, 5)
    for P_, col in ((m, RED),):          # bright heads
        ax.plot(*P_[-1], "o", ms=fs * .5, color=col, mec="white", mew=1.5, zorder=8)
    c = xy(NASH[None])[0]
    ax.plot(*c, marker="*", ms=fs * 1.1, mfc="#ffd23f", mec=th["fg"], mew=lw * .7, zorder=9)
    if len(only) == 3: ax.plot(*m[0], marker="o", ms=fs * .45, color=th["fg"], zorder=9)
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
    fig = plt.figure(figsize=(11, 6), dpi=160, facecolor=th["bg"])
    ax = fig.add_axes([.0, .02, .5, .94], facecolor=th["bg"])
    m, a, o, c = draw_simplex(ax, th, r, 19, 2.6)
    ax.set_xlim(-.3, 1.3); ax.set_ylim(-.14, 1.0)
    t = np.arange(len(m))
    rows = (("MWU: swings wider and wider", r["Xm"], RED),
            ("Its average: settles at 1/3", r["Xa"], BLUE),
            ("Optimistic MWU: settles at 1/3", r["Xo"], GREEN))
    for k, (title, X, col) in enumerate(rows):
        h = .20
        axk = fig.add_axes([.58, .66 - k * .28, .40, h], facecolor=th["bg"])
        axk.axhline(1 / 3, color=th["fg"], lw=1.2, ls=(0, (4, 3)), zorder=1)
        for i, (al, ls_) in enumerate(((1.0, "-"), (.65, "-"), (.4, "-"))):
            axk.plot(t, X[:, i], color=col, lw=2.2, alpha=al, ls=ls_, zorder=3)
        axk.set_ylim(-.02, 1.02); axk.set_xlim(0, t[-1])
        axk.set_yticks([0, 1 / 3, 1]); axk.set_yticklabels(["0", "1/3", "1"])
        for s_ in ("top", "right"):
            axk.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            axk.spines[s_].set_color(th["faint"])
        axk.tick_params(colors=th["grey"], labelsize=13)
        if k < 2:
            axk.set_xticklabels([])
        else:
            axk.set_xlabel("iteration t", color=th["grey"], fontsize=14)
        axk.set_title(title, loc="left", color=col, fontsize=16, fontweight="bold", pad=6)
    fig.text(.58, .985, "Probability of each move (player 1)", color=th["grey"], fontsize=13, va="top")
    fig.savefig(path, facecolor=th["bg"])
    plt.close(fig)


def uniform_figure(path, eta=0.2, T=80):
    """Zoom on the learning phase against a fixed opponent (0.5, 0.3, 0.2): strategy and payoff per round."""
    th = THEMES["light"]
    plt.rcParams["font.family"] = "DejaVu Sans"
    g = A @ OPP
    x = NASH.copy(); P = np.zeros((T + 1, 3)); pay = np.zeros(T + 1)
    for t in range(T + 1):
        P[t] = x; pay[t] = x @ g
        x = x * np.exp(eta * g); x /= x.sum()
    t = np.arange(T + 1)
    best = g.max()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4), dpi=160, facecolor=th["bg"], gridspec_kw={"wspace": .28})
    for ax in (a1, a2):
        ax.set_facecolor(th["bg"])
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            ax.spines[s_].set_color(th["faint"])
        ax.tick_params(colors=th["grey"], labelsize=13)
        ax.set_xlabel("round", color=th["grey"], fontsize=14); ax.set_xlim(0, T * 1.18)
    cols = [th["grey"], RED, th["faint"]]
    names = ["rock", "paper", "scissors"]
    for k in (0, 2, 1):
        a1.plot(t, P[:, k], color=cols[k], lw=3.6 if k == 1 else 2.4)
    a1.axhline(1 / 3, color=th["faint"], lw=1.2, ls=(0, (4, 3)))
    a1.text(T * 1.02, P[-1, 1], "paper", color=RED, fontsize=15, fontweight="bold", va="center")
    a1.text(T * 1.02, .105, "rock", color=th["grey"], fontsize=14, va="center")
    a1.text(T * 1.02, .03, "scissors", color=th["grey"], fontsize=14, va="center")
    a1.text(T * .02, 1 / 3 + .02, "start: 1/3 each", color=th["grey"], fontsize=12, va="bottom")
    a1.set_ylim(0, 1.02); a1.set_ylabel("probability of each move", color=th["grey"], fontsize=14)
    a1.set_title("MWU shifts to paper", loc="left", color=th["fg"], fontsize=16, fontweight="bold", pad=10)
    a2.plot(t, 0 * t, color=th["fg"], lw=3)
    a2.axhline(best, color=th["grey"], lw=1.8, ls=(0, (4, 3)))
    a2.plot(t, pay, color=RED, lw=3.6)
    a2.text(T * .02, best + .012, "best single move (paper): 0.3", color=th["grey"], fontsize=13, va="bottom")
    a2.text(T * .45, pay[int(T * .45)] - .05, "MWU", color=RED, fontsize=15, fontweight="bold", va="top")
    a2.text(T * .30, .015, "uniform play: 0", color=th["fg"], fontsize=15, fontweight="bold", va="bottom")
    a2.set_ylim(-.04, best * 1.2); a2.set_ylabel("average points per round", color=th["grey"], fontsize=14)
    a2.set_title("and earns more than uniform play", loc="left", color=th["fg"], fontsize=16, fontweight="bold", pad=10)
    fig.subplots_adjust(left=.07, right=.97, bottom=.17, top=.86)
    fig.savefig(path, facecolor=th["bg"]); plt.close(fig)


def duel_figure(path, r, eta=ETA, T=DUEL_T, window=240):
    """Left: player 1's total points in four pairings. Right: the optimistic-vs-plain pairing on the triangle."""
    th = THEMES["light"]
    plt.rcParams["font.family"] = "DejaVu Sans"
    Xd, Yd, tot = duel(eta, T, True, False, r["x0"], r["y0"])        # optimistic (1) vs plain (2)
    _, _, tm = duel(eta, T, False, False, r["x0"], r["y0"])
    _, _, to = duel(eta, T, True, True, r["x0"], r["y0"])
    t = np.arange(T + 1)
    fig = plt.figure(figsize=(11, 4.8), dpi=160, facecolor=th["bg"])
    ax = fig.add_axes([.075, .16, .40, .70], facecolor=th["bg"])
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color(th["faint"])
    ax.tick_params(colors=th["grey"], labelsize=13)
    ax.plot(t, tm, color=th["faint"], lw=2.2); ax.plot(t, to, color=th["faint"], lw=2.2)
    ax.plot(t, 0 * t, color=th["grey"], lw=1, ls=(0, (4, 3)))
    ax.plot(t, tot, color=GREEN, lw=3); ax.plot(t, -tot, color=RED, lw=3)
    ax.set_xlim(0, T * 1.02)
    ax.text(T * .03, tot[-1] * .93, "optimistic player", color=GREEN, fontsize=15, fontweight="bold", va="top")
    ax.text(T * .03, -tot[-1] * .93, "plain MWU player", color=RED, fontsize=15, fontweight="bold", va="bottom")
    ax.annotate("same rule on both sides", xy=(T * .26, 12), xytext=(T * .03, 41), color=th["grey"], fontsize=13, va="bottom",
                arrowprops=dict(arrowstyle="-", color=th["grey"], lw=1.2, shrinkA=2, shrinkB=0))
    ax.set_xlabel("round", color=th["grey"], fontsize=14); ax.set_ylabel("total points won", color=th["grey"], fontsize=14)
    fig.text(.075, .93, "The optimistic player wins, slowly", color=th["fg"], fontsize=16, fontweight="bold", va="center")
    for k, (title, P, col) in enumerate((("Plain MWU player", Yd, RED),
                                         ("Optimistic player", Xd, GREEN))):
        axk = fig.add_axes([.58, .55 - k * .39, .39, .27], facecolor=th["bg"])
        tt = np.arange(T - window, T + 1)
        axk.axhline(1 / 3, color=th["fg"], lw=1.2, ls=(0, (4, 3)), zorder=1)
        for i, al in enumerate((1.0, .62, .38)):
            axk.plot(tt, P[-window - 1:, i], color=col, lw=2.2, alpha=al, zorder=3)
        axk.set_ylim(-.02, 1.02); axk.set_xlim(tt[0], tt[-1])
        axk.set_yticks([0, 1 / 3, 1]); axk.set_yticklabels(["0", "1/3", "1"])
        for s_ in ("top", "right"):
            axk.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            axk.spines[s_].set_color(th["faint"])
        axk.tick_params(colors=th["grey"], labelsize=13)
        if k == 0: axk.set_xticklabels([])
        else: axk.set_xlabel("round", color=th["grey"], fontsize=14)
        axk.set_title(title, loc="left", color=col, fontsize=15, fontweight="bold", pad=6)
    fig.text(.58, .93, "Both keep swinging", color=th["fg"], fontsize=15, fontweight="bold", va="center")
    fig.savefig(path, facecolor=th["bg"]); plt.close(fig)
    return tot[-1], tm[-1], to[-1]


if __name__ == "__main__":
    r = run_all()
    res = verify(r)
    (HERE / "results.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    tweet(r, OUT / "tweet.png")
    uniform_figure(OUT / "figure-uniform.png")
    print("duel totals", duel_figure(OUT / "figure-duel.png", r))
    print("wrote", OUT / "tweet.png")
