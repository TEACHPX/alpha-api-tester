from flask import Flask, render_template, request, jsonify, Response
import requests, sqlite3, json, time, uuid, re

app=Flask(__name__)
DB="pulse_api.db"

def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS requests(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,method TEXT,url TEXT,
      headers TEXT,body TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS history(
      id INTEGER PRIMARY KEY AUTOINCREMENT,method TEXT,url TEXT,status INTEGER,
      ms REAL,ok INTEGER,created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS environments(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,variables TEXT);
    """)
    c.commit(); c.close()

@app.get("/")
def home(): return render_template("index.html")

def substitute(v, env):
    if not isinstance(v,str): return v
    return re.sub(r"\{\{([^}]+)\}\}",lambda m:str(env.get(m.group(1).strip(),m.group(0))),v)

@app.post("/api/send")
def send():
    d=request.get_json(silent=True) or {}
    method=str(d.get("method","GET")).upper(); url=str(d.get("url","")).strip()
    env=d.get("environment") or {}
    url=substitute(url,env)
    if not url:return jsonify(error="URL is required"),400
    try:
        headers=d.get("headers") or {}
        headers={substitute(str(k),env):substitute(str(v),env) for k,v in headers.items()}
        body=d.get("body")
        if isinstance(body,str): body=substitute(body,env)
        kw={"headers":headers,"timeout":30}
        if method not in {"GET","HEAD","OPTIONS"} and body not in (None,""):
            if isinstance(body,(dict,list)): kw["json"]=body
            else: kw["data"]=body
        t=time.perf_counter(); r=requests.request(method,url,**kw)
        ms=round((time.perf_counter()-t)*1000,2)
        try: out=r.json(); typ="json"
        except ValueError: out=r.text; typ="text"
        c=con(); c.execute("INSERT INTO history(method,url,status,ms,ok) VALUES(?,?,?,?,?)",
                            (method,url,r.status_code,ms,int(r.ok))); c.commit(); c.close()
        return jsonify(success=True,status_code=r.status_code,reason=r.reason,response_time_ms=ms,
                       response_type=typ,headers=dict(r.headers),body=out)
    except requests.exceptions.Timeout:return jsonify(success=False,error="Request timed out"),504
    except requests.exceptions.RequestException as e:return jsonify(success=False,error=str(e)),502
    except Exception as e:return jsonify(success=False,error=str(e)),500

@app.get("/api/saved")
def saved():
    c=con(); rows=c.execute("SELECT * FROM requests ORDER BY id DESC").fetchall(); c.close()
    return jsonify([dict(x) for x in rows])

@app.post("/api/saved")
def save():
    d=request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("url"):return jsonify(error="Name and URL required"),400
    c=con(); cur=c.execute("INSERT INTO requests(name,method,url,headers,body) VALUES(?,?,?,?,?)",
      (d["name"],d.get("method","GET"),d["url"],json.dumps(d.get("headers") or {}),d.get("body","")))
    c.commit(); i=cur.lastrowid; c.close(); return jsonify(success=True,id=i)

@app.delete("/api/saved/<int:i>")
def delete(i):
    c=con(); c.execute("DELETE FROM requests WHERE id=?",(i,)); c.commit(); c.close()
    return jsonify(success=True)

@app.get("/api/history")
def hist():
    c=con(); rows=c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50").fetchall(); c.close()
    return jsonify([dict(x) for x in rows])

@app.delete("/api/history")
def clear_hist():
    c=con(); c.execute("DELETE FROM history"); c.commit(); c.close(); return jsonify(success=True)

@app.get("/api/env")
def envs():
    c=con(); rows=c.execute("SELECT * FROM environments ORDER BY name").fetchall(); c.close()
    return jsonify([dict(x) for x in rows])

@app.post("/api/env")
def env_save():
    d=request.get_json(silent=True) or {}; name=d.get("name","").strip()
    if not name:return jsonify(error="Name required"),400
    c=con()
    c.execute("INSERT INTO environments(name,variables) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET variables=excluded.variables",
              (name,json.dumps(d.get("variables") or {},ensure_ascii=False)))
    c.commit(); c.close(); return jsonify(success=True)

@app.get("/api/export")
def export_data():
    c=con()
    saved=[dict(x) for x in c.execute("SELECT * FROM requests ORDER BY id").fetchall()]
    env=[dict(x) for x in c.execute("SELECT * FROM environments ORDER BY name").fetchall()]
    c.close()
    return Response(json.dumps({"saved_requests":saved,"environments":env},indent=2,ensure_ascii=False),
                    mimetype="application/json",
                    headers={"Content-Disposition":"attachment; filename=pulse_export.json"})

if __name__=="__main__":
    init(); app.run(host="0.0.0.0",port=5000,debug=False)
