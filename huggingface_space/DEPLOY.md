# Deploying to Hugging Face Spaces

The `huggingface_space/` folder is a self-contained Space-ready bundle:
static site, all data baked in, Plotly vendored locally.

## Option A — drag-and-drop in the browser

1. Sign in at <https://huggingface.co>.
2. Click your avatar (top right) → **New Space**.
3. Settings:
   - **Owner:** your username
   - **Space name:** `beyond-gdp` (or anything you like)
   - **License:** MIT
   - **Space SDK:** **Static**
   - **Visibility:** Public
4. Click **Create Space**.
5. On the empty Space page, **Files** tab → **Add file** → **Upload files**.
6. Drag every file inside `huggingface_space/` into the upload area:
   - `README.md` (provides the YAML metadata for the Space card)
   - `index.html`, `style.css`, `site.js`, `data.js`
   - `plotly.min.js`
   - `favicon.svg`
   - the entire `data/` folder
7. Write a commit message → **Commit changes to main**.
8. Switch to the **App** tab. The site builds in ~10 seconds.

## Option B — push from the command line

You will need a Hugging Face access token (Settings → Access Tokens → Read+Write).

```bash
git clone https://huggingface.co/spaces/<username>/beyond-gdp hf-space
cd hf-space
cp -r ../huggingface_space/. .
git add -A
git commit -m "deploy"
git push
```

## Updating later

Whenever the analysis is re-run with `make all`, the bundle is re-synced
automatically (`make hf-bundle`). Re-upload the changed files through the
Hugging Face web UI, or `git push` again from the cloned Space repo.
