# Aeris

## Weather risk, explained like a local

Aeris is a grounded weather-risk assistant for Indian cities. Ask a practical question such as:

> Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?

Aeris combines a live Open-Meteo forecast, deterministic risk rules, and retrieval from curated local and official guidance. The result is a conversational answer with a risk level, an inspectable reasoning trace, and verified sources.

**Live demo:** [aerisai-nine.vercel.app](https://aerisai-nine.vercel.app)

## What it does

- Evaluates waterlogging risk for traffic and commute questions.
- Evaluates heat risk for outdoor activity and vulnerable groups.
- Evaluates unseasonal rain risk for wheat and other crop questions in Punjab.
- Retrieves evidence scoped by sector, state, and city from ChromaDB.
- Produces natural-language answers grounded in retrieved evidence.
- Falls back to cached or static weather data when Open-Meteo is unavailable.
- Avoids inventing a local advisory when no matching evidence is retrieved.

Supported locations:

| City | State |
| --- | --- |
| Mumbai | Maharashtra |
| Pune | Maharashtra |
| Bengaluru | Karnataka |
| Delhi | Delhi |
| Ludhiana | Punjab |
| Amritsar | Punjab |

Agriculture queries are currently limited to Ludhiana and Amritsar.

## Architecture

```text
Client_root/ (React + Vite)
        |
        | POST /ask
        v
ccc.py (FastAPI)
        |
        +--> Open-Meteo forecast and cache
        +--> rules/ deterministic risk assessment
        +--> retrieval/ sector and location-scoped Chroma search
        +--> synthesis/ grounded conversational answer and citation checks
```

The language model does not decide the risk level. The rule engine produces `LOW`, `MODERATE`, `HIGH`, or `SEVERE`; synthesis explains that result using only the retrieved evidence.

## Project structure

```text
.
├── ccc.py                 # FastAPI application and weather client
├── Client_root/           # React/Vite frontend
├── rules/                 # Traffic, heat, crop, and threshold rules
├── retrieval/             # Evidence retrieval and location scoping
├── rag/                   # Retrieval and synthesis orchestration
├── synthesis/             # Conversational answer generation and citation checks
├── ingestion/             # Document chunking and Chroma ingestion
├── docs/                  # Curated agriculture, health, and traffic sources
├── chroma_db/             # Persistent ingested vector store
├── tests/                 # Backend test suite
├── verify_ingestion.py    # Ingestion verification
├── verify_retrieval.py    # Retrieval-scope verification
├── verify_citation.py     # Citation verification
├── railway.json           # Railway start command
└── requirements.txt       # Python dependencies
```

## Quick start

### Backend

Requirements: Python 3.10 or newer.

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_anthropic_key
PORT=8000
```

Start the API:

```bash
uvicorn ccc:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive documentation is available at `http://localhost:8000/docs`.

### Frontend

```bash
cd Client_root
npm install
npm run dev
```

The frontend uses `VITE_API_URL` when it is set and otherwise falls back to `http://localhost:8000`:

```env
VITE_API_URL=http://localhost:8000
```

Do not commit real `.env` files or API keys.

### Offline development

Without `ANTHROPIC_API_KEY`, the backend uses its local grounded synthesizer. It still runs the weather, rules, retrieval, and citation pipeline, but the final prose is generated without a hosted language-model call.

## API

### `GET /health`

```json
{
  "status": "ok",
  "service": "Nimit Backend API",
  "version": "1.0.0"
}
```

### `GET /weather?location=Mumbai`

Returns current conditions, a short hourly forecast, weather metadata, and baseline traffic and health risk assessments.

### `POST /ask`

Request:

```json
{
  "query": "Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?",
  "location": "Mumbai",
  "sector": "traffic"
}
```

Response shape:

```json
{
  "answer": "Conversational, grounded response...",
  "risk_level": "HIGH",
  "reasoning_trace": ["Deterministic rule-engine step..."],
  "sources": ["https://example.com/source"],
  "fallback_used": false
}
```

`sector` accepts `traffic`, `health`, or `agriculture`. Empty queries, unsupported locations, and agriculture requests outside Punjab return `400`.

## Testing and verification

Run the complete test suite from the project root:

```bash
python -m pytest -q
```

Useful read-only checks:

```bash
python verify_ingestion.py
python verify_retrieval.py
python verify_citation.py
```

## Deployment

The intended deployment is:

- **Frontend:** Vercel, with `Client_root` as the root directory.
- **Backend:** Railway, using the committed `railway.json` start command.

Railway start command:

```bash
uvicorn ccc:app --host 0.0.0.0 --port $PORT
```

Set `ANTHROPIC_API_KEY` in Railway variables. Set `VITE_API_URL` in Vercel to the public Railway backend URL. See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment checklist.

## Known limitations

- The forecast currently aggregates one day of precipitation.
- Flood-zone, child-activity, and unseasonal-weather detection use query keywords.
- Agriculture currently assumes a grain-filling crop stage for the risk calculation.
- The weather cache is in-process and is not shared across workers or restarts.
- CORS is open for the hackathon deployment and should be restricted for production.

## Data sources

- Weather: [Open-Meteo](https://open-meteo.com/)
- Curated official and local guidance: [`docs/`](docs/)
- Vector retrieval: ChromaDB
- Answer synthesis: Anthropic Claude when `ANTHROPIC_API_KEY` is configured
