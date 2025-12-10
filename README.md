# RAIL-MARP-GPT: Governance-Aware Custom GPT for MARP

This repository contains the configuration and supporting code for RAIL-MARP-GPT,
a Custom GPT that emulates a governance-aware orchestration architecture (RAIL)
for a Military Asset & Resource Planning (MARP) fleet transition case study.

RAIL-MARP-GPT is built entirely from:

Natural-language Instructions in the Custom GPT builder

Uploaded knowledge artifacts (policy, governance corpus, regulated knowledge, governed data)

A RAIL protocol file (rail_protocol.md)

A Custom GPT Action that routes some reasoning subtasks to local LLMs (Mistral / Llama 3.1 via Ollama) using a FastAPI adapter and an HTTPS ngrok tunnel

No OpenAI fine-tuning is required. You only need a ChatGPT account that supports Custom GPTs.

## 📂  Repository Structure
```
├── knowledge/
│   ├── marp_policy.json               # Policy-as-code: roles, clearances, domains, decisions
│   ├── marp_governance_knowledge.md   # Governance explanations & rationales
│   ├── marp_regulated_knowledge.json  # MARP calendars, thresholds, bottlenecks, flags
│   ├── marp_governed_data_view.csv    # Weekly synthetic capability/budget data
│   └── rail_protocol.md               # RAIL protocol (governance, routing, provenance)
├── adapter/
│   ├── main.py                        # FastAPI → Ollama adapter (POST /llm_route)
└── README.md
```
You do not need to modify the knowledge files to run the proof-of-concept.
You only need to:
- Run the adapter and expose it with ngrok.
- Create a Custom GPT and connect it to these files and the adapter.
  
---

## 📦 Prerequisites & Installation
### ✅ Requirements

- ChatGPT account with Custom GPTs (e.g. ChatGPT Plus or higher)
- Python 3.9+ with pip
- Ollama installed and running locally
- ngrok (or similar) for exposing your adapter over HTTPS

No OpenAI API key is required for this setup. The Custom GPT runs inside ChatGPT, and local models are accessed via Ollama.

---

### 🧰 Install and Run Local LLMs (Ollama)
1. Install Ollama from the official website.
2. Start the Ollama service:
```bash
ollama serve
```
3. Pull the models used by this PoC:
```bash
ollama pull mistral
ollama pull llama3.1
```
### 🌐 Install ngrok and Configure Auth Token
1. Create a free ngrok account.
2. Install ngrok.
3. Configure your auth token:
```bash
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```
---
# ⚙️ Setup Guide
## Step 1 – Run the RAIL LLM Adapter (FastAPI + Ollama)
1.1 Install Python Dependencies
From the repo root:
```bash
cd adapter
pip install fastapi uvicorn requests
```
1.2 Start Ollama (if not already running)
In a separate terminal execute:
```bash
ollama serve
```
1.3 Start the FastAPI Adapter

The adapter code can be found in the repo at adapter/main.py:

Run the adapter:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
The adapter now serves POST /llm_route on http://localhost:8000.

## Step 2 – Expose the Adapter via ngrok

In another terminal execute:
```bash
ngrok http 8000
```
You will see an HTTPS URL such as:
```bash
https://YOUR_ID.ngrok-free.app
```
Copy this URL. **You will reference it in the OpenAPI spec.** in step 3.4


## Step 3 – Create and Configure the Custom GPT (RAIL-MARP-GPT)

All next steps are done in the ChatGPT web UI.

#### 3.1 Open the Custom GPT Builder

- Open ChatGPT in your browser.

- Click Explore → Create a GPT.

- Go to the Configure tab.

- Set:

Name: RAIL-MARP-GPT

- Description:
Governance-aware MARP assistant that follows the RAIL protocol and can route some reasoning to local LLMs.

#### 3.2 Paste the Instructions

In the Instructions field, paste the following instruction:
```bash
You are BRIDGE-MARP-GPT, a governance-aware assistant that emulates the BRIDGE
architecture for the MARP fleet transition case.

SCOPE AND SOURCES
-----------------
You operate ONLY over the uploaded MARP artifacts. Treat these files as the ONLY
ground truth for MARP:

- marp_policy.json
- marp_governance_knowledge.md
- marp_regulated_knowledge.json
- marp_governed_data_view.csv
- bridge_protocol.md

Do NOT use general training data for MARP-specific values. Never invent new
numerical capability, dock, crew, spares, or budget figures or new calendar
structures beyond what is in these files. If information is missing, say so.

Always distinguish:
- Evidence = content read from the files above.
- LLM commentary = your explanations, comparisons, and formatting.

CORE BEHAVIOUR
--------------
For every request:

1. Follow bridge_protocol.md end-to-end:
   - Governance Plane (role, clearance, domains, ALLOW/PARTIAL/DENY).
   - Scenario control (SCENARIO 1 / 2 / 3 and weekly-curve requests).
   - Evidence routing (regulated knowledge vs governed data).
   - LLM routing over ChatGPT / Llama / Deepseek (including top-secret rules).
   - External adapter usage via the llmRoute Action.
   - Response Aggregation and confidence assessment.
   - Provenance stub generation.

2. Governance (high level):
   - Infer or read ROLE and CLEARANCE (default: planner, secret).
   - Use marp_policy.json to compute ALLOW / PARTIAL / DENY.
   - Use marp_governance_knowledge.md to justify the decision.
   - If DENY:
     - Return a short governance-based explanation.
     - Do NOT reveal numerical values or detailed calendar structures.
     - Return a minimal provenance_stub and stop.
   - If PARTIAL:
     - Explain restrictions.
     - Answer qualitatively only (no explicit numbers or dates).
   - If ALLOW:
     - Proceed with full protocol.

LLM ROUTING AND ACTION USAGE
----------------------------
The LLM pool consists of:
- ChatGPT (this Custom GPT; internal reasoning).
- Llama (via Ollama model "llama3.1" through the llmRoute Action).
- Deepseek (via Ollama model "deepseek-r1" through the llmRoute Action).

The details of the pseudo-random router, mapping to router_selected_llm,
backend_target, reasoning_mode, top_secret_internal_only, and any health-check
or timeout behaviour are defined in bridge_protocol.md. Follow that document
exactly.

Top-secret safeguard:
- If the query explicitly mentions "top secret" or the inferred clearance is
  top_secret, you MUST use internal ChatGPT only and MUST NOT call llmRoute.
- In such cases, set backend_target = "internal_chatgpt",
  backend_used = "internal_chatgpt", and top_secret_internal_only = true in
  the provenance stub.

Adapter usage:
- When bridge_protocol.md yields backend_target = "llama" or "deepseek" and the
  query is NOT top secret, you MUST call the llmRoute Action exactly once for
  the main explanatory subtask, using JSON:
  { "prompt": <structured MARP prompt>, "backend": "llama" | "deepseek" }.
- Respect any wait/timeout and health-check behaviour described in
  bridge_protocol.md (including simple echo tests and external failure handling)
  before falling back to internal reasoning.
- When backend_target = "internal_chatgpt" or the query is top secret, you MUST
  NOT call llmRoute and MUST rely only on internal reasoning.
- Always treat llmRoute.reply as commentary; if it conflicts with the uploaded
  files, prefer the files and note the discrepancy.

ANSWER STRUCTURE
----------------
Unless governance is DENY, structure answers as described in bridge_protocol.md,
typically:

1. Summary: whether capability can be maintained under the stated constraints.
2. Transition Calendar A: description, capability behaviour, bottlenecks,
   budget behaviour, policy flags.
3. Transition Calendar B: same elements plus explicit comparison to A.
4. Policy considerations and caveats, including any governance/confidence limits.
5. For ROLE = auditor: a short human-readable explanation of how evidence and
   governance rules were combined.

At the end of each answer (except pure DENY), append a fenced code block
labelled "provenance_stub" containing compact JSON with at least:
- role, clearance
- governance_decision
- evidence_sources
- router_selected_llm ("chatgpt", "llama", or "deepseek")
- backend_target
- backend_used ("internal_chatgpt", "llama", or "deepseek")
- top_secret_internal_only flag when applicable
- main subtasks
- confidence level and brief rationale.
```

You can adjust wording as long as the core behaviour is preserved.

#### 3.3 Upload Knowledge Files

In the Configure tab, under Knowledge upload the following given files from knowledge/.

```
├── knowledge/
│   ├── marp_policy.json               # Policy-as-code: roles, clearances, domains, decisions
│   ├── marp_governance_knowledge.md   # Governance explanations & rationales
│   ├── marp_regulated_knowledge.json  # MARP calendars, thresholds, bottlenecks, flags
│   ├── marp_governed_data_view.csv    # Weekly synthetic capability/budget data
│   └── rail_protocol.md               # RAIL protocol (governance, routing, provenance)
```
Ensure each file is enabled.

#### 3.4 Define the Action in Custom GPT (OpenAPI)

In the configuration tab click Add actions and then paste the following and within the instruction replace **https://YOUR_ID.ngrok-free.app** with your actual ngork URL 
```bash
{
  "openapi": "5.1.0",
  "info": {
    "title": "RAIL LLM Adapter",
    "version": "1.0.0",
    "description": "Adapter that routes prompts from RAIL-MARP-GPT to local Ollama models (mistral, llama3.1)."
  },
  "servers": [
    {
      "url": "https://YOUR_ID.ngrok-free.app"
    }
  ],
  "paths": {
    "/llm_route": {
      "post": {
        "operationId": "llmRoute",
        "summary": "Route a prompt to a selected Ollama backend and return its reply.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "prompt": {
                    "type": "string",
                    "description": "Full prompt including role, scenario, evidence, and instructions for the backend LLM."
                  },
                  "backend": {
                    "type": "string",
                    "description": "Target backend LLM identifier.",
                    "enum": ["mistral", "llama"]
                  }
                },
                "required": ["prompt", "backend"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "LLM reply.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "reply": {
                      "type": "string",
                      "description": "Text generated by the backend LLM."
                    },
                    "backend_used": {
                      "type": "string",
                      "description": "Backend actually used by the adapter."
                    }
                  },
                  "required": ["reply", "backend_used"]
                }
              }
            }
          },
          "4XX": {
            "description": "Client error when calling the adapter."
          },
          "5XX": {
            "description": "Server or adapter error."
          }
        }
      }
    }
  }
}
```
The builder should show an Action named llmRoute.

Use the built-in test:

{
  "prompt": "Simple echo test from RAIL-MARP-GPT Action.",
  "backend": "mistral"
}


You should see a JSON response with reply and backend_used.

#### 3.5 Define Capabilities

Under Capabilities tab do

- Web browsing: OFF (closed RAIL/HRE-style environment)

- Code Interpreter: optional (not required)

- Image generation: optional

Click Save to save the GPT.

### ✅ Step 4 – Quick Connectivity Test in a Chat

Open a new chat with RAIL-MARP-GPT and send:

For this message, ignore MARP and governance and just TEST your llmRoute Action.

Call llmRoute with:
- backend = "mistral"
- prompt  = "Simple echo test from RAIL-MARP-GPT."

Then show me ONLY:
1) The backend_used field you got back.
2) The reply field you got back.

Return them as a small JSON object and nothing else.


If everything is wired correctly, you should see something like:

{
  "backend_used": "mistral",
  "reply": "Simple echo test from RAIL-MARP-GPT. ..."
}


If not:

Confirm uvicorn is running on port 8000.

Confirm ngrok is running and llm_adapter_openapi.json has the current URL.

Re-import the OpenAPI file into the GPT if needed.

---

# 🚀 MARP Scenario Experiments

These prompts test the three RAIL-MARP routing scenarios described in the protocol.

6.1 Scenario 1 – Regulated Knowledge Only
SCENARIO 1
ROLE: planner
CLEARANCE: secret

Given a plan to retire two boats in quarter three, can weekly capability stay at
or above the required level through quarter four under current dock capacity,
crew readiness, and spares constraints, and within the approved budget? Return
the top two feasible transition calendars with uncertainty bands, key
bottlenecks, and any policy flags.


Expected:

Uses only marp_regulated_knowledge.json.

Does not consult marp_governed_data_view.csv.

Provenance stub: governed_data empty or omitted.

6.2 Scenario 2 – Regulated Knowledge + LLM Explanation

Base query:

SCENARIO 2
ROLE: planner
CLEARANCE: secret

Given a plan to retire two boats in quarter three, can weekly capability stay at
or above the required level through quarter four under current dock capacity,
crew readiness, and spares constraints, and within the approved budget? Return
the top two feasible transition calendars with uncertainty bands, key
bottlenecks, and any policy flags.


Follow-up explanation:

SCENARIO 2
ROLE: planner
CLEARANCE: secret

Explain the trade-offs between Transition Calendar A and Transition Calendar B.
Focus on the uncertainty bands, dock and crew bottlenecks, and policy
implications. Do not introduce any new numerical values beyond those already
encoded in the regulated knowledge file.


Expected:

Answers grounded in marp_regulated_knowledge.json.

Second answer is more narrative; external LLM may be invoked via llmRoute,
but no new numbers are invented.

6.3 Scenario 3 – Regulated Knowledge + Governed Data + LLM Reasoning
SCENARIO 3
ROLE: planner
CLEARANCE: secret

Given a plan to retire two boats in quarter three, can weekly capability stay at
or above the required level through quarter four under current dock capacity,
crew readiness, and spares constraints, and within the approved budget?

This time, please:
- Use both the precomputed Transition Calendars A and B and the governed data
  view.
- Summarise the weekly capability curves and budget utilisation patterns for
  each calendar (you can aggregate weeks if needed).
- Highlight which weeks come closest to the capability threshold and where dock
  utilisation or budget usage is most critical.
- Return the top two feasible transition calendars with uncertainty bands, key
  bottlenecks, policy flags, and the requested capability/budget patterns.


Expected:

Structural information from marp_regulated_knowledge.json.

Weekly capability / budget patterns from marp_governed_data_view.csv.

Provenance stub lists both regulated knowledge and governed data as evidence sources, plus routing info for any llmRoute calls.
