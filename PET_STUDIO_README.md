# Pet Hatch Studio

Local test URL:

```powershell
python pet_studio_server.py
```

Then open:

```text
http://127.0.0.1:8787/pet_studio.html
```

## What It Does

- Creates one base identity prompt for a custom desktop pet.
- Generates or imports each animation row separately.
- Normalizes row images into `192x208` cells.
- Validates missing frames, edge clipping, and non-empty unused slots.
- Composes the canonical 9-row atlas: `1536x1872`.
- Exports `spritesheet.webp` and `pet.json`.

## API Safety Gate

The built-in image generation endpoint is wired but locked by default so testing never spends money by accident.

To enable Gemini-powered pet chat, screen looks, vision, and agent replies:

```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
python pet_studio_server.py
```

For the newer Gemini Python client used by the pet brain:

```powershell
python -m pip install google-genai
```

Optional non-agent Pet Studio image settings, still locked by default:

```powershell
$env:PET_STUDIO_IMAGE_MODEL = "gpt-image-2"
$env:PET_STUDIO_IMAGE_QUALITY = "medium"
$env:PET_STUDIO_PORT = "8787"
```

If the API is locked, clicking Generate still opens the exact prompt so a user can test the workflow with ChatGPT, Bing, or another image tool and import the result.

## Product Contract

The studio currently targets the core pet contract:

```text
atlas: 1536x1872
cells: 192x208
columns: 8
rows: 9
states: idle, running-right, running-left, waving, jumping, failed, waiting, running, review
```

The existing 12-row shonen/combat sheets should stay as an advanced extension after the 9-row flow is stable.
