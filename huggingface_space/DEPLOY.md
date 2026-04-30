# Deploying to Hugging Face Spaces

The `huggingface_space/` folder is a self-contained, Space-ready bundle:
modern static site, all data baked in, Plotly vendored locally. Pick whichever
of the two paths below is most comfortable.

## Option A — drag-and-drop in the browser (easiest)

1. Sign in at <https://huggingface.co> (or sign up — free).
2. Click your avatar (top right) → **New Space**.
3. Settings:
   - **Owner:** your username
   - **Space name:** `beyond-gdp` (or anything you like; it ends up in the URL)
   - **License:** MIT
   - **Space SDK:** **Static** (the third option, important!)
   - **Visibility:** Public
4. Click **Create Space**.
5. On the empty Space page, click the **Files** tab → **Add file** →
   **Upload files**.
6. Drag every file inside `huggingface_space/` into the upload area:
   - `README.md` (this provides the YAML metadata for the Space card)
   - `index.html`, `style.css`, `site.js`, `data.js`
   - `plotly.min.js` (it's 4.5 MB, that's fine)
   - `favicon.svg`
   - the entire `data/` folder (drag the folder itself in)
7. Bottom of the page: write a commit message (e.g. "Initial deploy") →
   **Commit changes to main**.
8. Switch to the **App** tab. The site builds in 5–15 seconds. You will
   see your live URL near the top:
   `https://huggingface.co/spaces/<your-username>/beyond-gdp`.

That URL is public, mobile-friendly and works without any login.

## Option B — push from the command line

You'll need a Hugging Face access token (Settings → Access Tokens →
**New token** → Read+Write).

```bash
# 1) create the Space on the website (Static SDK), then:
git clone https://huggingface.co/spaces/<your-username>/beyond-gdp hf-space
cd hf-space

# 2) copy the bundle in
cp -r ../huggingface_space/. .

# 3) commit & push
git add -A
git commit -m "Initial deploy: Beyond GDP"
git push  # paste your token when prompted
```

## After deployment

- Drop your Space URL into the GitHub README (top of the file) so the
  marker has a one-click link.
- Optionally also enable GitHub Pages on `main /docs` so you have two
  publicly-served mirrors. Pages = same site, served from GitHub; HF
  Space = same site, served from Hugging Face. Either is fine on its
  own.

## Updating the site later

Whenever you change the analysis and re-run `make all`, the bundle is
re-synced automatically (`make hf-bundle`). Re-upload the changed files
through the Hugging Face web UI, or `git push` again from the cloned
Space repo.
