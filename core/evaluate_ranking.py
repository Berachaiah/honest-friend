"""
Task B Ranking Evaluation — NDCG@10 and Hit Rate@10
Uses embedding-based ranking: persona excerpts vs candidate business reviews.
Run: python core/evaluate_ranking.py
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

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_CSV  = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'reviews_sample.csv')
N_USERS     = 20
MIN_REVIEWS = 6
K           = 10   # NDCG@10, Hit Rate@10
MODEL_NAME  = 'all-MiniLM-L6-v2'

def dcg(relevances):
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))

def ndcg_at_k(ranked_relevances, k=10):
    actual = dcg(ranked_relevances[:k])
    ideal  = dcg(sorted(ranked_relevances, reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0

def hit_rate_at_k(ranked_relevances, k=10):
    return 1.0 if any(r > 0 for r in ranked_relevances[:k]) else 0.0

def run_ranking_evaluation():
    print("\n" + "="*60)
    print("  The Honest Friend — Task B Ranking Evaluation")
    print("="*60)

    df = pd.read_csv(SAMPLE_CSV)
    print(f"\nLoaded {len(df)} reviews, {df['business_id'].nunique()} businesses")

    # Build business → avg review text lookup
    print("Building business text index...")
    biz_texts = (
        df.groupby('business_id')['text']
        .apply(lambda x: ' '.join(x.tolist()[:3]))  # use up to 3 reviews per business
        .to_dict()
    )
    all_businesses = list(biz_texts.keys())

    # Load embedding model
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Embed all business texts once
    print(f"Embedding {len(all_businesses)} businesses (one-time)...")
    biz_embeddings = model.encode(
        [biz_texts[b] for b in all_businesses],
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    biz_index = {biz: emb for biz, emb in zip(all_businesses, biz_embeddings)}

    # Select evaluation users
    user_counts  = df.groupby('user_id').size()
    eligible     = user_counts[user_counts >= MIN_REVIEWS + 1].index.tolist()
    selected     = eligible[:N_USERS]
    print(f"\nEvaluating {len(selected)} users...\n")

    ndcg_scores = []
    hit_scores  = []
    results     = []

    for uid in tqdm(selected, desc="Ranking"):
        user_df   = df[df['user_id'] == uid].sort_values('date')
        history   = user_df.iloc[:-1]
        holdout   = user_df.iloc[-1]
        target_biz = holdout['business_id']

        # Skip if target business not in index
        if target_biz not in biz_index:
            continue

        # Candidate businesses = all businesses user hasn't reviewed
        seen       = set(history['business_id'])
        candidates = [b for b in all_businesses if b not in seen]

        if target_biz not in candidates:
            candidates.append(target_biz)

        # User vector = mean embedding of their history review texts
        user_texts  = history['text'].tolist()[:5]
        user_vector = model.encode(
            ' '.join(user_texts),
            normalize_embeddings=True
        )

        # Score all candidates by cosine similarity
        candidate_embs = np.array([biz_index[b] for b in candidates])
        scores         = candidate_embs @ user_vector  # cosine sim (normalized)

        # Rank
        ranked_indices = np.argsort(scores)[::-1]
        ranked_bibs    = [candidates[i] for i in ranked_indices]

        # Relevance: 1 if target business, 0 otherwise
        relevances = [1 if b == target_biz else 0 for b in ranked_bibs]

        ndcg = ndcg_at_k(relevances, K)
        hit  = hit_rate_at_k(relevances, K)
        rank = next((i+1 for i, b in enumerate(ranked_bibs) if b == target_biz), len(candidates))

        ndcg_scores.append(ndcg)
        hit_scores.append(hit)
        results.append({
            'user_id':   uid[:12],
            'target_rank': rank,
            'hit@10':    int(hit),
            'ndcg@10':   round(ndcg, 4),
            'n_candidates': len(candidates),
        })

    # ── Results ────────────────────────────────────────────────────────────────
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    avg_hit  = sum(hit_scores)  / len(hit_scores)

    print("\n" + "="*60)
    print("  TASK B RANKING RESULTS")
    print("="*60)
    print(f"\n  Users evaluated : {len(results)}")
    print(f"  NDCG@10         : {avg_ndcg:.4f}")
    print(f"  Hit Rate@10     : {avg_hit:.4f}  ({avg_hit*100:.1f}% of users had target in top 10)")
    print(f"  Candidate pool  : ~{results[0]['n_candidates'] if results else 0} businesses per user\n")

    print(f"  {'User':<14} {'Rank':>6} {'Hit@10':>8} {'NDCG@10':>9}")
    print(f"  {'-'*14} {'-'*6} {'-'*8} {'-'*9}")
    for r in results:
        print(f"  {r['user_id']:<14} {r['target_rank']:>6} {r['hit@10']:>8} {r['ndcg@10']:>9.4f}")

    print("\n" + "="*60)
    print(f"  NDCG@10: {avg_ndcg:.4f}  |  Hit Rate@10: {avg_hit:.4f}")
    print("="*60 + "\n")

    # Save results
    out = {
        'n_users':      len(results),
        'ndcg_at_10':   round(avg_ndcg, 4),
        'hit_rate_at_10': round(avg_hit, 4),
        'k':            K,
        'candidate_pool': results[0]['n_candidates'] if results else 0,
        'per_user':     results,
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'paper', 'eval_ranking_results.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"  Results saved to paper/eval_ranking_results.json\n")

if __name__ == '__main__':
    run_ranking_evaluation()
