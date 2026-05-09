"""
Loads and preprocesses Yelp review data into a working sample.
Run directly: python core/data_loader.py
"""
import json
import os
import pandas as pd
from tqdm import tqdm
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
SAMPLE_DIR = DATA_DIR / 'sample'


def load_sample(review_path: str, n_users: int = 100, reviews_per_user: int = 20) -> dict:
    """
    Load a manageable sample from the full Yelp JSON dataset.
    Stops reading as soon as n_users qualified users are found.
    Returns dict of {user_id: [list of review dicts]}
    """
    print(f"Loading reviews from {review_path}...")
    user_reviews: dict = {}
    qualified: set = set()

    with open(review_path, 'r') as f:
        for line in tqdm(f, desc="Reading reviews"):
            review = json.loads(line)
            uid = review['user_id']

            if uid not in user_reviews:
                user_reviews[uid] = []

            user_reviews[uid].append({
                'review_id': review['review_id'],
                'user_id': uid,
                'business_id': review['business_id'],
                'stars': review['stars'],
                'text': review['text'],
                'date': review['date'],
                'useful': review['useful'],
                'funny': review['funny'],
                'cool': review['cool'],
            })

            # Track when a user crosses the threshold
            if len(user_reviews[uid]) == reviews_per_user:
                qualified.add(uid)

            # Stop early once we have enough qualified users
            if len(qualified) >= n_users:
                print(f"\nFound {n_users} qualified users — stopping early.")
                break

    sampled = {uid: user_reviews[uid] for uid in qualified}
    print(f"Loaded {len(sampled)} users with {reviews_per_user}+ reviews each.")
    return sampled


def load_businesses(business_path: str) -> dict:
    """Load business metadata keyed by business_id."""
    businesses = {}
    with open(business_path, 'r') as f:
        for line in f:
            b = json.loads(line)
            businesses[b['business_id']] = {
                'name': b['name'],
                'city': b['city'],
                'state': b['state'],
                'stars': b['stars'],
                'categories': b.get('categories', ''),
                'attributes': b.get('attributes', {}),
            }
    return businesses


def save_sample(sample_users: dict, output_path: str = None) -> pd.DataFrame:
    """Flatten sample dict and save to CSV, with progress."""
    output_path = output_path or str(SAMPLE_DIR)
    os.makedirs(output_path, exist_ok=True)

    print("Building rows...")
    rows = []
    for i, (uid, reviews) in enumerate(tqdm(sample_users.items(), desc="Processing users")):
        for r in reviews:
            rows.append(r)

    print(f"Writing {len(rows)} rows to CSV...")
    df = pd.DataFrame(rows)
    out_file = os.path.join(output_path, 'reviews_sample.csv')
    df.to_csv(out_file, index=False)
    print(f"Done! Saved {len(df)} reviews to {out_file}")
    print(f"Shape: {df.shape}")
    return df


def load_saved_sample(path: str = None) -> pd.DataFrame:
    """Load the pre-saved CSV sample (fast path for inference)."""
    path = path or str(SAMPLE_DIR / 'reviews_sample.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No sample found at {path}. "
            "Run: python core/data_loader.py to generate it first."
        )
    return pd.read_csv(path)


def get_user_reviews(df: pd.DataFrame, user_id: str) -> pd.DataFrame:
    """Return all reviews for a specific user."""
    return df[df['user_id'] == user_id].sort_values('date')


if __name__ == '__main__':
    review_path = DATA_DIR / 'yelp_academic_dataset_review.json'
    if not review_path.exists():
        print(f"ERROR: Dataset not found at {review_path}")
        print("Download from https://www.yelp.com/dataset and extract to data/")
    else:
        users = load_sample(str(review_path), n_users=500)
        df = save_sample(users)
        print(df.head())
        print(f"Shape: {df.shape}")