from flask import Flask, render_template, request, jsonify, Response
import requests, json, time, re, os
from urllib.parse import urlparse

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    try:
        import psycopg
        return psycopg.connect(DATABASE_URL, connect_timeout=10)
    except ImportError:
        raise RuntimeError("psycopg is not installed")


def init_db():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS requests(
          id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,method TEXT NOT NULL,url TEXT NOT NULL,
          headers TEXT,body TEXT,created_at TIMESTAMPTZ DEFAULT NOW());
        CREATE TABLE IF NOT EXISTS history(
          id BIGSERIAL PRIMARY KEY,method TEXT NOT NULL,url TEXT NOT NULL,status INTEGER,
          ms DOUBLE PRECISION,ok BOOLEAN,created_at TIMESTAMPTZ DEFAULT NOW());
        CREATE TABLE IF NOT EXISTS environments(
          id BIGSERIAL PRIMARY KEY,name TEXT UNIQUE NOT NULL,variables TEXT);
        """)


def substitute(v, env):
    if not isinstance(v, str):
        return v
    return re.sub(r"\{\{([^}]+)\}\}", lambda m: str(env.get(m.group(1).strip(), m.group(0))), v)


def require_db():
    if not DATABASE_URL:
        return jsonify(success=False, error="DATABASE_URL is not configured"), 503
    return None


@app.before_request
def ensure_database():
    if request.path.startswith("/api/") and DATABASE_URL:
        init_db()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    if not DATABASE_URL:
        return jsonify(success=False, database="not_configured"), 503
    try:
        with db() as c:
            c.execute("SELECT 1")
        return jsonify(success=True, database="connected")
    except Exception as e:
        return jsonify(success=False, database="error", error=str(e)), 503


@app.post("/api/send")
def send():
    d = request.get_json(silent=True) or {}
    method = str(d.get("method", "GET")).upper()
    url = substitute(str(d.get("url", "")).strip(), d.get("environment") or {})
    env = d.get("environment") or {}
    if not url:
        return jsonify(error="URL is required"), 400
    try:
        headers = d.get("headers") or {}
        headers = {substitute(str(k), env): substitute(str(v), env) for k, v in headers.items()}
        body = d.get("body")
        if isinstance(body, str):
            body = substitute(body, env)
        kw = {"headers": headers, "timeout": 30, "allow_redirects": True}
        if method not in {"GET", "HEAD", "OPTIONS"} and body not in (None, ""):
            if isinstance(body, (dict, list)):
                kw["json"] = body
            else:
                kw["data"] = body
        t = time.perf_counter()
        r = requests.request(method, url, **kw)
        ms = round((time.perf_counter() - t) * 1000, 2)
        try:
            out = r.json(); typ = "json"
        except ValueError:
            out = r.text; typ = "text"
        with db() as c:
            c.execute("INSERT INTO history(method,url,status,ms,ok) VALUES(%s,%s,%s,%s,%s)",
                      (method, url, r.status_code, ms, r.ok))
        return jsonify(success=True, status_code=r.status_code, reason=r.reason,
                       response_time_ms=ms, response_type=typ,
                       headers=dict(r.headers), body=out)
    except requests.exceptions.Timeout:
        return jsonify(success=False, error="Request timed out"), 504
    except requests.exceptions.RequestException as e:
        return jsonify(success=False, error=str(e)), 502
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.get("/api/saved")
def saved():
    try:
        with db() as c:
            rows = c.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
            cols = [x.name for x in c.description]
        return jsonify([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.post("/api/saved")
def save():
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("url"):
        return jsonify(error="Name and URL required"), 400
    try:
        with db() as c:
            row = c.execute("INSERT INTO requests(name,method,url,headers,body) VALUES(%s,%s,%s,%s,%s) RETURNING id",
                            (d["name"], d.get("method", "GET"), d["url"],
                             json.dumps(d.get("headers") or {}), d.get("body", ""))).fetchone()
        return jsonify(success=True, id=row[0])
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.delete("/api/saved/<int:i>")
def delete(i):
    try:
        with db() as c:
            c.execute("DELETE FROM requests WHERE id=%s", (i,))
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.get("/api/history")
def hist():
    try:
        with db() as c:
            rows = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50").fetchall()
            cols = [x.name for x in c.description]
        return jsonify([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.delete("/api/history")
def clear_hist():
    try:
        with db() as c:
            c.execute("DELETE FROM history")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.get("/api/env")
def envs():
    try:
        with db() as c:
            rows = c.execute("SELECT * FROM environments ORDER BY name").fetchall()
            cols = [x.name for x in c.description]
        return jsonify([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.post("/api/env")
def env_save():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    if not name:
        return jsonify(error="Name required"), 400
    try:
        with db() as c:
            c.execute("""INSERT INTO environments(name,variables) VALUES(%s,%s)
                         ON CONFLICT(name) DO UPDATE SET variables=EXCLUDED.variables""",
                      (name, json.dumps(d.get("variables") or {}, ensure_ascii=False)))
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.get("/api/export")
def export_data():
    try:
        with db() as c:
            saved = c.execute("SELECT * FROM requests ORDER BY id").fetchall()
            cols1 = [x.name for x in c.description]
            env = c.execute("SELECT * FROM environments ORDER BY name").fetchall()
            cols2 = [x.name for x in c.description]
        payload = {
            "saved_requests": [dict(zip(cols1, row)) for row in saved],
            "environments": [dict(zip(cols2, row)) for row in env]
        }
        return Response(json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                        mimetype="application/json",
                        headers={"Content-Disposition": "attachment; filename=pulse_export.json"})
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# Vercel imports this Flask object from api/index.py.
# Local development can still use: python app.py
if __name__ == "__main__":
    if DATABASE_URL:
        init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
