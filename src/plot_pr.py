"""Gera a curva precisão--recall anotada da reprodução (a figura do artigo).

Marca na curva o ponto de melhor F1, o ponto da regra de decisão KDE + p-valor
(no nível alpha) e o alvo reportado no artigo (0,98/0,97), além da linha de base
(prevalência de anômalos). A regra KDE + p-valor equivale a um limiar no score;
seu ponto de operação é obtido por bisseção na CDF do KDE ajustado aos scores
normais de validação.

Uso (dentro da imagem fixada, como o evaluate.py):
    python src/plot_pr.py results/rnvp_testbed.csv \
        --normal-scores results/vrnvp_testbed.csv --out paper/pr_curve.pdf
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy.stats import gaussian_kde
from scipy.special import ndtr
from sklearn.metrics import average_precision_score, precision_recall_curve

PAPER = (0.97, 0.98)  # (recall, precisao) reportado na Tabela II do artigo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="CSV pontuado (id,label,score)")
    ap.add_argument("--normal-scores", required=True,
                    help="CSV de scores de validacao (vrnvp_*.csv) que ajusta o KDE")
    ap.add_argument("--alpha", type=float, default=0.001)
    ap.add_argument("--out", default="pr_curve.pdf", help="PDF de saida")
    ap.add_argument("--preview", default=None, help="PNG opcional para conferencia de layout")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    y = df["label"].to_numpy()
    s = df["score"].to_numpy()
    val = pd.read_csv(args.normal_scores)["score"].to_numpy()

    prec, rec, _ = precision_recall_curve(y, -s)
    auprc = average_precision_score(y, -s)
    f1 = 2 * prec * rec / (prec + rec + 1e-12)
    b = int(np.nanargmax(f1))
    bf_P, bf_R = prec[b], rec[b]

    # ponto KDE + p-valor: limiar s* onde CDF(s*)=alpha, por bisseção (regra monotona)
    kde = gaussian_kde(val)
    std = float(np.sqrt(kde.covariance.ravel()[0]))
    lo, hi = float(s.min()) - 1, float(s.max()) + 1
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if float(ndtr((mid - val) / std).mean()) < args.alpha:
            lo = mid
        else:
            hi = mid
    p = s < lo
    tp = int((p & (y == 1)).sum()); fp = int((p & (y == 0)).sum()); fn = int((~p & (y == 1)).sum())
    kde_P, kde_R = tp / (tp + fp), tp / (tp + fn)
    prev = float((y == 1).mean())

    OUR, PAP, INK, MUTED = "#2166ac", "#b2182b", "#222222", "#8a8a8a"
    plt.rcParams.update({"font.family": "serif", "font.size": 9,
                         "axes.edgecolor": "#9a9a9a", "axes.linewidth": 0.6})
    c = lambda x: ("%.3f" % x).replace(".", ",")
    arr = lambda color: dict(arrowstyle="->", color=color, lw=0.6, shrinkA=1, shrinkB=3)

    fig, ax = plt.subplots(figsize=(3.35, 2.6))
    ax.grid(True, color="#ededed", lw=0.6, zorder=0)
    ax.plot(rec, prec, color=OUR, lw=1.7, zorder=3)
    ax.axhline(prev, color=MUTED, lw=0.8, ls=":", zorder=1)
    ax.text(0.015, prev + 0.02, "linha de base = " + c(prev), color=MUTED, fontsize=6.5)
    ax.scatter([kde_R], [kde_P], marker="s", s=34, color=OUR, edgecolor="white", lw=0.9, zorder=5)
    ax.annotate("KDE+p ($\\alpha$=%s)\n(%s/%s)" % (c(args.alpha), c(kde_P), c(kde_R)),
                (kde_R, kde_P), xytext=(0.06, 0.62), fontsize=6.8, ha="left", va="center",
                color=INK, arrowprops=arr(INK))
    ax.scatter([bf_R], [bf_P], marker="o", s=40, color=OUR, edgecolor="white", lw=0.9, zorder=5)
    ax.annotate("melhor-F1\n(%s/%s)" % (c(bf_P), c(bf_R)), (bf_R, bf_P), xytext=(0.44, 0.44),
                fontsize=6.8, ha="left", va="center", color=INK, arrowprops=arr(INK))
    ax.scatter([PAPER[0]], [PAPER[1]], marker="*", s=95, color=PAP, edgecolor="white", lw=0.7, zorder=6)
    ax.annotate("Artigo\n(0,98/0,97)", (PAPER[0], PAPER[1]), xytext=(0.72, 0.66),
                fontsize=6.8, ha="left", va="center", color=PAP, arrowprops=arr(PAP))
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.06)
    ax.set_xlabel("Recall"); ax.set_ylabel("Precisão")
    fmt = FuncFormatter(lambda v, _: ("%.1f" % v).replace(".", ","))
    ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    ax.text(0.015, 0.06, "AUPRC = " + c(auprc), fontsize=8, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.3)
    fig.savefig(args.out)
    if args.preview:
        fig.savefig(args.preview, dpi=200)
    print("saved %s | best-F1 %.3f/%.3f | KDE+p %.3f/%.3f | AUPRC %.3f"
          % (args.out, bf_P, bf_R, kde_P, kde_R, auprc))


if __name__ == "__main__":
    main()
