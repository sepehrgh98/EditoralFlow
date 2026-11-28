# EditoralFlow

An AI editorial desk: it reviews a draft for quality and fit with house rules, checks every factual statement against trusted sources with citations (or says "can't tell"), and lets a human editor approve it.

**Status:** The Phase 1 Fact-check MVP is complete. The frontend offers grammar and style review and fact-checking against SciFact. See the [roadmap](documentation/product/roadmap.md).

## How it works

```
Frontend (Next.js, :3000)
   │  POST /review { article }
   ▼
Backend (FastAPI, :8000)
   │  LangGraph review graph
   ▼
Prepare draft ──► Grammar agent ─┐
              └─► Style agent  ──┴─► Merge results ──► { grammar_result, style_result }
                       │
                       ▼
              LLM client: Ollama on your machine (default, free) or Claude (paid)
```

Grammar and Style run at the same time. Each returns a score from 0 to 100 (100 = no problems), a list of issues and a summary. Every LLM call is logged with model, tokens, latency and estimated cost.

## Requirements

- macOS or Linux
- [uv](https://docs.astral.sh/uv/) (Python packages; installs Python 3.12 for you)
- [Node.js](https://nodejs.org/) for the frontend
- [Ollama](https://ollama.com/) for the free local model
- Docker (optional; to run the backend in a container)

## Quick start

All `make` commands work from the repository root.

**1. Start Ollama and download the model** (once, about 5 GB):

```bash
brew services start ollama      # or open the Ollama app
ollama pull qwen3:8b
```

**2. Configure the backend** (optional; the defaults use Ollama and need no key):

```bash
cp backend/.env.example backend/.env
```

**3. Set up fact-checking** (optional, before starting the backend):

```bash
make data
ollama pull qwen3:14b   # when using Ollama
```

**4. Start the backend**, either way:

```bash
make dev      # without Docker, logs in this terminal
make start    # in Docker; then: make logs
```

Open http://localhost:8000/health to check the backend. The `fact_check` field is `ready` when the corpus is indexed and `unavailable` when it could not be loaded.

**5. Start the frontend** in a second terminal:

```bash
cd frontend
npm install   # first time only
npm run dev
```

**6. Open http://localhost:3000**, paste an article and click **Review**. A review takes about 10 to 30 seconds on the local model. With `REVIEW_INCLUDE_FACT_CHECK=true`, Review also checks the draft against SciFact. Select a highlighted sentence to inspect the verdict and cited evidence.

### Fact-check an article through the API

Open http://localhost:8000/docs and try `POST /fact-check` with `{"article":"Your draft here."}`. The response includes each claim's verdict, any cited SciFact sentences, and counts by verdict.

If the corpus is missing, `POST /fact-check` returns 503 with setup instructions and grammar and style review remain available. To include fact-checking in `POST /review`, set `REVIEW_INCLUDE_FACT_CHECK=true` and restart. The review then shows highlighted claims and citations alongside grammar and style. With that flag enabled the server requires a loadable corpus at startup.

### Using Claude instead of the local model

Set these in `backend/.env` and restart the backend:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
```

API keys come from [console.anthropic.com](https://console.anthropic.com/) and are billed per use, separately from a claude.ai subscription. A review costs roughly $0.002 with the default fast model (Claude Haiku 5.5). Claude gives noticeably better reviews than the 8B local model.

### Main settings

All settings are listed with defaults in [`backend/.env.example`](backend/.env.example).

| Setting | Default | Meaning |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` (local, free) or `anthropic` (Claude, paid) |
| `OLLAMA_FAST_MODEL` | `qwen3:8b` | Local model for the agents |
| `OLLAMA_THINK` | `false` | Let the model reason first: slower, sometimes better |
| `ANTHROPIC_FAST_MODEL` | `claude-haiku-5-5` | Claude model for the agents |
| `LLM_TIMEOUT_SECONDS` | `120` | Give up on one model call after this long |
| `LOG_LEVEL` | `INFO` | `DEBUG` shows more detail |

## Testing

| Command | What it does | Cost |
| --- | --- | --- |
| `make check` | Lint and format check (ruff), types (pyright), all tests with a fake model | Free |
| `make test-live` | Two tests against the real model in your settings | Free with Ollama |
| `make hooks` | Turn on pre-commit: ruff runs on changed files at each `git commit` | Free |

GitHub Actions runs `make check`'s steps on every push and pull request ([workflow](.github/workflows/ci.yml)).

## Reading the code

The backend is split into layers; each layer only calls the one below it.

| Folder | Job |
| --- | --- |
| [`backend/app/api/`](backend/app/api/) | HTTP routes: `POST /review`, `POST /fact-check`, `GET /health` |
| [`backend/app/workflows/`](backend/app/workflows/) | The LangGraph graph: which agents run, in what order |
| [`backend/app/agents/`](backend/app/agents/) | One kind of review each; prompts in `prompts/<agent>/system.txt` and `user.txt` |
| [`backend/app/llm/`](backend/app/llm/) | The only code that talks to a model: interface, Ollama and Anthropic clients, pricing |
| [`backend/app/models/`](backend/app/models/) | Data shapes (Pydantic) shared by all layers |
| [`backend/app/core/`](backend/app/core/) | Settings and logging |
| [`backend/app/main.py`](backend/app/main.py) | App factory: builds everything once at startup |
| [`backend/tests/`](backend/tests/) | Tests; `fakes.py` holds the fake model |
| [`frontend/`](frontend/) | Next.js page |

A good reading order: `api/review.py` → `workflows/review_graph.py` → `agents/base.py` → `llm/base.py` → `llm/ollama.py`.

## Documentation

Design, decisions (ADRs) and the phase plans are in [`documentation/`](documentation/MAP.md). [Current state](documentation/architecture/current-state.md) describes the code file by file.
