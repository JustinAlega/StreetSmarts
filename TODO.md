# PickHacksSP26 — TODO

## File Structure

```
PickHacksSP26/
├── backend/
│   ├── main.py                    # FastAPI entry — DONE, don't touch
│   ├── requirements.txt           # Python deps
│   ├── Dockerfile                 # Docker build — DONE
│   ├── .dockerignore
│   ├── db/
│   │   ├── database.py            # init_db(), get_connection() — DONE
│   │   └── db_writer.py           # DBWriter: insert/query helpers — STUB
│   ├── routes/
│   │   ├── heatmap.py             # GET /api/heatmap-data — STUB
│   │   ├── routing.py             # POST /api/route — STUB
│   │   ├── social.py              # POST /api/post + GET /api/feed — STUB
│   │   └── location_summary.py    # GET /api/location-summary — STUB
│   ├── ai/
│   │   └── gemini_classifier.py   # Gemini post classification — STUB
│   └── data/
│       ├── seed_truth.py          # Gaussian seed data for STL — STUB
│       └── parse_slmpd.py         # SLMPD CSV parser — STUB
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx                # Router — STUB
│       ├── main.tsx               # React entry
│       ├── index.css              # Global styles
│       ├── components/
│       │   ├── MapView.tsx        # Mapbox GL + heatmap layer — STUB
│       │   ├── RoutePanel.tsx     # Route inputs + safety slider — STUB
│       │   ├── SummaryPanel.tsx   # Risk breakdown panel — STUB
│       │   ├── LiveFeed.tsx       # Community feed + post form — STUB
│       │   ├── MapLegend.tsx      # Heatmap color legend — STUB
│       │   └── Header.tsx         # App header/nav — STUB
│       └── pages/
│           └── FeedPage.tsx       # Dedicated feed page — STUB
├── docker-compose.yml             # Docker Compose — DONE
├── .env.example                   # Env var template — DONE
├── .gitignore
├── TODO.md                        # ← you are here
└── README.md
```

---

## Backend Tasks

- [ ] **db/db_writer.py** — Implement insert_post(), update_truth(), get_feed(), risk_at_point()
- [ ] **routes/heatmap.py** — Query truth table → return GeoJSON FeatureCollection
- [ ] **routes/routing.py** — OSMnx graph load + A* pathfinding with safety weights
- [ ] **routes/social.py** — POST /api/post (classify + store) + GET /api/feed (nearby posts)
- [ ] **routes/location_summary.py** — Aggregate risk scores + nearby posts for a location
- [ ] **ai/gemini_classifier.py** — Gemini classify post → {severity, category}
- [ ] **data/seed_truth.py** — Generate Gaussian anchor data for STL bounding box
- [ ] **data/parse_slmpd.py** — Parse SLMPD NIBRS CSVs into truth table (stretch goal)

## Frontend Tasks

- [ ] **MapView.tsx** — Mapbox GL map + heatmap layer + click handler + route line
- [ ] **RoutePanel.tsx** — Start/end inputs, safety slider, call POST /api/route
- [ ] **SummaryPanel.tsx** — Show risk breakdown on location click
- [ ] **LiveFeed.tsx** — Display posts + submit form
- [ ] **MapLegend.tsx** — Green→Yellow→Red legend
- [ ] **Header.tsx** — App name, nav links
- [ ] **index.css** — Global styles, design system
- [ ] **FeedPage.tsx** — Full-page feed view

## Polish / Deploy

- [ ] Tighten CORS origins for production
- [ ] Deploy backend to Vultr (`docker compose up -d`)
- [ ] Point frontend API base URL to Vultr server
- [ ] README + demo prep

---

## 🏆 Sponsor Track Notes

### Google Gemini API

Already integrated in `backend/ai/gemini_classifier.py`. Places to use Gemini:

| Use Case | File | Description |
|----------|------|-------------|
| **Post classification** | `ai/gemini_classifier.py` | Classify user reports → severity + category |
| **Location summaries** | `routes/location_summary.py` | Generate natural-language safety recommendations |
| **News analysis** | `ai/` (new file) | If time: scrape STL news → Gemini extract safety events |

Model: `gemini-2.0-flash` (free tier: 15 RPM, 1M tokens/day)
Env var: `GEMINI_API_KEY` in `.env`

### Vultr RAG / Serverless Inference

Vultr offers serverless GPU inference and managed vector databases. Places to use:

| Use Case | Where to Add | Description |
|----------|-------------|-------------|
| **RAG knowledge base** | `ai/` (new module) | Store STL safety knowledge (crime reports, neighborhood guides) in Vultr vector DB, retrieve context for better Gemini responses |
| **Alternative models** | `ai/` (new module) | Use Vultr serverless inference to run open models (Llama, Mistral) as a fallback or for specific tasks like embeddings |
| **Embeddings** | `ai/` or `db/` | Generate embeddings for posts/reports, enable semantic search in the feed |

To add Vultr: create a new file like `ai/vultr_rag.py`, add the Vultr API endpoint + key to `.env.example`, and call it from routes as needed.
