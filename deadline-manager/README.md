# Deadline Manager — Setup Guide

## Folder structure

```
deadline-manager/
├── api_bridge.py          ← Python backend (HTTP wrapper, run this)
├── package.json
├── public/
│   └── index.html
└── src/
    ├── App.jsx
    ├── App.css
    └── index.js
```

---

## Step 1 — Install Python dependencies

```bash
pip install flask flask-cors canvasapi google-genai python-dotenv
```

Make sure your `.env` file sits in the same folder as `api_bridge.py`:

```
CANVAS_API_URL=https://sdsu.instructure.com
GEMINI_API_KEY=your_gemini_key_here
```

---

## Step 2 — Start the Python backend

Open Terminal window #1:

```bash
python api_bridge.py
```

Leave it running. You'll see: `* Running on http://localhost:5000`

---

## Step 3 — Install Node.js (first time only)

Download the LTS version from https://nodejs.org and install it.

Verify:
```bash
node --version   # should print v20.x.x or similar
```

---

## Step 4 — Install React dependencies (first time only)

Open Terminal window #2 and navigate to this folder:

```bash
cd path/to/deadline-manager
npm install
```

---

## Step 5 — Start the React app

```bash
npm start
```

Browser opens automatically at http://localhost:3000

---

## What's new in this version

- **Finished submissions** are now displayed (matching updated server.py)
- Each assignment shows both **due date** and **submitted date**
- Difficulty badges: **Hard** (submitted < 6h before due), **Medium** (6–48h), **Easy** (> 48h), **Late**
- Stats row shows counts per difficulty tier
- Donut now shows % of hard/late submissions as a course difficulty score
- Calendar marks both due dates (red) and submission dates (blue)
- AI prompt includes `submitted_at` so Gemini can rank difficulty accurately

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Error connecting" on login | Make sure `python api_bridge.py` is running |
| Blank assignment list | Your Canvas token may lack read permission, or no submitted assignments exist yet |
| CORS error | Use `npm start`, don't open index.html directly |
| Gemini not responding | Check `GEMINI_API_KEY` in `.env` |
