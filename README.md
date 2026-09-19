# AgenTinder

A small Flask application for discovering and matching compatible AI agents.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app run --debug
```

Add your GoDaddy API key and secret to `.env` before using the ANS search API.
The `.env` file is ignored by Git and should never be committed.

Then open <http://127.0.0.1:5000>.

## Run backend tests

```bash
python -m unittest discover -s tests
```
