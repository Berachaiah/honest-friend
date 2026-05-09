# 🤝 The Honest Friend

> *An LLM-based behavioural intelligence agent that recommends things the way your most trusted Nigerian friend would — honest, opinionated, and culturally aware.*

**DSN × BCT LLM Agent Challenge — Data & AI Summit Hackathon 3.0**  
Submitted by **Abolaji Berachaiah** · Bells University of Technology · Computer Engineering 

---

## What It Does

Most recommendation systems treat users as static profiles. The Honest Friend builds a **dynamic behavioural persona** from a user's review history, then uses that persona to:

- **Task A** — Simulate how the user would review any new product (star rating + written review in their authentic voice)
- **Task B** — Reason through and recommend the next best experience for that specific person, with Nigerian cultural context baked in

The Nigerian cultural layer is not cosmetic — price sensitivity detection, natural Pidgin injection, community trust signals, and occasion-aware context are all engineered into the persona modelling pipeline.

---

## Live Demo Features

| Feature | Description |
|---|---|
| **Live Persona Card** | Visual breakdown of your behavioural profile after entering review history |
| **Task A — Review Generator** | Simulates your review of any product with typing animation |
| **Task B — Recommendation Agent** | Reasons step-by-step before recommending, with filtered-out section |
| **Persona Comparison Lab** | Two personas tested side-by-side on the same product — delta banner shows the star difference |
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
| Containerisation | Docker + docker-compose |
| Language | Python 3.12 |

---

## Project Structure

```
honest-friend/
├── manage.py                    # Django entry point
├── requirements.txt
├── .env.example                 # Copy to .env and fill in keys
│
├── config/                      # Django project settings
│   ├── settings.py
│   └── urls.py
│
├── task_a/                      # Task A — Review Generation app
│   ├── views.py                 # Web form handler + DRF APIView
│   └── urls.py
│
├── task_b/                      # Task B — Recommendation app
│   ├── views.py
│   └── urls.py
│
├── agents/                      # Core agent logic
│   ├── persona_builder.py       # Builds behavioural persona from review history
│   ├── review_agent.py          # Task A — generates reviews via Llama 4 Scout
│   ├── recommend_agent.py       # Task B — reasons then recommends
│   └── cold_start.py            # Handles new users with no history
│
├── core/                        # Shared utilities
│   ├── llm.py                   # Groq API interface
│   ├── embeddings.py            # sentence-transformers (lazy-loaded)
│   ├── vector_store.py          # ChromaDB similarity search
│   ├── nigerian_voice.py        # Nigerian cultural + linguistic layer
│   ├── scoring.py               # Self-evaluation / confidence scoring
│   └── data_loader.py           # Yelp JSON → sample CSV
│
├── data/
│   ├── yelp_academic_dataset_review.json   # ← download separately (see below)
│   └── sample/
│       └── reviews_sample.csv             # auto-generated
│
├── templates/
│   ├── base.html
│   └── core/index.html
│
├── static/
│   ├── css/main.css
│   └── js/app.js
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/Berachaiah/honest-friend.git
cd honest-friend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
DJANGO_SECRET_KEY=any-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GROQ_API_KEY=your-groq-api-key-here
MODEL_NAME=meta-llama/Llama-4-Scout-17B-16E-Instruct
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) — no approval needed, instant access.

### 3. Download the Yelp dataset

Download from [yelp.com/dataset](https://www.yelp.com/dataset) and place the following files in `data/`:

```
data/yelp_academic_dataset_review.json
data/yelp_academic_dataset_business.json
data/yelp_academic_dataset_user.json
```

### 4. Generate the sample CSV

```bash
python core/data_loader.py
```

This reads the Yelp JSON, finds 500 users with 20+ reviews each (stops early — takes ~5 seconds), and writes `data/sample/reviews_sample.csv`.

### 5. Run the server

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

---

## Docker (Recommended for Judges)

```bash
cp .env.example .env
# Fill in GROQ_API_KEY in .env

cd docker
docker-compose up --build
```

Open [http://localhost:8000](http://localhost:8000).

> **Note:** You still need to place the Yelp dataset files in `data/` and run `python core/data_loader.py` once to generate the sample CSV before starting the container, or mount the data volume after generation.

---

## API Endpoints

Both tasks expose REST API endpoints for the containerised submission requirement.

### Task A — Generate Review

```
POST /api/task-a/api/generate/
Content-Type: application/json

{
  "reviews": [
    {"stars": 4, "text": "Solid spot, service was decent.", "user_id": "user"},
    {"stars": 2, "text": "Waited 45 minutes. Not acceptable.", "user_id": "user"}
  ],
  "product": {
    "name": "Chicken Republic Lekki",
    "category": "Fast Food",
    "description": "Popular Nigerian fast food chain. Consistent quality.",
    "avg_price": "₦2,500"
  }
}
```

**Response:**
```json
{
  "persona": { "rating_style": "balanced", "price_sensitivity": "medium", ... },
  "simulated_review": "The chicken was solid sha, but...",
  "predicted_rating": 3.5,
  "reasoning_chain": "This user values service speed...",
  "naija_descriptor": "e dey okay",
  "confidence": { "score": 0.82, "passed": true }
}
```

### Task B — Get Recommendations

```
POST /api/task-b/api/recommend/
Content-Type: application/json

{
  "reviews": [
    {"stars": 4, "text": "Solid spot, service was decent.", "user_id": "user"}
  ],
  "context": {
    "mood": "Catching up with an old friend",
    "budget": "₦5,000",
    "location": "Victoria Island, Lagos"
  }
}
```

**Response:**
```json
{
  "persona": { ... },
  "result": {
    "reasoning_chain": "This person values...",
    "filtered_explanation": "- Craft Grill: Way above budget...",
    "recommendations": ["Terra Kulture — My guy, you love...", ...],
    "verdict": "For your vibe today, start with Terra Kulture — thank me later."
  }
}
```

---

## How the Agent Works

### Persona Extraction

The `PersonaBuilder` analyses review history and extracts a structured profile:

| Signal | Method |
|---|---|
| Rating style | Average rating → generous (≥4.2) / balanced / critical (≤2.5) |
| Verbosity | Median word count → brief (<60) / moderate / detailed (>150) |
| Price sensitivity | Price-marker keyword density in review text |
| Sentiment bias | Positive/negative keyword frequency |
| Consistency | Standard deviation of ratings |
| Top categories | Most frequent business types reviewed |
| Sample excerpts | Top 3 reviews preserved verbatim for LLM context |

### Agentic Behaviours

| Behaviour | Implementation |
|---|---|
| **Perceives** | Reads and encodes review history; extracts persona signals from unstructured text |
| **Plans** | Chain-of-thought prompting — reasoning is exposed before output is generated |
| **Uses Tools** | ChromaDB for embedding search, persona classifier, review generator, recommendation ranker |
| **Reflects** | Self-evaluates confidence score; retries with refined instructions if below threshold |
| **Cold Start** | Questionnaire-based persona building for users with no history |

### Nigerian Cultural Layer (`core/nigerian_voice.py`)

- **Price sensitivity detection** — price-marker keyword analysis classifies users as high/medium/low
- **Pidgin injection** — natural code-switching at moments of emotional emphasis
- **Occasion awareness** — context (salary day, date night, catching up) shifts recommendation priorities
- **Community trust signals** — word-of-mouth and social proof patterns recognised in review text

---

## Dataset

**Yelp Academic Dataset** (not included — download required)
- 500 users selected with 20+ reviews each
- 15,209 total reviews in working sample
- Filtered using early-stopping loader (`core/data_loader.py`) — stops reading the 7M-line JSON as soon as 500 qualified users are found

Dataset source: [yelp.com/dataset](https://www.yelp.com/dataset)

---

## Solution Paper

Included in the repository root: `solution_paper.docx`

Covers: architecture, persona extraction methodology, Nigerian cultural layer engineering, chain-of-thought prompting design, persona contrast test results (1.8-star delta between critical and balanced personas on the same product), ablation studies, limitations, and future work.

---

## Author

**Abolaji Berachaiah**  
Computer Engineering · Bells University of Technology  
Matriculation No: 2022/11317  
DSN × BCT LLM Agent Challenge — Data & AI Summit Hackathon 3.0
