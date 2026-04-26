# 🔍 Veritas — AI-Powered Fact-Checking Platform

> **"Don't just read the news. Verify it."**

Veritas is a full-stack, production-grade fact-checking platform that fights misinformation by dissecting news articles, social media posts, and screenshots into atomic claims and verifying each one against live, multi-source web evidence. It combines a state-of-the-art LangGraph agentic AI pipeline with community-driven consensus to produce a final, transparent credibility verdict.

---

## 📑 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [How It Works — The Big Picture](#-how-it-works--the-big-picture)
3. [Architecture Deep Dive](#-architecture-deep-dive)
4. [Safety & Accuracy Mechanisms](#-safety--accuracy-mechanisms)
5. [Community Layer](#-community-layer)
6. [API Reference](#-api-reference)
7. [Technology Stack](#-technology-stack)
8. [Project Structure](#-project-structure)
9. [Setup & Running Locally](#-setup--running-locally)
10. [Environment Variables](#-environment-variables)

---

## 🎯 Problem Statement

Misinformation spreads because fact-checking is slow, opaque, and hard to access. Most fact-checkers:
- Take hours or days to publish verdicts
- Only cover major viral stories
- Give you a verdict without explaining **why**
- Have no mechanism for public correction or disagreement

Veritas solves this by giving anyone instant, transparent, claim-by-claim fact-checking with full evidence citations — and a community layer that can challenge and adjust the AI's conclusions.

---

## 🌐 How It Works — The Big Picture

A user submits a news article (via URL, text paste, or screenshot). Veritas runs it through a 10-node agentic pipeline and returns a structured result within 30–60 seconds. This is what happens inside:

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline                   │
│                                                         │
│  Cache Check ──hit──▶ Score Aggregator                  │
│       │                                                 │
│      miss                                               │
│       ▼                                                 │
│  Input Parser (URL scrape / OCR / text)                 │
│       ▼                                                 │
│  Essence Extractor (What is this article REALLY about?) │
│       ▼                                                 │
│  Claim Splitter (Break into atomic, verifiable claims)  │
│       │                                                 │
│       ├──▶ Claim 1 Processing (Parallel)                │
│       ├──▶ Claim 2 Processing (Parallel)                │
│       └──▶ Claim N Processing (Parallel)                │
│              │                                          │
│              │  Per-claim subgraph:                     │
│              │    Query Builder                         │
│              │      ▼                                   │
│              │    Adversarial Searcher (2 Tavily calls) │
│              │      ▼                                   │
│              │    Evidence Judge (1 LLM call)           │
│              │      ▼                                   │
│              │    Penalty Node (confidence math)        │
│              │                                          │
│       ◀──────┘ Fan-in all claim results                 │
│       ▼                                                 │
│  Score Aggregator (compute final ai_score)              │
│       ▼                                                 │
│  Explanation Generator (plain-English summary)          │
│       ▼                                                 │
│  Cache Writer (persist to Firestore)                    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Frontend renders claim cards + scores + evidence links
```

---

## 🏗️ Architecture Deep Dive

### Node 1 — Cache Check
Every analysis starts with a SHA-256 hash of the raw input. If the same article was analyzed within the last **7 days**, the pipeline short-circuits straight to `Score Aggregator`, returning the cached result instantly. This saves API costs and dramatically reduces latency for popular articles.

### Node 2 — Input Parser
Handles three input types:
- **URL**: Fetches the page with `httpx` (3-retry policy with exponential backoff), strips boilerplate HTML (nav, footer, scripts), and extracts clean article text via `BeautifulSoup`.
- **Text**: Passes the raw text through directly after sanitization.
- **Image**: Sends a base64-encoded screenshot to **Gemini Vision** to perform OCR and extract the news text.

### Node 3 — Essence Extractor
The LLM reads the full article and extracts a structured "essence object":
- `is_verifiable`: Flags personal statements (e.g., "I am sick") as non-news — the pipeline short-circuits if `False`.
- `essence`: A 2-3 sentence factual summary of what the article is actually claiming.
- `framing_tone`: One of `[alarmist, neutral, misleading, satirical, opinion]`.
- `primary_actor`: The key subject of the article (person, country, organization).
- `implied_consequence`: What outcome the article implies or warns about.

### Node 4 — Claim Splitter + Essence Drift Guard
The LLM splits the article into up to **4 atomic, independently verifiable claims** and tags each with:
- `type`: `fact` (externally checkable) | `framing` (opinion/spin) | `attributed` (X said Y — verifiable only as a quote)
- `loaded_language`: An array of emotionally manipulative words/phrases detected in the claim (e.g., `["secretly", "massive crackdown"]`).
- `essence_relation`: How this specific claim connects to the article's overall narrative.

**Immediately after splitting**, the Essence Drift Guard runs a **cosine similarity check** using `sentence-transformers`:
```
drift_score = 1 - cosine_similarity(essence_embedding, recomposed_claims_embedding)
```
If `drift_score > 0.25`, the claims have semantically drifted from the original article's meaning. This score is stored in state and used downstream to penalize overconfident verdicts.

### Node 5 — Claim Router (Fan-Out)
Uses LangGraph's `Send` API to launch each claim as a **fully independent, parallel execution branch**. Claims are processed concurrently — the pipeline doesn't wait for Claim 1 to finish before starting Claim 2.

### Per-Claim Subgraph (Nodes 6–9)

Each claim runs through a 4-step subgraph:

#### Step 1: Query Builder (Node 6)
The LLM generates two distinct search queries for each claim:
- **Confirming query**: Finds primary sources, official statements, and reports that support the claim.
- **Contradicting query**: Targets specific factual errors, retractions, corrections, or denials — NOT just "different framing" of the same event.

For **attributed claims** (e.g., "PM Modi said..."), the contradicting query looks for evidence that the statement was never made, not evidence that the statement is wrong.

#### Step 2: Adversarial Searcher (Node 7)
Fires **both queries simultaneously** using `asyncio.gather` against the **Tavily AI Search API**. Results are tagged with their search stance (`supports` or `contradicts`).

The searcher also performs **Echo Chamber Detection**: if 3+ results share the same root domain, or fewer than 3 unique domains appear total, it flags `echo_chamber_detected = True`. This prevents circular sourcing from inflating confidence.

#### Step 3: Evidence Judge (Node 8 — merged LLM call)
A single, structured LLM call (replacing the old 2-step alignment + judge flow) that:
1. **Classifies each piece of evidence** by `relevance` (direct/partial/irrelevant), `stance` (supports/contradicts/neutral), and `source_type` (primary/secondary/aggregator).
2. **Renders a final verdict** for the claim: `supported` | `contradicted` | `uncertain` | `unverifiable`.
3. Identifies the **specific false detail** if the claim is contradicted.

Critical rules baked into the prompt:
- A source reporting the **same event** is "neutral" or "supports", never "contradicts".
- A source only "contradicts" if it explicitly states a **specific detail** is factually wrong.
- An attributed claim is "supported" if **any credible source** confirms the statement was made.

#### Step 4: Penalty Node (Node 9)
Applies mathematical penalties to the raw confidence score:
```python
echo_multiplier = 0.75  if echo_chamber_detected  else 1.0
# drift_score is stored in state from the Essence Drift Guard
final_confidence = raw_confidence * echo_multiplier
```
Then packages the claim result — including `loaded_language`, sources, verdict, and reasoning — for fan-in.

### Node 10 — Score Aggregator
All parallel claim results fan back in here. The aggregator uses a **weighted scoring formula**:

```python
VERDICT_WEIGHT = {
    "supported":    1.0,
    "uncertain":    0.5,
    "unverifiable": 0.4,
    "contradicted": 0.0,
}

# Confidence-weighted average per claim type
fact_score    = Σ(verdict_weight × confidence) / Σ(confidence)   # for fact claims
framing_score = Σ(verdict_weight × confidence) / Σ(confidence)   # for framing claims

# Final blended score (facts weighted more heavily)
ai_score = 0.7 × fact_score + 0.3 × framing_score
```

### Node 11 — Explanation Generator
The LLM writes a 3-4 sentence plain-English summary of the fact-check:
- What the article got **right** (supported claims)
- What it got **wrong** (contradicted claims, with specific detail named)
- What could **not be verified** (unverifiable claims — importantly, this is NOT labeled "false")
- How the **framing/tone** affects the overall credibility picture

### Node 12 — Cache Writer
Persists the complete analysis result to **Firestore** under `analysis_cache/{sha256_hash}` for 7-day reuse. Also creates/updates a `posts` document for community features (voting and disputes).

---

## 🛡️ Safety & Accuracy Mechanisms

| Mechanism | Where | What it Prevents |
|---|---|---|
| **Essence Drift Guard** | After claim splitting | LLM hallucinating claims that don't reflect the original article |
| **Echo Chamber Detection** | Adversarial Searcher | Single-source circular reporting inflating confidence |
| **Adversarial Search** | Per-claim | Confirmation bias — the pipeline always looks for contradictions |
| **Context Injection** | Evidence Judge | The Judge always receives the original `essence` to prevent evaluating a misrepresented claim |
| **Attributed Claim Typing** | Claim Splitter + Judge | Prevents marking quotes as "false" when only the statement — not its content — is verifiable |
| **Non-news Guard** | Essence Extractor | Personal or anonymous texts (e.g., "I feel sick") are rejected before wasting API calls |
| **7-day Cache** | Cache Check | Prevents duplicate expensive analyses of the same article |
| **Confidence Penalty** | Penalty Node | Echo chamber and semantic drift reduce AI confidence automatically |

---

## 👥 Community Layer

Beyond the AI pipeline, Veritas includes a full community consensus system:

### Voting
Authenticated users can upvote or downvote any analysis. Votes are stored in `post_votes/{post_id}:{uid}` and aggregated as `upvotes` and `downvotes` on the post document.

### Dispute System
Users can file a formal dispute against a specific claim, providing their own evidence URL and counter-argument. The dispute service:
1. Validates the evidence URL
2. Uses an LLM to reason about whether the user's evidence actually contradicts the AI's verdict
3. Returns a `score_impact` indicating how much the community disagrees with the AI

### Community Feed
The `/community` page shows a live feed of all analyzed articles with their:
- AI credibility score
- Community vote totals
- Number of disputes filed
- Sortable by: Trending / Top Rated / Most Disputed

### WhatsApp Bot
Users can submit news directly over WhatsApp:
1. Send any news text or image to **+1 (415) 523-8886** with the code `join clean-water`
2. Veritas replies instantly with "Analyzing..." via Twilio
3. The analysis runs in a background **ARQ + Redis** queue
4. A full verdict is sent back to the user's WhatsApp when complete

---

## 📡 API Reference

All API routes are prefixed at `http://localhost:8000`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/analyze` | Optional | Submit a new analysis job. Returns `job_id` immediately. |
| `GET` | `/api/results/{job_id}` | Optional | Poll for analysis result. Returns status + full result when done. |
| `GET` | `/api/results` | Optional | List all completed analyses (community feed data). |
| `POST` | `/api/vote/{post_id}` | Required | Cast an upvote or downvote on an analysis. |
| `POST` | `/api/disputes` | Required | File a dispute against a specific claim with counter-evidence. |
| `GET` | `/api/posts/{post_id}/disputes` | None | Get all disputes filed against a post. |
| `POST` | `/auth/login` | None | Firebase token exchange. |
| `POST` | `/whatsapp/webhook` | Twilio sig | Inbound WhatsApp message handler. |
| `POST` | `/chatbot/chat` | None | Chatbot interface for general Q&A. |
| `GET` | `/health` | None | Server health check. |

### Example: Submit an Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"input_type": "url", "raw_input": "https://example.com/news-article"}'
```

**Response:**
```json
{ "job_id": "abc123", "status": "queued" }
```

### Example: Poll for Result

```bash
curl http://localhost:8000/api/results/abc123
```

**Response (when done):**
```json
{
  "job_id": "abc123",
  "status": "done",
  "result": {
    "ai_score": 0.72,
    "essence": "The article claims that...",
    "explanation": "Two of the four claims were supported by...",
    "claims": [
      {
        "claim": "The government passed bill X",
        "claim_type": "fact",
        "verdict": "supported",
        "confidence": 0.88,
        "loaded_language": ["secretly", "rushed"],
        "reasoning": "Three independent sources confirmed...",
        "supporting_sources": ["https://reuters.com/...", "https://bbc.com/..."],
        "contradicting_sources": []
      }
    ]
  }
}
```

---

## 🛠️ Technology Stack

### Backend
| Component | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| Agentic Orchestration | LangGraph (StateGraph) |
| Primary LLM | Google Gemini 2.5 Flash (via LangChain) |
| Vision/OCR | Google Gemini Vision |
| Web Search | Tavily AI Search API |
| Semantic Embeddings | `sentence-transformers` (all-MiniLM-L6-v2, local) |
| Database | Firebase Firestore (async) |
| Authentication | Firebase Auth |
| Background Jobs | ARQ + Redis |
| WhatsApp Integration | Twilio |
| HTTP Client | `httpx` (async) |
| HTML Parsing | `BeautifulSoup4` |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 + Vite |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Auth | Firebase Auth (client SDK) |
| Design | Dark mode, Glassmorphism, micro-animations |

---

## 📂 Project Structure

```
Veritas/
├── backend/
│   ├── main.py                    # FastAPI app entry point, route registration
│   ├── requirements.txt
│   │
│   ├── agent/
│   │   ├── pipeline.py            # LangGraph StateGraph definition and compilation
│   │   ├── nodes.py               # All 10 pipeline node functions
│   │   └── llm_judge_subgraph.py  # Per-claim processing subgraph
│   │
│   ├── core/
│   │   ├── config.py              # Settings, env var loading
│   │   ├── firebase.py            # Firebase Admin SDK init + async client
│   │   ├── llm_client.py          # Gemini LLM singleton
│   │   └── prompts.py             # All LLM system prompts
│   │
│   ├── routes/
│   │   ├── analyze.py             # POST /api/analyze, GET /api/results
│   │   ├── vote.py                # POST /api/vote/{post_id}
│   │   ├── dispute.py             # POST /api/disputes
│   │   ├── auth.py                # Firebase auth endpoints
│   │   └── whatsapp.py            # POST /whatsapp/webhook (Twilio)
│   │
│   ├── services/
│   │   ├── web_search.py          # Tavily adversarial search (parallel)
│   │   ├── essence_guard.py       # Semantic drift check via sentence-transformers
│   │   ├── input_parser.py        # URL fetch, image OCR, text sanitization
│   │   ├── dispute_service.py     # Dispute validation and LLM reasoning
│   │   └── twilio_service.py      # WhatsApp message sending
│   │
│   └── schema/
│       ├── state.py               # GraphState TypedDict, all Pydantic output models
│       └── dispute.py             # Dispute request/response models
│
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx           # Landing page / analysis input
        │   ├── analyze/           # Real-time analysis progress + result page
        │   ├── analysis/          # Detailed per-analysis view
        │   ├── community/         # Community feed (trending, top, disputed)
        │   └── auth/              # Login / signup pages
        │
        ├── components/
        │   ├── ClaimCard.tsx      # Per-claim verdict card (verdict, evidence, loaded language chips)
        │   ├── ScoreGauge.tsx     # Animated credibility score dial
        │   └── ...                # Other UI components
        │
        └── lib/
            ├── api.ts             # All backend API calls (typed)
            └── types.ts           # Shared TypeScript interfaces
```

---

## 🚀 Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Firebase project with Firestore enabled
- API keys for Google Gemini and Tavily

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see Environment Variables section)
cp .env.example .env
# Edit .env with your keys

# 5. Place your Firebase service account key
# Download from Firebase Console → Project Settings → Service Accounts
# Save as: backend/serviceAccountKey.json

# 6. Start the backend server
python main.py
# Server runs at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create your .env file
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_FIREBASE_... (your Firebase web config)

# 4. Start the development server
npm run dev
# App runs at http://localhost:3000
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key for all LLM calls |
| `TAVILY_API_KEY` | ✅ | Tavily Search API key for web searches |
| `FIREBASE_CREDENTIALS_PATH` | ✅ | Path to `serviceAccountKey.json` |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated list of allowed CORS origins |
| `REDIS_URL` | Optional | Redis DSN for WhatsApp job queue (default: `redis://localhost:6379`) |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio SID for WhatsApp bot |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token for WhatsApp bot |
| `TWILIO_WHATSAPP_NUMBER` | Optional | Twilio WhatsApp sender number |
| `APP_ENV` | Optional | `development` or `production` |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend base URL (e.g., `http://localhost:8000`) |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | ✅ | Firebase web API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | ✅ | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | ✅ | Firebase project ID |

---

## 🧭 Design Decisions & Trade-offs

- **LangGraph over custom orchestration**: LangGraph's `Send` API enables true parallel claim processing with fan-out/fan-in, something difficult to implement cleanly with raw asyncio.
- **Single merged LLM call per claim**: The old system made 2 LLM calls per claim (alignment + judge). Merging them into one `EvidenceJudgeOutput` cut per-claim latency by ~40%.
- **Local embeddings for drift detection**: Using `sentence-transformers` locally (no API call) keeps the drift guard fast and free.
- **Tavily over raw Google Search**: Tavily's API is purpose-built for LLM pipelines, returning clean structured results without pagination or HTML parsing.
- **In-memory job store**: Analysis jobs are stored in-memory during the session. Firestore is the persistent source of truth, and the in-memory store is rebuilt from Firestore on server restart via the `/api/results` merge logic.

---

*Built with ❤️ to make truth more accessible.*
