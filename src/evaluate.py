"""Reconstruct TraceAnomaly's detection metrics from its scored-trace output.

The published artifact (``traceanomaly.main``) only writes per-trace CSVs:
  * ``rnvp_<name>.csv``  -- test traces, columns ``id,label,score``
    (label 0=normal, 1=anomalous; score = log p(x)/dim, so an *anomalous* trace
    has a *low* score).
  * ``vrnvp_<name>.csv`` -- validation traces, column ``score`` only (a held-out
    10% split of the normal training traces).
It stops at scores: it computes NO precision/recall and applies NO decision rule.

This script rebuilds the two things the artifact leaves out, one per research
question:

  RQ1 -- reference operating curve. Sweep every threshold on ``-score`` and report
         AUPRC and the best-F1 point. The threshold is chosen knowing the labels,
         so this is a label-aware *oracle* point: it upper-bounds what any single
         threshold could achieve and characterises how separable the scores are.

  RQ2 -- the paper's actual decision step, which the released code omits: a KDE
         over the NORMAL traces' scores followed by a one-sided p-value test at
         significance ``alpha`` (0.001 in the paper). We reimplement it from the
         paper's text plus the artifact's own outputs, and report P/R/F1 under it.
         See ``kde_pvalue_decision`` for the three points the paper underspecifies.

Usage:
    # RQ1 only (reference curve):
    python src/evaluate.py results/rnvp_testbed.csv
    # RQ1 + RQ2 (fit the KDE on the validation scores, decide at alpha=0.001):
    python src/evaluate.py results/rnvp_testbed.csv \
        --normal-scores results/vrnvp_testbed.csv --plot results/pr.png
"""
import argparse
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.metrics import average_precision_score, precision_recall_curve


def reference_curve(labels: np.ndarray, scores: np.ndarray) -> dict:
    """RQ1 reference operating curve: AUPRC and the label-aware best-F1 point.

    Negates the score so that "higher = more anomalous", sweeps all thresholds via
    the precision-recall curve, and returns the best-F1 operating point. Because
    the threshold is picked knowing the labels, this is an oracle upper bound, not
    the paper's rule -- it is the backdrop against which the RQ2 decision is judged.
    """
    anomaly_score = -scores
    precision, recall, _thresholds = precision_recall_curve(labels, anomaly_score)
    f1 = 2 * precision * recall / (precision + recall + 1e-12)
    best = int(np.nanargmax(f1))
    return {
        "auprc": float(average_precision_score(labels, anomaly_score)),
        "best_f1": float(f1[best]),
        "precision_at_best_f1": float(precision[best]),
        "recall_at_best_f1": float(recall[best]),
        "curve": (precision, recall),
    }


def kde_pvalue_decision(
    test_scores: np.ndarray, normal_scores: np.ndarray, alpha: float
) -> Tuple[np.ndarray, np.ndarray]:
    """RQ2: reimplementation of the paper's (code-absent) decision step.

    The paper turns a per-trace log-likelihood score into a normal/anomalous
    verdict via a KDE over the normal traces' scores followed by a p-value test at
    significance ``alpha`` (0.001). Three points are underspecified in the paper
    and fixed here by the most natural reading -- each is a threat to validity:

      (a) WHICH normal set fits the KDE. We use the artifact's validation scores
          (``vrnvp_*.csv``), a held-out 10% split of the normal training traces.
          Fitting on the *test* normals would peek at the evaluation set.
      (b) BANDWIDTH. Not given by the paper; we take scipy's default (Scott's
          rule) and do not tune it.
      (c) THE STATISTIC. An anomaly has a LOW score, so the test is one-sided on
          the LEFT tail: p(s) = P(X <= s) under the fitted KDE = the density mass
          to the left of the trace's score. Flag anomalous when p(s) < alpha.

    Returns ``(pvalues, predictions)``; predictions is a boolean array, True=anomaly.
    """
    kde = gaussian_kde(normal_scores)  # Scott bandwidth (scipy default) -- decision (b)
    # Left-tail p-value per trace: mass of the normal-score density below s -- decision (c).
    pvalues = np.array([kde.integrate_box_1d(-np.inf, s) for s in test_scores])
    predictions = pvalues < alpha
    return pvalues, predictions


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("csv", help="Scored test CSV (id,label,score) from traceanomaly.main")
    ap.add_argument(
        "--normal-scores", default=None,
        help="Validation-scores CSV (vrnvp_*.csv, column 'score') to fit the KDE "
             "for the RQ2 decision. If omitted, only the RQ1 reference curve is reported.",
    )
    ap.add_argument(
        "--alpha", type=float, default=0.001,
        help="Significance level for the p-value decision (paper: 0.001)",
    )
    ap.add_argument("--plot", default=None, help="Optional path to save the PR curve PNG")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    if not {"label", "score"}.issubset(df.columns):
        raise ValueError(f"{args.csv} must have columns id,label,score; got {list(df.columns)}")
    labels = df["label"].to_numpy()
    scores = df["score"].to_numpy()

    ref = reference_curve(labels, scores)
    print(f"file:                 {args.csv}")
    print(f"traces:               {len(df)} "
          f"({int((labels == 0).sum())} normal, {int((labels == 1).sum())} anomalous)")
    print("--- RQ1 reference operating curve (label-aware oracle, best achievable) ---")
    print(f"AUPRC:                {ref['auprc']:.4f}")
    print(f"best-F1:              {ref['best_f1']:.4f}  "
          f"(P={ref['precision_at_best_f1']:.4f}, R={ref['recall_at_best_f1']:.4f})")

    if args.normal_scores:
        normal_scores = pd.read_csv(args.normal_scores)["score"].to_numpy()
        _pvalues, preds = kde_pvalue_decision(scores, normal_scores, args.alpha)
        # Confusion counts, then P/R/F1 by definition (kept explicit for the paper).
        tp = int((preds & (labels == 1)).sum())
        fp = int((preds & (labels == 0)).sum())
        fn = int((~preds & (labels == 1)).sum())
        tn = int((~preds & (labels == 0)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        print(f"--- RQ2 decision: KDE(normal scores) + left-tail p-value, alpha={args.alpha} ---")
        print(f"KDE fit on:           {len(normal_scores)} normal validation scores (Scott bandwidth)")
        print(f"flagged anomalous:    {int(preds.sum())} / {len(preds)}")
        print(f"precision:            {precision:.4f}")
        print(f"recall:               {recall:.4f}")
        print(f"F1:                   {f1:.4f}")
        print(f"confusion:            TP={tp} FP={fp} FN={fn} TN={tn}")
    else:
        print("(RQ2 skipped: pass --normal-scores vrnvp_*.csv to run the KDE + p-value decision)")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        precision_c, recall_c = ref["curve"]
        plt.figure(figsize=(4, 3))
        plt.plot(recall_c, precision_c)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title(f"PR curve (AUPRC={ref['auprc']:.3f})")
        plt.tight_layout()
        plt.savefig(args.plot, dpi=150)
        print(f"saved PR curve -> {args.plot}")


if __name__ == "__main__":
    main()
