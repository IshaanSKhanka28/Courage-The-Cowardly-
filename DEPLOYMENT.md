# Nimit — Deployment Guide

Locked stack: **Vercel** (frontend) + **Railway** (backend). This doc is the
step-by-step for getting both live, plus the code changes required first and
coding-agent prompts for each.

Read the whole thing before starting — step 0 is a required code change, not
optional prep.

---

## 0. Required code change BEFORE deploying (do this first)

Right now the frontend calls the backend at a hardcoded
`http://localhost:8000/ask`. That only works on one person's machine. Before
deploying anywhere, this needs to become an environment variable so the same
frontend code works locally *and* against the deployed Railway URL.

### Prompt — make the API URL configurable

```
CONTEXT: "Nimit" project frontend (Client_root/, Vite + React). 
ChatPage.jsx currently calls fetch() against a hardcoded 
'http://localhost:8000/ask'. We're deploying the backend to Railway and 
the frontend to Vercel, so this URL must become configurable per 
environment instead of hardcoded.

TASK:
1. In ChatPage.jsx (and anywhere else the backend URL is hardcoded), 
   replace the literal 'http://localhost:8000' with 
   import.meta.env.VITE_API_URL, falling back to 
   'http://localhost:8000' if the env var isn't set (so local dev with 
   no .env still works unchanged).

2. Create Client_root/.env.example with:
   VITE_API_URL=http://localhost:8000

3. Confirm Client_root/.gitignore already excludes .env (it should, 
   per the project's existing gitignore pattern) - if not, add it. 
   .env.example should be committed; a real .env should never be.

CONSTRAINTS: Do not change the actual fetch logic, headers, or request 
body - only how the base URL is resolved. Vite exposes env vars prefixed 
with VITE_ automatically via import.meta.env; no extra config needed for 
this to work.

DEFINITION OF DONE: Running the frontend locally with no .env file still 
hits localhost:8000 exactly as before (no behavior change for existing 
devs). Setting VITE_API_URL in a real .env or in Vercel's environment 
variables redirects requests there instead.

OUTPUT FORMAT: files changed, and confirm the fallback behavior still 
works with a local manual test.
```

Run this, verify the app still works locally exactly as before, **then**
continue below.

---

## 1. Backend deployment — Railway

### 1.1 Pre-flight checklist

- [ ] `GEMINI_API_KEY` exists only in your local `.env`, never committed
      (verify this exact variable name matches what `synthesis/synthesize.py`
      actually reads via `os.getenv(...)` — swap below if it differs)
- [ ] `requirements.txt` is up to date (`fastapi`, `uvicorn[standard]`,
      `pydantic`, `python-dotenv`, `httpx`, `chromadb`,
      `sentence-transformers`, `google-generativeai`, `pytest`) — confirm
      the exact package name matches whatever Gemini SDK is actually
      imported in `synthesis/synthesize.py`
- [ ] `chroma_db/` is already committed to git (it is — confirmed not
      gitignored). This means Railway will deploy with your *already-ingested*
      vector store baked in. **Do not re-run ingestion on the deployed
      server** — it doesn't need to, the data is already there.
- [ ] All tests pass locally one more time: `pytest -v`

### 1.2 Create the Railway project

1. Go to [railway.app](https://railway.app), sign in with GitHub
2. **New Project → Deploy from GitHub repo** → select this repo
3. If Railway asks for a root directory and your backend files
   (`ccc.py`, `rules/`, `rag/`, `docs/`, `chroma_db/`, `requirements.txt`)
   are at the repo root (not inside a subfolder), leave root directory as `/`

### 1.3 Configure the start command

Railway auto-detects Python via Nixpacks, but you must set the start command
explicitly so it runs your FastAPI app correctly, not the local dev
`if __name__ == "__main__"` block.

In Railway's project settings → **Deploy** tab → **Custom Start Command**:

```
uvicorn ccc:app --host 0.0.0.0 --port $PORT
```

Railway injects `$PORT` automatically — don't hardcode `8000` here, it won't
match what Railway actually exposes.

### 1.4 Set environment variables

In Railway's project → **Variables** tab, add:

```
GEMINI_API_KEY=<your real key>
```

Nothing else should be required if `rules/`, `rag/`, `docs/`, and
`chroma_db/` are all present in the repo (they are, per the checklist above).

### 1.5 Deploy and get your URL

Railway deploys automatically after you save the config. Once it shows
"Success," go to **Settings → Networking → Generate Domain** to get a public
URL, something like `nimit-backend-production.up.railway.app`.

### 1.6 Verify the backend is actually live

```bash
curl https://<your-railway-url>/health
```

Should return `{"status": "ok", ...}`. Then hit `/docs` in a browser
(`https://<your-railway-url>/docs`) and manually run one real `/ask` call —
same verification discipline as every local test we've done. Don't assume
"deployed" means "working."

**Known risk to check for:** if Railway's build fails specifically on
`sentence-transformers` or `chromadb` (large dependencies, sometimes hit
build memory/timeout limits on free tiers), that's a real possibility worth
knowing about in advance — see the fallback note at the bottom of this doc.

---

## 2. Frontend deployment — Vercel

### 2.1 Pre-flight checklist

- [ ] Step 0's env-var change is done and verified locally
- [ ] Backend is already deployed and you have its real Railway URL

### 2.2 Create the Vercel project

1. Go to [vercel.com](https://vercel.com), sign in with GitHub
2. **Add New → Project** → select this repo
3. Vercel will ask for the **Root Directory** — set this to `Client_root`
   (the actual Vite app lives there, not at the repo root)
4. Framework Preset should auto-detect as **Vite** — confirm it did

### 2.3 Set environment variables

In Vercel's project settings → **Environment Variables**, add:

```
VITE_API_URL=https://<your-railway-backend-url>
```

Use the real Railway URL from step 1.5, **not** `localhost`.

### 2.4 Build settings (should auto-fill correctly for Vite, confirm anyway)

- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

### 2.5 Deploy and verify

Vercel deploys automatically after saving. Once live, open the real Vercel
URL, submit one real query through the actual deployed UI (not local), and
confirm you get a real answer with real sources — this is the true
end-to-end check, deployed frontend talking to deployed backend, not two
local processes on the same machine.

---

## 3. CORS — one thing to double check

`ccc.py` currently has:

```python
allow_origins=["*"]
```

This is fine for the hackathon demo (any frontend can call the backend), but
worth knowing it's wide open — not a real security posture, just a
deliberate hackathon-speed tradeoff. No action needed unless something breaks;
if it does, the fix is adding your specific Vercel domain to `allow_origins`
instead of `"*"`.

---

## 4. If something breaks — fallback plan

Per the project's own rules (never let a live demo depend on a single point
of failure):

- **If Railway deploy fails or is flaky close to demo time:** fall back to
  running the backend locally on the presenter's laptop
  (`uvicorn ccc:app --reload`) and pointing the deployed Vercel frontend's
  `VITE_API_URL` at a tunneled local URL (e.g. via `ngrok`), or just run
  both frontend and backend locally for the live demo instead of relying on
  the deployed versions. A working local demo beats a flaky deployed one.
- **If `sentence-transformers`/`chromadb` fail to build on Railway's free
  tier:** this is a known risk with heavier ML dependencies on constrained
  build environments. If it happens, the fastest fix is usually increasing
  Railway's build resources (paid tier) or, if there's no time for that,
  falling back to local-backend-only for the demo as above.

---

## 5. Final pre-demo checklist

- [ ] Backend deployed, `/health` and `/ask` verified live
- [ ] Frontend deployed, verified against the *deployed* backend (not
      localhost)
- [ ] Run your full eval query set (see project eval notes) against the
      **deployed** versions, not just local — behavior can differ under
      real network latency or cold-start delays
- [ ] Confirm `GEMINI_API_KEY` is set correctly in Railway (a missing
      key fails silently in some client setups — actually run a query, don't
      just check the variable is "there")
- [ ] Have the local fallback (both services running on the presenter's
      laptop) ready and pre-tested as backup, per section 4
