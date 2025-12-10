from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from fastapi.responses import HTMLResponse

app = FastAPI()

# Logical backend names → Ollama model ids
BACKENDS = {
    "mistral": "mistral",
    "llama": "llama3.1",
}

OLLAMA_URL = "http://localhost:11434/api/chat"


class LLMRouteRequest(BaseModel):
    prompt: str
    backend: str  # "mistral" or "llama"


class LLMRouteResponse(BaseModel):
    reply: str
    backend_used: str


@app.post("/llm_route", response_model=LLMRouteResponse)
def llm_route(body: LLMRouteRequest):
    # Validate backend
    if body.backend not in BACKENDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown backend '{body.backend}'. "
                   f"Valid options: {list(BACKENDS.keys())}",
        )

    model_id = BACKENDS[body.backend]

    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": body.prompt}
        ],
        "stream": False,
        # Unload after each request for memory fairness
        "keep_alive": 0,
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error contacting Ollama: {e}",
        )

    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned {r.status_code}: {r.text}",
        )

    data = r.json()
    reply_text = data.get("message", {}).get("content", "").strip()

    if not reply_text:
        raise HTTPException(
            status_code=500,
            detail="Empty response from Ollama",
        )

    return LLMRouteResponse(
        reply=reply_text,
        backend_used=body.backend,
    )


PRIVACY_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>RAIL-MARP-GPT Action – Privacy Policy</title>
</head>
<body>
  <h1>Privacy Policy – RAIL-MARP-GPT External Action (llmRoute)</h1>
  <p><strong>Last updated:</strong> 17 November 2025</p>

  <p>This Action is a research and proof-of-concept service that routes prompts
  from ChatGPT to locally hosted language models via Ollama.</p>

  <h2>Data sent to this Action</h2>
  <p>When the llmRoute Action is called, it receives:</p>
  <ul>
    <li>The prompt text assembled by the custom GPT (which may include role,
    clearance label, scenario label, and MARP-related context).</li>
    <li>The backend identifier ("mistral" or "llama").</li>
  </ul>

  <h2>How the data is used</h2>
  <p>The data is used only to:</p>
  <ol>
    <li>Forward the prompt to a local model via Ollama (e.g. mistral, llama3.1).</li>
    <li>Obtain a text completion from that model.</li>
    <li>Return the completion back to ChatGPT as the Action response.</li>
  </ol>
  <p>The operator does not use this data to train or fine-tune any models.</p>

  <h2>Storage and logs</h2>
  <p>The FastAPI and Ollama processes may produce local logs (e.g. timestamps,
  status codes, and possibly truncated request bodies) for debugging purposes.
  These logs stay on the operator's machine and are not shared with third parties.</p>

  <h2>Data sharing</h2>
  <p>No data is shared with external third parties by the operator. Prompts are
  only passed to locally running models via Ollama in order to generate the
  requested completion.</p>

  <h2>Your choices</h2>
  <p>If you do not want your prompts sent to this Action, you can avoid using the
  custom GPT that is configured with this Action or disable Actions in your
  ChatGPT configuration (where applicable).</p>
</body>
</html>
"""


@app.get("/privacy", response_class=HTMLResponse)
def privacy():
    return PRIVACY_HTML
