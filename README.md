# 🤝 The Honest Friend

> *An LLM-based behavioural intelligence agent that recommends things the way your most trusted Nigerian friend would — honest, opinionated, and culturally aware.*

**DSN × BCT LLM Agent Challenge — Data & AI Summit Hackathon 3.0**  
Submitted by **Abolaji Berachaiah** · Bells University of Technology · Computer Engineering · 2022/11317

**🌐 Live Demo:** [honest-friend-production.up.railway.app](https://honest-friend-production.up.railway.app)  
**📁 GitHub:** [github.com/Berachaiah/honest-friend](https://github.com/Berachaiah/honest-friend)

---

## What It Does

Most recommendation systems treat users as static profiles. The Honest Friend builds a **dynamic behavioural persona** from a user's review history, then uses that persona to:

- **Task A** — Simulate how the user would review any new product (star rating + written review in their authentic voice)
- **Task B** — Reason through and recommend the next best experience for that specific person, with Nigerian cultural context baked in

The Nigerian cultural layer is not cosmetic — price sensitivity detection, natural Pidgin injection, community trust signals, and occasion-aware context are all engineered into the persona modelling pipeline.

---

## Evaluation Results

| Metric | Value | Brief Criterion |
|---|---|---|
| RMSE (Rating Accuracy) | **0.7704** | Rating Accuracy |
| ROUGE-L | **0.2050** | Review Text Quality |
| BERTScore F1 | **0.8406** | Review Text Quality |
| Persona Contrast Delta | **2.8 stars** | Behavioural Fidelity |
| NDCG@10 | **0.0301** | Ranking Quality |
| Hit Rate@10 | **10%** | Ranking Quality |
| Lift over Random | **~31x** | Ranking Quality |
| Cold-Start | ✅ Questionnaire UI | Cold-Start & Cross-Domain |
| Cross-Domain | ✅ 4/4 (Food/Movies/Books/Music) | Cold-Start & Cross-Domain |
| Multiturn | ✅ Budget-enforced refinement | Multiturn scenarios |

---

## Live Demo Features

| Feature | Description |
|---|---|
| **Live Persona Card** | Visual breakdown of your behavioural profile after entering review history |
| **Cold-Start Questionnaire** | No review history? Answer 5 questions to build your persona instead |
| **Task A — Review Generator** | Simulates your review of any product with typing animation and confidence retry |
| **Task B — Recommendation Agent** | Cross-domain recommendations (Food, Movies, Books, Music) with step-by-step reasoning |
| **Multiturn Refinement** | Follow up with budget changes or constraints — agent adjusts without repeating recommendations |
| **Persona Comparison Lab** | Two personas tested side-by-side — delta banner shows the star difference |
| **Confidence Retry** | Agent self-evaluates and regenerates if quality threshold not met |

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | `meta-llama/Llama-4-Scout-17B-16E-Instruct` via Groq API |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Store | ChromaDB (in-memory) |
| Backend | Django 6 + Django REST Framework |
| Frontend | Vanilla JS + custom CSS (dark navy/gold theme) |
| Dataset | Yelp Academic Dataset — 500 users, 15,209 reviews |
| Containerisation | Docker + docker-compose, deployed on Railway |
| Language | Python 3.12 |

---

## Project Structure

```
honest-friend/
├── manage.py
├── requirements.txt
├── .env.example
├── railway.json
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── task_a/
│   ├── views.py          # Review generation + cold-start endpoint
│   └── urls.py
│
├── task_b/
│   ├── views.py          # Recommendations + multiturn support
│   └── urls.py
│
├── agents/
│   ├── persona_builder.py
│   ├── review_agent.py   # Hard rating constraints per persona
│   ├── recommend_agent.py # Cross-domain, multiturn, budget enforcement
│   └── cold_start.py
│
├── core/
│   ├── llm.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── nigerian_voice.py
│   ├── scoring.py
│   ├── data_loader.py
│   ├── evaluate.py           # RMSE, ROUGE-L, BERTScore
│   └── evaluate_ranking_v2.py # NDCG@10, Hit Rate@10
│
├── paper/
│   ├── solution_paper.docx
│   ├── eval_results.json
│   └── eval_ranking_results.json
│
├── data/
│   └── sample/reviews_sample.csv
│
├── templates/
└── docker/
```

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/Berachaiah/honest-friend.git
cd honest-friend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```env
DJANGO_SECRET_KEY=any-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GROQ_API_KEY=your-groq-api-key-here
MODEL_NAME=meta-llama/Llama-4-Scout-17B-16E-Instruct
HUGGINGFACE_TOKEN=your-huggingface-token-here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 3. Download Yelp dataset

Download from [yelp.com/dataset](https://www.yelp.com/dataset) and place in `data/`:

```
data/yelp_academic_dataset_review.json
data/yelp_academic_dataset_business.json
data/yelp_academic_dataset_user.json
```

### 4. Generate sample CSV

```bash
python core/data_loader.py
```

### 5. Run

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

---

## Docker

```bash
cp .env.example .env  # fill in GROQ_API_KEY
cd docker
docker-compose up --build
```

---

## API Endpoints

### Task A — Generate Review

```
POST /api/task-a/generate/
{
  "reviews": [{"stars": 4, "text": "Solid spot.", "user_id": "user"}],
  "product": {"name": "Chicken Republic", "category": "Fast Food",
               "description": "Popular Nigerian chain.", "avg_price": "₦2,500"}
}
```

### Task A — Cold Start

```
POST /api/task-a/cold-start/
{
  "answers": {
    "rating_strictness": 4,
    "priorities": ["price", "quality"],
    "loves": ["fast service", "generous portions"],
    "hates": ["long waits", "overpriced"],
    "price_budget": "₦3,000"
  }
}
```

### Task B — Recommendations (with Multiturn)

```
POST /api/task-b/recommend/
{
  "reviews": [{"stars": 4, "text": "Solid spot.", "user_id": "user"}],
  "context": {"mood": "Catching up with a friend", "budget": "₦5,000", "location": "Lagos"},
  "followup": "Actually I only have ₦2,000 now",
  "history": [{"recommendations": ["Bogobiri House", "Terra Kulture"],
               "agent_verdict": "Start with Bogobiri — thank me later."}]
}
```

---

## Running Evaluations

```bash
# Task A — RMSE, ROUGE-L, BERTScore
python core/evaluate.py
# → RMSE: 0.7704 | ROUGE-L: 0.2050 | BERTScore F1: 0.8406

# Task B — NDCG@10, Hit Rate@10
python core/evaluate_ranking_v2.py
# → NDCG@10: 0.0301 | Hit Rate@10: 10% | ~31x random baseline
```

---

## Nigerian Cultural Layer

- **Price sensitivity detection** — keyword analysis classifies users as high/medium/low
- **Pidgin injection** — natural code-switching at moments of emotional emphasis
- **Occasion awareness** — salary day, date night, catching up shift recommendation priorities
- **Community trust signals** — word-of-mouth patterns recognised in review text

---

## Dataset

Yelp Academic Dataset (not included — download required). 500 users, 15,209 reviews.  
Source: [yelp.com/dataset](https://www.yelp.com/dataset)

---

## Solution Paper

`paper/solution_paper.docx` — full architecture, evaluation results (RMSE 0.7704, ROUGE-L 0.2050, BERTScore F1 0.8406, NDCG@10 0.0301, Hit Rate 10%), ablation studies, and future work.

---

## Author

**Abolaji Berachaiah**  
Computer Engineering · Bells University of Technology · 2022/11317  
DSN × BCT LLM Agent Challenge — Data & AI Summit Hackathon 3.0  
[github.com/Berachaiah](https://github.com/Berachaiah)
