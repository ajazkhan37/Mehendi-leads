# TODO — Deployment-ready + Responsive Website

## Step 1 — Hero uploads deploy-safety
- [x] Move hero uploads out of `static/` into `uploads/hero/` (or serve them via Flask route from there)
- [x] Add `GET /uploads/hero/<filename>` route using `send_from_directory`
- [x] Update `/api/hero-image` and `/api/hero-images` to return URLs that work after deployment
- [x] Keep backward compatibility for existing `static/uploads/hero/` images (serve from both locations if present)


## Step 2 — Production-ready Flask app (WSGI-ready)
- [x] Remove `debug=True` default (controlled via DEBUG env var)
- [x] Add environment-based configuration (SECRET_KEY, ADMIN creds, HOST, PORT)

- [x] Ensure `app` object is WSGI-compatible (no platform-specific config)

- [ ] Add `create_app()` pattern if needed


## Step 3 — Responsive robustness
- [ ] Check `static/style.css` for conflicting duplicate sections affecting homepage responsiveness
- [x] Fix any breakpoints/layout issues found

## Step 4 — Verification
- [ ] Run `python db_init.py`
- [ ] Start app locally with debug off and verify:
  - [ ] Homepage hero loads (active hero)
  - [ ] Homepage gallery loads + filters
  - [ ] Admin hero upload -> set active -> appears on homepage
  - [ ] Admin gallery unchanged


