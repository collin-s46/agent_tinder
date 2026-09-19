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

The public ANS discovery endpoint does not require credentials. The optional
`.env` file lets you change the ANS base URL or request timeout and is ignored
by Git.

Then open <http://127.0.0.1:5000>.

## Run backend tests

```bash
python -m unittest discover -s tests
```
