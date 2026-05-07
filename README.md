# Propeller Copack Website

Marketing website for Propeller Copack, built as a static multi-page site.

## Overview

This repository contains the public website for Propeller Copack and supporting static assets.

- Home page: `index.html`
- Service/detail pages: one folder per page (for example `blending/`, `packaging-design/`, `white-label/`)
- Shared styles/scripts: `style.css`, `css/`, `js/`
- Image/font assets: `img/`, `fonts/`, `favicon.png`
- Form processors: `includes/` (PHP handlers referenced by page forms)

## Project Structure

```text
.
├── index.html
├── style.css
├── css/
├── js/
├── img/
├── fonts/
├── includes/
├── blending/
├── packaging-design/
├── white-label/
└── ...other service page folders
```

## Run Locally

Because this is a static site, you can run it with any local web server.

### Option 1: Python

```bash
python -m http.server 8080
```

Then open [http://localhost:8080](http://localhost:8080).

### Option 2: VS Code Live Server

Open the repo in VS Code/Cursor and start a Live Server session from `index.html`.

## Editing Guidelines

- Keep page-specific content in each page folder's `index.html`.
- Reuse global styles in `style.css` and shared vendor assets in `css/` and `js/`.
- Optimize new images before adding them to `img/` (prefer WebP when possible).
- If you update forms, verify matching handler files exist in `includes/`.

## Deployment

This repo is static-host friendly and can be deployed to platforms like GitHub Pages, Cloudflare Pages, Netlify, or any standard web host.

If your host uses a specific publish directory, set it to the repo root.

## License

Internal project repository unless otherwise specified by the repository owner.
