"""
Task B Ranking Evaluation v5 — clean, debugged version
Run: python core/evaluate_ranking_v5.py
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

SAMPLE_CSV  = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'reviews_sample.csv')
BIZ_JSON    = os.path.join(os.path.dirname(__file__), '..', 'data', 'yelp_academic_dataset_business.json')
N_USERS     = 20
MIN_REVIEWS = 6
K           = 10
MODEL_NAME  = 'all-MiniLM-L6-v2'

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
    print("  The Honest Friend — Task B Ranking v5 (Clean)")
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
    # Fixed ordered list and lookup
    all_biz_ids  = list(biz_texts.keys())
    all_biz_texts = [biz_texts[b] for b in all_biz_ids]
    biz_to_idx   = {b: i for i, b in enumerate(all_biz_ids)}

    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Embedding {len(all_biz_ids)} businesses (one-time)...")
    biz_matrix = model.encode(
        all_biz_texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )  # shape: (4744, 384)

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

        # Skip if target not in our index
        if target_biz not in biz_to_idx:
            continue

        avg_rating  = float(history['stars'].mean())
        seen        = set(history['business_id'])

        # Candidate indices — all businesses not yet reviewed by this user
        candidate_idx = [i for i, b in enumerate(all_biz_ids) if b not in seen]
        target_idx    = biz_to_idx[target_biz]

        # Ensure target is in candidates
        if target_idx not in candidate_idx:
            candidate_idx.append(target_idx)

        candidate_idx  = np.array(candidate_idx)
        candidate_bibs = [all_biz_ids[i] for i in candidate_idx]
        candidate_embs = biz_matrix[candidate_idx]  # shape: (N, 384)

        # User vector: mean of last 10 review embeddings
        recent_texts = history['text'].tail(10).tolist()
        user_vector  = model.encode(
            ' '.join(recent_texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )  # shape: (384,)

        # Cosine similarity
        cos_scores = candidate_embs @ user_vector  # shape: (N,)

        # Star alignment bonus
        star_arr       = np.array([biz_stars.get(b, 3.0) for b in candidate_bibs])
        star_alignment = 1.0 - np.abs(star_arr - avg_rating) / 4.0

        # Final score
        final_scores = 0.80 * cos_scores + 0.20 * star_alignment

        # Rank
        ranked_order = np.argsort(final_scores)[::-1]
        ranked_bibs  = [candidate_bibs[i] for i in ranked_order]

        # Verify target is somewhere in ranked list
        assert target_biz in ranked_bibs, f"BUG: target {target_biz} not in ranked list!"

        relevances = [1 if b == target_biz else 0 for b in ranked_bibs]
        target_pos = next(i+1 for i, b in enumerate(ranked_bibs) if b == target_biz)

        ndcg = ndcg_at_k(relevances, K)
        hit  = hit_rate_at_k(relevances, K)

        ndcg_scores.append(ndcg)
        hit_scores.append(hit)
        results.append({
            'user_id':      uid[:12],
            'target_rank':  target_pos,
            'hit@10':       int(hit),
            'ndcg@10':      round(ndcg, 4),
            'n_candidates': len(candidate_bibs),
            'avg_rating':   round(avg_rating, 2),
        })

    avg_ndcg  = sum(ndcg_scores) / len(ndcg_scores)
    avg_hit   = sum(hit_scores)  / len(hit_scores)
    avg_pool  = sum(r['n_candidates'] for r in results) / len(results)
    random_bl = K / avg_pool

    print("\n" + "="*60)
    print("  TASK B RANKING RESULTS v5")
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
        'version':            'v5_clean_full_pool',
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
