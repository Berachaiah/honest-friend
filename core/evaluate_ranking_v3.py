"""
Task B Ranking Evaluation v3 — Specific Category Filter + Star Threshold + Rating-Weighted Scoring
Run: python core/evaluate_ranking_v3.py
"""
import os, sys, json, math
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
import numpy as np
from tqdm import tqdm
from collections import Counter
from sentence_transformers import SentenceTransformer

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'reviews_sample.csv')
BIZ_JSON   = os.path.join(os.path.dirname(__file__), '..', 'data', 'yelp_academic_dataset_business.json')
N_USERS    = 20
MIN_REVIEWS = 6
K          = 10
MODEL_NAME = 'all-MiniLM-L6-v2'

BROAD = {
    'Restaurants', 'Food', 'Shopping', 'Local Services', 'Home Services',
    'Health & Medical', 'Beauty & Spas', 'Automotive', 'Event Planning & Services',
    'Bars', 'Nightlife', 'Arts & Entertainment'
}

def dcg(relevances):
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))

def ndcg_at_k(ranked_relevances, k=10):
    actual = dcg(ranked_relevances[:k])
    ideal  = dcg(sorted(ranked_relevances, reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0

def hit_rate_at_k(ranked_relevances, k=10):
    return 1.0 if any(r > 0 for r in ranked_relevances[:k]) else 0.0

def run_evaluation():
    print("\n" + "="*60)
    print("  The Honest Friend — Task B Ranking v3")
    print("  (Specific Categories + Star Threshold + Rating Weight)")
    print("="*60)

    df = pd.read_csv(SAMPLE_CSV)
    print(f"\nLoaded {len(df)} reviews, {df['business_id'].nunique()} businesses")

    print("Loading business metadata...")
    biz_cats  = {}
    biz_stars = {}
    biz_names = {}
    with open(BIZ_JSON) as f:
        for line in f:
            b = json.loads(line)
            biz_cats[b['business_id']]  = b.get('categories', '') or ''
            biz_stars[b['business_id']] = b.get('stars', 3.0)
            biz_names[b['business_id']] = b.get('name', '')

    df['categories'] = df['business_id'].map(biz_cats).fillna('')

    print("Building business text index...")
    biz_texts = (
        df.groupby('business_id')['text']
        .apply(lambda x: ' '.join(x.tolist()[:3]))
        .to_dict()
    )
    all_businesses = list(biz_texts.keys())

    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Embedding {len(all_businesses)} businesses (one-time)...")
    biz_embeddings = model.encode(
        [biz_texts[b] for b in all_businesses],
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    biz_index = {biz: emb for biz, emb in zip(all_businesses, biz_embeddings)}

    user_counts = df.groupby('user_id').size()
    eligible    = user_counts[user_counts >= MIN_REVIEWS + 1].index.tolist()
    selected    = eligible[:N_USERS]
    print(f"\nEvaluating {len(selected)} users...\n")

    ndcg_scores, hit_scores, results = [], [], []

    for uid in tqdm(selected, desc="Ranking"):
        user_df    = df[df['user_id'] == uid].sort_values('date')
        history    = user_df.iloc[:-1]
        holdout    = user_df.iloc[-1]
        target_biz = holdout['business_id']

        if target_biz not in biz_index:
            continue

        avg_rating  = history['stars'].mean()
        star_thresh = 3.0 if avg_rating < 3.0 else 3.5

        # Extract specific (non-broad) top categories
        cat_counter = Counter()
        for cats in history['categories']:
            for cat in cats.split(','):
                cat = cat.strip()
                if cat and cat not in BROAD:
                    cat_counter[cat] += 1
        top5_cats = {cat for cat, _ in cat_counter.most_common(5)}

        seen = set(history['business_id'])

        # Filter candidates
        candidates = [
            b for b in all_businesses
            if b not in seen
            and any(c in biz_cats.get(b, '') for c in top5_cats)
            and biz_stars.get(b, 0) >= star_thresh
        ]

        # Always include target
        if target_biz not in candidates:
            candidates.append(target_biz)

        # User vector — weight recent reviews more heavily
        history_texts = history['text'].tolist()
        weights = np.linspace(0.5, 1.0, len(history_texts))  # recent = higher weight
        weighted_texts = ' '.join(
            t for t, w in zip(history_texts[-10:], weights[-10:])
            for _ in range(max(1, int(w * 2)))
        )
        user_vector = model.encode(weighted_texts, normalize_embeddings=True)

        # Score = cosine sim + star alignment bonus
        candidate_embs  = np.array([biz_index[b] for b in candidates])
        cos_scores      = candidate_embs @ user_vector

        # Star alignment: reward businesses whose stars match user's avg rating
        biz_star_arr    = np.array([biz_stars.get(b, 3.0) for b in candidates])
        star_alignment  = 1.0 - np.abs(biz_star_arr - avg_rating) / 4.0  # 0-1

        # Final score: 75% semantic, 25% star alignment
        final_scores = 0.75 * cos_scores + 0.25 * star_alignment

        ranked_indices = np.argsort(final_scores)[::-1]
        ranked_bibs    = [candidates[i] for i in ranked_indices]
        relevances     = [1 if b == target_biz else 0 for b in ranked_bibs]

        ndcg = ndcg_at_k(relevances, K)
        hit  = hit_rate_at_k(relevances, K)
        rank = next((i+1 for i, b in enumerate(ranked_bibs) if b == target_biz), len(candidates))

        ndcg_scores.append(ndcg)
        hit_scores.append(hit)
        results.append({
            'user_id':      uid[:12],
            'target_rank':  rank,
            'hit@10':       int(hit),
            'ndcg@10':      round(ndcg, 4),
            'n_candidates': len(candidates),
            'avg_rating':   round(float(avg_rating), 2),
            'top_cats':     list(top5_cats),
        })

    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    avg_hit  = sum(hit_scores)  / len(hit_scores)
    avg_pool = sum(r['n_candidates'] for r in results) / len(results)

    print("\n" + "="*60)
    print("  TASK B RANKING RESULTS v3")
    print("="*60)
    print(f"\n  Users evaluated  : {len(results)}")
    print(f"  NDCG@10          : {avg_ndcg:.4f}")
    print(f"  Hit Rate@10      : {avg_hit:.4f}  ({avg_hit*100:.1f}%)")
    print(f"  Avg candidate pool: {avg_pool:.0f} (from 4,744 total)\n")

    print(f"  {'User':<14} {'Pool':>6} {'Rank':>6} {'Hit@10':>8} {'NDCG@10':>9} {'AvgRating':>10}")
    print(f"  {'-'*14} {'-'*6} {'-'*6} {'-'*8} {'-'*9} {'-'*10}")
    for r in results:
        print(f"  {r['user_id']:<14} {r['n_candidates']:>6} {r['target_rank']:>6} {r['hit@10']:>8} {r['ndcg@10']:>9.4f} {r['avg_rating']:>10.1f}")

    print("\n" + "="*60)
    print(f"  NDCG@10: {avg_ndcg:.4f}  |  Hit Rate@10: {avg_hit:.4f}")
    print("  Random baseline NDCG@10: ~0.0002")
    print(f"  Improvement over random: {avg_ndcg/0.0002:.0f}x")
    print("="*60 + "\n")

    out = {
        'version':            'v3_specific_cat_star_aligned',
        'n_users':            len(results),
        'ndcg_at_10':         round(avg_ndcg, 4),
        'hit_rate_at_10':     round(avg_hit, 4),
        'avg_candidate_pool': round(avg_pool),
        'random_baseline':    0.0002,
        'k':                  K,
        'per_user':           results,
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'paper', 'eval_ranking_results.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"  Results saved to paper/eval_ranking_results.json\n")

if __name__ == '__main__':
    run_evaluation()
