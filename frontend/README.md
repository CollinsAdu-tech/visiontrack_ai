# VisionTrack AI -- Frontend

React + Vite dashboard for the VisionTrack AI backend.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Opens on <http://localhost:5173>. The dev server proxies `/detect`,
`/track`, `/results`, `/health`, `/config`, and `/outputs` to the
backend at `http://localhost:8000` (see `vite.config.js`) -- make sure
the backend is running first (see `../backend/README.md`).

## Build

```bash
npm run build   # outputs to dist/
npm run preview # serve the production build locally
```

## How it works

- `hooks/useVisionTrack.js` is the single state machine driving the
  whole workflow (`idle -> uploading -> processing -> completed|failed`).
  Components only read this state; they never call the API directly
  except through `services/api.js`.
- The backend already burns detection/tracking boxes into the output
  image/video, so the frontend never draws its own overlay boxes -- it
  just displays whichever media is current (the local file before
  running, the annotated `output_url` after).
- `DetectionOverlay` is purely decorative chrome (the corner-bracket
  "viewfinder" frame and scanline) around whatever `MediaPreview` renders.

## Design notes

Dark, technical palette (deep teal-charcoal, phosphor-mint accent)
styled after machine-vision instrumentation rather than a generic SaaS
dashboard -- see `src/styles/index.css` for the token list. IBM Plex
Mono carries anything that reads like a data readout (counts,
confidence, fps); IBM Plex Sans carries body copy and instructions.
