# Installation Guide

## Requirements

- Python 3.11 or newer
- Internet access for APIs you want to test
- A modern browser

## Linux / macOS / Termux

```bash
git clone https://github.com/YOUR_USERNAME/pulse-api-x.git
cd pulse-api-x
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Windows PowerShell

```powershell
git clone https://github.com/YOUR_USERNAME/pulse-api-x.git
cd pulse-api-x
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Troubleshooting

### `ModuleNotFoundError`

Run:

```bash
pip install -r requirements.txt
```

### Port 5000 is busy

Stop the process using the port, or modify the Flask startup configuration in `app.py`.

### API returns an error

Check the target URL, headers, request body, network access and the API's own authentication requirements.
