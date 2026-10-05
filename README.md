# ⚡ PULSE API X

> A modern, local-first API testing dashboard built with Flask, SQLite and vanilla JavaScript.

PULSE API X is a lightweight developer tool for sending HTTP requests, inspecting responses, managing environments, saving requests and reviewing request history — all from a clean web interface.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20App-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🚀 GET, POST, PUT, PATCH, DELETE, HEAD and OPTIONS requests
- 🧩 JSON and raw request bodies
- 🧾 Custom JSON headers
- 🔐 Environment variables such as `{{token}}`, `{{base_url}}` and `{{id}}`
- 💾 Save and manage requests
- 🕘 Request history with status, response time and size
- 🔎 Pretty JSON, raw response and response-header inspection
- 📋 cURL command generation and copy
- 🗃️ SQLite persistence — no external database required
- 📦 Export saved data and environments as JSON
- 📱 Responsive interface for desktop and mobile
- 🌌 Neon/glass developer UI

## 🏗️ Project structure

```text
pulse-api-x/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
├── .env.example
├── docs/
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   └── API.md
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

## 🚀 Quick start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/pulse-api-x.git
cd pulse-api-x
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Linux/macOS/Termux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

For Termux, the same command works after installing Python and the dependencies.

## 🧪 Example request

Try a public test endpoint:

```text
GET https://httpbin.org/get
```

For a JSON POST request:

```text
POST https://httpbin.org/post
```

Body:

```json
{
  "message": "Hello from PULSE API X",
  "source": "local-api-tester"
}
```

## 🔐 Environment variables

Create an environment from the **Environments** section and define variables such as:

```text
base_url = https://example.com
api_version = v1
token = YOUR_TOKEN
```

Then use them in requests:

```text
{{base_url}}/{{api_version}}/users
```

or in headers:

```json
{
  "Authorization": "Bearer {{token}}"
}
```

> Do not commit real API keys, passwords or access tokens. Use local environment data and keep secrets out of Git.

## 📡 Backend endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Dashboard UI |
| POST | `/api/send` | Execute an HTTP request |
| GET | `/api/saved` | List saved requests |
| POST | `/api/saved` | Save a request |
| DELETE | `/api/saved/<id>` | Delete a saved request |
| GET | `/api/history` | Read request history |
| DELETE | `/api/history` | Clear request history |
| GET | `/api/env` | List environments |
| POST | `/api/env` | Create/update an environment |
| GET | `/api/export` | Export application data |

More details are available in [`docs/API.md`](docs/API.md).

## 🛡️ Security notes

PULSE API X is intended primarily for **local development and authorized API testing**.

If you expose the application beyond localhost, add authentication, authorization, HTTPS, rate limiting and stricter outbound-request controls before using it in an untrusted environment.

Never use it to access systems or APIs without permission.

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Usage Guide](docs/USAGE.md)
- [Backend API Reference](docs/API.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 🗺️ Roadmap

Planned ideas:

- [ ] JSON tree response viewer
- [ ] Response diff viewer
- [ ] Request timeline visualization
- [ ] GraphQL mode
- [ ] OpenAPI import
- [ ] Mock API server
- [ ] WebSocket/live request logs
- [ ] Workspace/team collections
- [ ] Optional authentication for remote deployments

## 📄 License

Released under the MIT License. See [`LICENSE`](LICENSE).

## ⭐ Support

If you find the project useful, consider starring the repository and opening an issue with feature requests or bug reports.
