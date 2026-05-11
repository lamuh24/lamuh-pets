# Lamuh Pets

Lamuh Pets is a desktop-pet and Pet Hatch Studio workspace for building, testing, and packaging animated AI companions.

## What Is Included

- `pet.py` - desktop pet runtime.
- `pet_studio.html` - local Pet Hatch Studio UI.
- `pet_studio_server.py` - local API server for studio workflows.
- `desktop-app/` - Electron shell and Windows packaging config.
- `hatch_engine/` - pet atlas generation and validation assets.
- `interaction_import_pack/` - Lamuh sample spritesheets and interaction manifests.
- `deploy/` - static deployable Pet Studio build.

## Run Locally

```powershell
python pet_studio_server.py
```

Then open:

```text
http://127.0.0.1:8787/pet_studio.html
```

## Desktop App

```powershell
cd desktop-app
npm install
npm start
```

Build the Windows installer:

```powershell
cd desktop-app
npm install
npm run build
```

## Static Deploy

The static site is configured for Netlify with `deploy/` as the publish directory.
