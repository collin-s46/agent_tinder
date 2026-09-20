# AgenTinder

A small Flask application that makes open agent discovery visible: a local
primary agent identifies a capability gap, discovers candidates through
GoDaddy Agent Name Service (ANS), and delegates the user's request to a chosen
agent over the A2A JSON-RPC protocol.

## What the demo proves

1. Choose Spark (events) or Sage (wellness) as Agent A.
2. Agent A classifies the request with deterministic, role-specific rules.
3. ANS returns real A2A-over-HTTP agents; no candidate records are fabricated.
4. AgenTinder displays an explainable compatibility score for each candidate.
5. A match is re-resolved through ANS, verified against its public Agent Card,
   and contacted using A2A `0.3.0`.
6. Agent B's response is returned through Agent A and shown in the interface.
7. Obvious low-information fallbacks are labeled, with an option to try the
   next discovered agent instead of treating protocol success as answer success.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app run --debug
```

The public ANS discovery endpoint does not require credentials. The optional
`.env` file is ignored by Git and supports:

```dotenv
ANS_BASE_URL=https://api.godaddy.com
ANS_TIMEOUT_SECONDS=10
A2A_TIMEOUT_SECONDS=20
```

Then open <http://127.0.0.1:5000>.

## Run backend tests

```bash
python -m unittest discover -s tests
```

The test suite uses mocks for external ANS and A2A requests, so it runs without
network access. The live interface still requires internet access to discover
and contact public agents.

## Project structure

- `app.py` owns the Flask routes and request validation.
- `services/ans_client.py` discovers and normalizes public ANS records.
- `services/a2a_client.py` validates Agent Cards and performs A2A requests.
- `services/capability.py` and `services/scoring.py` contain deterministic,
  explainable matching logic.
- `templates/` and `static/` contain the single-page interface.
