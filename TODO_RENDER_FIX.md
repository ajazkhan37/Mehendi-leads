# Render deployment fix (Python 3.14 / ast.Str crash)

## Plan checkpoints
- [ ] Confirm current dependency versions and identify packages that break on Python 3.14 (ast.Str usage).
- [ ] Decide compatibility path:
  - [ ] Prefer keeping Python 3.11.9 (pin runtime + lock deps), OR
  - [ ] Upgrade Flask/Werkzeug/CSP stack if compatible.
- [ ] Verify Render respects `runtime.txt` (and configure Render environment accordingly).
- [ ] Update `requirements.txt` (pin Flask/Werkzeug versions and explicitly add any missing transitive deps needed).
- [ ] Update `Procfile` / gunicorn command if needed (timeouts, workers).
- [ ] Ensure startup works: `gunicorn app:app` locally.
- [ ] Run minimal runtime smoke tests: import app, call `/`.
- [ ] Commit changes and push to GitHub.
- [ ] Deploy to Render and verify app reaches Live.

