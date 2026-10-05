from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import time
import re
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_nmxOy1bVkv0Q@ep-shy-sky-b5ugtj4f-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require").strip()


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    try:
        import psycopg
        return psycopg.connect(
            DATABASE_URL,
            connect_timeout=10
        )
    except ImportError:
        raise RuntimeError("psycopg is not installed")


def init_db():
    with db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS requests(
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                body TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS history(
                id BIGSERIAL PRIMARY KEY,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                status INTEGER,
                ms DOUBLE PRECISION,
                ok BOOLEAN,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS environments(
                id BIGSERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                variables TEXT
            );
        """)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def substitute(value, env):
    if not isinstance(value, str):
        return value

    return re.sub(
        r"\{\{([^}]+)\}\}",
        lambda m: str(
            env.get(
                m.group(1).strip(),
                m.group(0)
            )
        ),
        value
    )


def safe_json(value, default=None):
    try:
        return json.loads(value)
    except Exception:
        return default


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

@app.before_request
def ensure_database():
    if request.path.startswith("/api/") and DATABASE_URL:
        try:
            init_db()
        except Exception:
            pass


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/api/health")
def health():

    if not DATABASE_URL:
        return jsonify(
            success=False,
            database="not_configured",
            error="DATABASE_URL is not configured"
        ), 503

    try:
        with db() as c:
            c.execute("SELECT 1")

        return jsonify(
            success=True,
            database="connected"
        )

    except Exception as e:
        return jsonify(
            success=False,
            database="error",
            error=str(e)
        ), 503


# --------------------------------------------------
# SEND REQUEST
# --------------------------------------------------

@app.post("/api/send")
def send():

    data = request.get_json(silent=True) or {}

    method = str(
        data.get("method", "GET")
    ).upper()

    env = data.get("environment") or {}

    url = substitute(
        str(data.get("url", "")).strip(),
        env
    )

    if not url:
        return jsonify(
            success=False,
            error="URL is required"
        ), 400

    try:

        headers = data.get("headers") or {}

        if not isinstance(headers, dict):
            return jsonify(
                success=False,
                error="Headers must be a JSON object"
            ), 400

        headers = {
            substitute(str(k), env):
            substitute(str(v), env)
            for k, v in headers.items()
        }

        body = data.get("body")

        if isinstance(body, str):
            body = substitute(body, env)

        options = {
            "headers": headers,
            "timeout": 30,
            "allow_redirects": True
        }

        if method not in {
            "GET",
            "HEAD",
            "OPTIONS"
        } and body not in (None, ""):

            if isinstance(body, (dict, list)):
                options["json"] = body
            else:
                options["data"] = body

        start = time.perf_counter()

        response = requests.request(
            method,
            url,
            **options
        )

        elapsed = round(
            (time.perf_counter() - start) * 1000,
            2
        )

        try:
            output = response.json()
            response_type = "json"

        except ValueError:
            output = response.text
            response_type = "text"

        # History
        with db() as c:
            c.execute(
                """
                INSERT INTO history
                (method,url,status,ms,ok)
                VALUES(%s,%s,%s,%s,%s)
                """,
                (
                    method,
                    url,
                    response.status_code,
                    elapsed,
                    response.ok
                )
            )

        return jsonify(
            success=True,
            status_code=response.status_code,
            reason=response.reason,
            response_time_ms=elapsed,
            response_type=response_type,
            headers=dict(response.headers),
            body=output
        )

    except requests.exceptions.Timeout:

        return jsonify(
            success=False,
            error="Request timed out"
        ), 504

    except requests.exceptions.RequestException as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 502

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


# --------------------------------------------------
# SAVED REQUESTS
# --------------------------------------------------

@app.get("/api/saved")
def saved():

    try:

        with db() as c:

            rows = c.execute(
                """
                SELECT *
                FROM requests
                ORDER BY id DESC
                """
            ).fetchall()

            columns = [
                x.name
                for x in c.description
            ]

        data = [
            dict(zip(columns, row))
            for row in rows
        ]

        return jsonify(
            success=True,
            saved_requests=data
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e),
            saved_requests=[]
        ), 500


@app.post("/api/saved")
def save():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    url = str(
        data.get("url", "")
    ).strip()

    if not name or not url:

        return jsonify(
            success=False,
            error="Name and URL required"
        ), 400

    try:

        with db() as c:

            row = c.execute(
                """
                INSERT INTO requests
                (name,method,url,headers,body)
                VALUES(%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    name,
                    data.get("method", "GET"),
                    url,
                    json.dumps(
                        data.get("headers") or {}
                    ),
                    data.get("body", "")
                )
            ).fetchone()

        return jsonify(
            success=True,
            id=row[0]
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


@app.delete("/api/saved/<int:item_id>")
def delete_saved(item_id):

    try:

        with db() as c:
            c.execute(
                "DELETE FROM requests WHERE id=%s",
                (item_id,)
            )

        return jsonify(
            success=True
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


# --------------------------------------------------
# HISTORY
# --------------------------------------------------

@app.get("/api/history")
def history():

    try:

        with db() as c:

            rows = c.execute(
                """
                SELECT *
                FROM history
                ORDER BY id DESC
                LIMIT 50
                """
            ).fetchall()

            columns = [
                x.name
                for x in c.description
            ]

        data = [
            dict(zip(columns, row))
            for row in rows
        ]

        return jsonify(
            success=True,
            history=data
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e),
            history=[]
        ), 500


@app.delete("/api/history")
def clear_history():

    try:

        with db() as c:
            c.execute(
                "DELETE FROM history"
            )

        return jsonify(
            success=True
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


# --------------------------------------------------
# ENVIRONMENTS
# --------------------------------------------------

@app.get("/api/env")
def get_environments():

    try:

        with db() as c:

            rows = c.execute(
                """
                SELECT *
                FROM environments
                ORDER BY name
                """
            ).fetchall()

            columns = [
                x.name
                for x in c.description
            ]

        data = [
            dict(zip(columns, row))
            for row in rows
        ]

        return jsonify(
            success=True,
            environments=data
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e),
            environments=[]
        ), 500


@app.post("/api/env")
def save_environment():

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    if not name:

        return jsonify(
            success=False,
            error="Environment name required"
        ), 400

    variables = data.get(
        "variables"
    ) or {}

    if not isinstance(variables, dict):

        return jsonify(
            success=False,
            error="Variables must be a JSON object"
        ), 400

    try:

        with db() as c:

            c.execute(
                """
                INSERT INTO environments
                (name,variables)
                VALUES(%s,%s)

                ON CONFLICT(name)
                DO UPDATE SET
                variables=EXCLUDED.variables
                """,
                (
                    name,
                    json.dumps(
                        variables,
                        ensure_ascii=False
                    )
                )
            )

        return jsonify(
            success=True
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


# --------------------------------------------------
# EXPORT
# --------------------------------------------------

@app.get("/api/export")
def export_data():

    try:

        with db() as c:

            saved_rows = c.execute(
                """
                SELECT *
                FROM requests
                ORDER BY id
                """
            ).fetchall()

            saved_columns = [
                x.name
                for x in c.description
            ]

            env_rows = c.execute(
                """
                SELECT *
                FROM environments
                ORDER BY name
                """
            ).fetchall()

            env_columns = [
                x.name
                for x in c.description
            ]

        payload = {

            "saved_requests": [
                dict(zip(
                    saved_columns,
                    row
                ))
                for row in saved_rows
            ],

            "environments": [
                dict(zip(
                    env_columns,
                    row
                ))
                for row in env_rows
            ]

        }

        return Response(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=str
            ),
            mimetype="application/json",
            headers={
                "Content-Disposition":
                "attachment; filename=pulse_export.json"
            }
        )

    except Exception as e:

        return jsonify(
            success=False,
            error=str(e)
        ), 500


# --------------------------------------------------
# LOCAL DEVELOPMENT
# --------------------------------------------------

if __name__ == "__main__":

    if DATABASE_URL:

        try:
            init_db()
        except Exception as e:
            print(
                "Database initialization failed:",
                e
            )

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )
