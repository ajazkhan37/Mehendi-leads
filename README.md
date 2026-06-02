# Mehendi-leads

(Deployment compatibility fixes added for Render/Python 3.14)

## Render
- Ensure `runtime.txt` uses `python-3.11.9`.
- Use `Procfile` with gunicorn.

## Local
To run locally:
- `python app.py` (debug/dev)
- `gunicorn app:app` (prod-like)

