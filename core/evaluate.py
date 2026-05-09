"""
Evaluation script — Task A behavioural fidelity metrics.
Computes RMSE (rating accuracy) and ROUGE-L (review text quality).

Run: python core/evaluate.py
"""
import os, sys, json, math
import django

# ── Django setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
import numpy as np
from tqdm import tqdm
from rouge_score import rouge_scorer

from agents.persona_builder import build_persona
from agents.review_agent import generate_review

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_CSV   = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'reviews_sample.csv')
N_USERS      = 20      # number of users to evaluate
MIN_REVIEWS  = 6       # minimum reviews per user (need history + test item)
HOLDOUT_N    = 1       # hold out last N reviews per user as ground truth

def rmse(actual, predicted):
    return math.sqrt(sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual))

def run_evaluation():
    print("\n" + "="*60)
    print("  The Honest Friend — Task A Evaluation")
    print("="*60)

    # ── Load data ──────────────────────────────────────────────────────────────
    if not os.path.exists(SAMPLE_CSV):
        print(f"\nERROR: Sample CSV not found at {SAMPLE_CSV}")
        print("Run: python core/data_loader.py first")
        sys.exit(1)

    df = pd.read_csv(SAMPLE_CSV)
    print(f"\nLoaded {len(df)} reviews from {df['user_id'].nunique()} users")

    # ── Select users with enough reviews ──────────────────────────────────────
    user_counts = df.groupby('user_id').size()
    eligible    = user_counts[user_counts >= MIN_REVIEWS + HOLDOUT_N].index.tolist()
    selected    = eligible[:N_USERS]
    print(f"Evaluating {len(selected)} users (each with {MIN_REVIEWS}+ history reviews)\n")

    scorer      = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    actual_ratings, predicted_ratings = [], []
    rouge_scores = []
    results      = []

    for uid in tqdm(selected, desc="Evaluating users"):
        user_df  = df[df['user_id'] == uid].sort_values('date')
        history  = user_df.iloc[:-HOLDOUT_N]
        holdout  = user_df.iloc[-HOLDOUT_N:]

        # Build reviews list for persona
        reviews = [
            {'stars': int(r['stars']), 'text': str(r['text']), 'user_id': uid}
            for _, r in history.iterrows()
        ]

        # Ground truth
        gt_rating = float(holdout.iloc[0]['stars'])
        gt_text   = str(holdout.iloc[0]['text'])

        # Build persona
        persona = build_persona(reviews)

        # Generate review for the held-out item
        product = {
            'name':        'Held-out item',
            'category':    'General',
            'description': gt_text[:200],   # use actual text as description signal
            'avg_price':   'Unknown',
        }

        try:
            result        = generate_review(persona, product)
            pred_rating   = float(result.get('rating', 3.0))
            pred_text     = str(result.get('review', ''))

            rouge_result  = scorer.score(gt_text, pred_text)
            rouge_l       = rouge_result['rougeL'].fmeasure

            actual_ratings.append(gt_rating)
            predicted_ratings.append(pred_rating)
            rouge_scores.append(rouge_l)

            results.append({
                'user_id':      uid[:12],
                'actual':       gt_rating,
                'predicted':    round(pred_rating, 1),
                'delta':        round(abs(gt_rating - pred_rating), 1),
                'rouge_l':      round(rouge_l, 3),
                'rating_style': persona.get('rating_style', 'unknown'),
            })

        except Exception as e:
            print(f"  ⚠ Skipped {uid[:12]}: {e}")
            continue

    # ── Results ────────────────────────────────────────────────────────────────
    if not results:
        print("No results — check your GROQ_API_KEY in .env")
        return

    final_rmse   = rmse(actual_ratings, predicted_ratings)
    final_rouge  = sum(rouge_scores) / len(rouge_scores)
    avg_delta    = sum(r['delta'] for r in results) / len(results)

    print("\n" + "="*60)
    print("  RESULTS")
    print("="*60)
    print(f"\n  Users evaluated : {len(results)}")
    print(f"  RMSE (ratings)  : {final_rmse:.4f}  (lower is better, <1.0 is good)")
    print(f"  Avg ROUGE-L     : {final_rouge:.4f}  (higher is better)")
    print(f"  Avg rating delta: {avg_delta:.2f} stars\n")

    print(f"  {'User':<14} {'Actual':>7} {'Pred':>6} {'Delta':>6} {'ROUGE-L':>8} {'Style':<10}")
    print(f"  {'-'*14} {'-'*7} {'-'*6} {'-'*6} {'-'*8} {'-'*10}")
    for r in results:
        print(f"  {r['user_id']:<14} {r['actual']:>7.1f} {r['predicted']:>6.1f} {r['delta']:>6.1f} {r['rouge_l']:>8.3f} {r['rating_style']:<10}")

    print("\n" + "="*60)
    print(f"  RMSE: {final_rmse:.4f}  |  ROUGE-L: {final_rouge:.4f}")
    print("="*60 + "\n")

    # ── Save to file ───────────────────────────────────────────────────────────
    out = {
        'n_users':    len(results),
        'rmse':       round(final_rmse, 4),
        'rouge_l':    round(final_rouge, 4),
        'avg_delta':  round(avg_delta, 4),
        'per_user':   results,
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'paper', 'eval_results.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"  Results saved to paper/eval_results.json\n")

if __name__ == '__main__':
    run_evaluation()
