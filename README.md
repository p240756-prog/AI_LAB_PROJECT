# Plant Disease Classifier

A local leaf-image classifier with a React interface and the supplied VGG19 model. It ranks 36 crop-condition classes across 14 crops. The interface separates crop, condition and model score, with a searchable class catalogue, project plots and recent classifications.

**Prediction quality is not independently established.** Scores are uncalibrated softmax class scores, not disease severity or measured accuracy. See [the short report](docs/PROJECT_REPORT.md) for the preprocessing and evaluation findings.

## Folder structure

```text
Plant_Disease_Classifier/
  frontend/             React/TypeScript source, build config and public assets
  backend/              Unchanged HTTP integration, class map and Python requirements
  models/best_model.h5  Original supplied VGG19 checkpoint
  dist/                 Prebuilt frontend served by the backend
  docs/                 Short project report in Markdown and PDF
  Start-PlantLab.cmd    Windows launcher
  Start-PlantLab.ps1    Setup/start script
  Stop-PlantLab.ps1     Stop the launcher-managed service
```

Training/validation datasets, redundant model exports, notebooks, old presentations, screenshots, caches, installed dependencies and machine-specific configuration are excluded. The model and backend inference code are unchanged. Launch commands explicitly supply the relocated model path.

## Run locally on Windows

Install **64-bit Python 3.10, 3.11 or 3.12** and use a current browser. CPU inference works; a GPU is not required. TensorFlow needs an AVX-capable CPU and its supported Windows runtime; install the Microsoft Visual C++ Redistributable if a TensorFlow DLL error occurs. The first setup needs internet access for Python packages. Optional Google Fonts use the internet; fallback fonts and local inference work without them.

Extract the ZIP first, then double-click `Start-PlantLab.cmd`. It creates `.venv`, installs `backend/requirements.txt`, starts the service and opens **http://127.0.0.1:8787**. Initial TensorFlow installation/model loading can take several minutes. Node.js is unnecessary for this prebuilt app.

Manual PowerShell alternative, from this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/server.py --model models/best_model.h5 --port 8787
```

Open the localhost URL. Use Ctrl+C to stop a manually started service; use `.\Stop-PlantLab.ps1` for a launcher-managed service. If PowerShell script execution is restricted, use the manual Python commands. To retry a failed dependency installation, rerun the pip command above.

The bridge uses `tf_keras` to load the legacy H5 model. Do not replace it with a direct Keras 3 loader. Default `notebook` preprocessing preserves the supplied GUI's behavior, including its documented mismatch with training. The optional `--preprocessing vgg19` comparison mode is experimental and has not been certified as a fix.

## Edit or rebuild the frontend

Use Node.js 22+ and pnpm 11. From `frontend/`:

```text
pnpm install --frozen-lockfile
pnpm build
```

The build writes to the root `dist/` folder. For development, start the Python backend with `--allow-origin http://127.0.0.1:5173`, then run `pnpm dev` inside `frontend/` and open the printed **127.0.0.1** URL. The Vite proxy forwards `/api` to port 8787. For the integrated app, always open the backend URL rather than opening `dist/index.html` directly.

## Local API

- `GET /api/health`: readiness, model, class count and preprocessing mode.
- `GET /api/classes`: the complete ordered class map.
- `POST /api/predict`: raw JPEG/PNG/WebP bytes with the matching Content-Type; returns the top three class scores, image dimensions and timing. Maximum 10 MiB and 20 million pixels.

Images are processed locally and not saved by the server. The server binds to localhost and is intended for local use. GitHub Pages alone cannot execute the TensorFlow backend.

## GitHub upload: model requires Git LFS

The included model is 180,959,328 bytes (172.6 MiB). GitHub blocks normal Git files above 100 MiB and browser uploads above 25 MiB. **Do not upload this ZIP or the H5 model through the repository web uploader.** Use Git with Git LFS installed. The root `.gitattributes` already tracks `models/*.h5`.

Before adding files to a new local repository:

```text
git init
git lfs install
git lfs track "models/*.h5"
git add .
git lfs ls-files
```

Confirm the model appears in the LFS list before committing and pushing to your chosen repository. After cloning, use `git lfs pull` if the model is only a small pointer file. The ZIP contains the actual model bytes. No repository has been created or uploaded as part of this delivery.

Reference: [GitHub file-size limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

## Reports and asset sources

- [Project report (Markdown)](docs/PROJECT_REPORT.md)
- [Project report (PDF)](docs/PROJECT_REPORT.pdf)
- Sample photographs: [PlantVillage-Dataset](https://github.com/spMohanty/PlantVillage-Dataset); exact URLs and hashes are retained in `frontend/public/samples/PROVENANCE.json`.
- Original notebook plot provenance is retained beside the PNGs in `frontend/public/notebook-plots/`. These are image previews, not lesion maps or performance curves.
