"""
Task B Ranking Evaluation v4 — Full pool + Star Alignment + Recent-Weighted User Vector
No category filtering (target business often outside user's usual categories).
Run: python core/evaluate_ranking_v4.py
"""
import os, sys, json, math
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'reviews_sample.csv')
BIZ_JSON   = os.path.join(os.path.dirname(__file__), '..', 'data', 'yelp_academic_dataset_business.json')
N_USERS    = 20
MIN_REVIEWS = 6
K          = 10
MODEL_NAME = 'all-MiniLM-L6-v2'

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
    print("  The Honest Friend — Task B Ranking v4")
    print("  (Full pool + Star Alignment + Recent-Weighted Vector)")
    print("="*60)

    df = pd.read_csv(SAMPLE_CSV)
    print(f"\nLoaded {len(df)} reviews, {df['business_id'].nunique()} businesses")

    print("Loading business metadata...")
    biz_stars = {}
    with open(BIZ_JSON) as f:
        for line in f:
            b = json.loads(line)
            biz_stars[b['business_id']] = b.get('stars', 3.0)

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
    # Stack into matrix for fast batch dot product
    biz_matrix  = np.array(biz_embeddings)   # shape (4744, 384)
    biz_id_list = all_businesses

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

        if target_biz not in {b: i for i, b in enumerate(biz_id_list)}:
            continue

        avg_rating = history['stars'].mean()
        seen       = set(history['business_id'])

        # Candidate mask — everything not yet reviewed
        candidate_mask = [b not in seen for b in biz_id_list]
        candidate_bibs = [b for b, m in zip(biz_id_list, candidate_mask) if m]
        candidate_embs = biz_matrix[np.array(candidate_mask)]

        if target_biz not in candidate_bibs:
            candidate_bibs.append(target_biz)
            target_emb = biz_matrix[biz_id_list.index(target_biz)]
            candidate_embs = np.vstack([candidate_embs, target_emb])

        # Recent-weighted user vector: last 10 reviews, linearly increasing weight
        recent_history = history.tail(10)
        texts   = recent_history['text'].tolist()
        weights = np.linspace(0.5, 1.0, len(texts))
        repeated = []
        for t, w in zip(texts, weights):
            repeated.extend([t] * max(1, int(w * 3)))
        user_vector = model.encode(' '.join(repeated), normalize_embeddings=True)

        # Cosine similarity (fast matrix multiply)
        cos_scores = candidate_embs @ user_vector  # shape (N,)

        # Star alignment: businesses whose avg rating matches user's avg get boosted
        star_arr       = np.array([biz_stars.get(b, 3.0) for b in candidate_bibs])
        star_alignment = 1.0 - np.abs(star_arr - avg_rating) / 4.0  # 0→1

        # High-rated filter bonus: slightly boost businesses rated ≥ 4.0
        quality_bonus = (star_arr >= 4.0).astype(float) * 0.05

        # Final score
        final_scores = (0.70 * cos_scores +
                        0.20 * star_alignment +
                        0.10 * quality_bonus)

        ranked_indices = np.argsort(final_scores)[::-1]
        ranked_bibs    = [candidate_bibs[i] for i in ranked_indices]
        relevances     = [1 if b == target_biz else 0 for b in ranked_bibs]

        ndcg = ndcg_at_k(relevances, K)
        hit  = hit_rate_at_k(relevances, K)
        rank = next((i+1 for i, b in enumerate(ranked_bibs) if b == target_biz), len(candidate_bibs))

        ndcg_scores.append(ndcg)
        hit_scores.append(hit)
        results.append({
            'user_id':      uid[:12],
            'target_rank':  rank,
            'hit@10':       int(hit),
            'ndcg@10':      round(ndcg, 4),
            'n_candidates': len(candidate_bibs),
            'avg_rating':   round(float(avg_rating), 2),
        })

    avg_ndcg   = sum(ndcg_scores) / len(ndcg_scores)
    avg_hit    = sum(hit_scores)  / len(hit_scores)
    avg_pool   = sum(r['n_candidates'] for r in results) / len(results)
    random_bl  = K / avg_pool

    print("\n" + "="*60)
    print("  TASK B RANKING RESULTS v4")
    print("="*60)
    print(f"\n  Users evaluated   : {len(results)}")
    print(f"  NDCG@10           : {avg_ndcg:.4f}")
    print(f"  Hit Rate@10       : {avg_hit:.4f}  ({avg_hit*100:.1f}%)")
    print(f"  Avg candidate pool: {avg_pool:.0f}")
    print(f"  Random baseline   : {random_bl:.4f}")
    print(f"  Lift over random  : {(avg_hit/random_bl):.1f}x\n")

    print(f"  {'User':<14} {'Pool':>6} {'Rank':>6} {'Hit@10':>8} {'NDCG@10':>9} {'AvgRating':>10}")
    print(f"  {'-'*14} {'-'*6} {'-'*6} {'-'*8} {'-'*9} {'-'*10}")
    for r in results:
        print(f"  {r['user_id']:<14} {r['n_candidates']:>6} {r['target_rank']:>6} {r['hit@10']:>8} {r['ndcg@10']:>9.4f} {r['avg_rating']:>10.1f}")

    print("\n" + "="*60)
    print(f"  NDCG@10: {avg_ndcg:.4f}  |  Hit Rate@10: {avg_hit:.4f}")
    print(f"  Lift over random baseline: {(avg_hit/random_bl):.1f}x")
    print("="*60 + "\n")

    out = {
        'version':            'v4_full_pool_star_aligned',
        'n_users':            len(results),
        'ndcg_at_10':         round(avg_ndcg, 4),
        'hit_rate_at_10':     round(avg_hit, 4),
        'avg_candidate_pool': round(avg_pool),
        'random_baseline':    round(random_bl, 4),
        'lift_over_random':   round(avg_hit / random_bl, 2) if random_bl > 0 else 0,
        'k':                  K,
        'per_user':           results,
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'paper', 'eval_ranking_results.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"  Results saved to paper/eval_ranking_results.json\n")

if __name__ == '__main__':
    run_evaluation()
