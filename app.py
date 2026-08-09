
import os, json, sqlite3, secrets
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventario.db"
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("INVENTARIO_SECRET_KEY", "troque-esta-chave-em-producao")
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def normalize(s):
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "")).encode("ascii","ignore").decode()
    return " ".join(s.upper().strip().split())

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('manager','technician')),
      active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS locations(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company TEXT NOT NULL,
      line TEXT NOT NULL,
      location TEXT NOT NULL,
      base_status TEXT,
      expected_atm INTEGER NOT NULL DEFAULT 0,
      expected_validator INTEGER NOT NULL DEFAULT 0,
      expected_pos INTEGER NOT NULL DEFAULT 0,
      survey_status TEXT NOT NULL DEFAULT 'PENDENTE'
        CHECK(survey_status IN ('PENDENTE','EM ANDAMENTO','CONCLUIDA')),
      started_at TEXT,
      completed_at TEXT,
      completed_by INTEGER,
      UNIQUE(company,line,location),
      FOREIGN KEY(completed_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS base_assets(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      asset_key TEXT UNIQUE,
      description TEXT,
      company TEXT,
      station_code TEXT,
      line TEXT,
      locality TEXT,
      serial TEXT,
      qrcode_id TEXT,
      top_id TEXT,
      products TEXT,
      model TEXT,
      supplier TEXT,
      transactions TEXT,
      pix TEXT,
      mount TEXT,
      base_status TEXT
    );

    CREATE TABLE IF NOT EXISTS inventory(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_id INTEGER NOT NULL,
      equipment_type TEXT NOT NULL,
      base_asset_id INTEGER,
      asset_identifier TEXT NOT NULL,
      serial TEXT,
      supplier TEXT,
      model TEXT,
      exact_position TEXT,
      mount TEXT,
      operational_status TEXT NOT NULL,
      connectivity TEXT,
      network_id TEXT,
      label_status TEXT,
      in_base TEXT,
      divergence TEXT,
      notes TEXT,
      technician_id INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT,
      UNIQUE(location_id,equipment_type,asset_identifier),
      FOREIGN KEY(location_id) REFERENCES locations(id),
      FOREIGN KEY(base_asset_id) REFERENCES base_assets(id),
      FOREIGN KEY(technician_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS attachments(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      inventory_id INTEGER NOT NULL,
      original_name TEXT NOT NULL,
      stored_name TEXT NOT NULL,
      mime_type TEXT,
      FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_inventory_location ON inventory(location_id);
    CREATE INDEX IF NOT EXISTS idx_locations_status ON locations(survey_status);
    """)

    # Usuários iniciais
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,?)",
                     ("Administrador","admin",generate_password_hash("Admin@123"),"manager"))
        conn.execute("INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,?)",
                     ("Técnico de Campo","tecnico",generate_password_hash("Tecnico@123"),"technician"))

    # Localidades
    if conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0] == 0:
        data = json.loads((DATA_DIR/"locations.json").read_text(encoding="utf-8"))
        for x in data:
            conn.execute("""INSERT OR IGNORE INTO locations
              (company,line,location,base_status,expected_atm,expected_validator,expected_pos)
              VALUES(?,?,?,?,?,?,?)""",
              (x["company"],x["line"],x["location"],x["base_status"],
               x["expected_atm"],x["expected_validator"],x["expected_pos"]))

    # Ativos-base ATM
    if conn.execute("SELECT COUNT(*) FROM base_assets").fetchone()[0] == 0:
        data = json.loads((DATA_DIR/"atm_assets.json").read_text(encoding="utf-8"))
        for a in data:
            conn.execute("""INSERT OR IGNORE INTO base_assets
              (asset_key,description,company,station_code,line,locality,serial,qrcode_id,top_id,products,model,supplier,transactions,pix,mount,base_status)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (a["asset_key"],a["description"],a["company"],a["station_code"],a["line"],a["locality"],a["serial"],
               a["qrcode_id"],a["top_id"],a["products"],a["model"],a["supplier"],a["transactions"],a["pix"],a["mount"],a["base_status"]))
    conn.commit()
    conn.close()

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner

def manager_required(fn):
    from functools import wraps
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "manager":
            return redirect(url_for("technician"))
        return fn(*args, **kwargs)
    return inner

@app.route("/")
def index():
    if not session.get("user_id"): return redirect(url_for("login"))
    return redirect(url_for("manager" if session.get("role")=="manager" else "technician"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        conn = db()
        u = conn.execute("SELECT * FROM users WHERE username=? AND active=1",(username,)).fetchone()
        conn.close()
        if u and check_password_hash(u["password_hash"], password):
            session.clear()
            session.update(user_id=u["id"], name=u["name"], role=u["role"])
            return redirect(url_for("manager" if u["role"]=="manager" else "technician"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/tecnico")
@login_required
def technician():
    return render_template("technician.html")

@app.route("/gerencial")
@manager_required
def manager():
    return render_template("manager.html")

@app.get("/api/locations")
@login_required
def api_locations():
    conn = db()
    rows = conn.execute("""
      SELECT l.*,
             COUNT(i.id) AS inventoried,
             SUM(CASE WHEN i.operational_status='Operacional' THEN 1 ELSE 0 END) AS operational,
             SUM(CASE WHEN i.operational_status='Inoperante' THEN 1 ELSE 0 END) AS inoperative
      FROM locations l
      LEFT JOIN inventory i ON i.location_id=l.id
      GROUP BY l.id
      ORDER BY l.company,l.line,l.location
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/location/<int:location_id>/inventory")
@login_required
def api_location_inventory(location_id):
    conn=db()
    rows=conn.execute("""
      SELECT i.*,u.name technician,
             (SELECT COUNT(*) FROM attachments a WHERE a.inventory_id=i.id) attachments_count
      FROM inventory i JOIN users u ON u.id=i.technician_id
      WHERE i.location_id=? ORDER BY i.created_at DESC
    """,(location_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/location/<int:location_id>/assets")
@login_required
def api_assets(location_id):
    conn=db()
    loc=conn.execute("SELECT * FROM locations WHERE id=?",(location_id,)).fetchone()
    if not loc:
        conn.close(); return jsonify([])
    # ATM detailed match: tolerate METRO/METRÔ and station code/name differences
    line = normalize(loc["line"])
    company = normalize(loc["company"])
    station_text = normalize(loc["location"])
    base=conn.execute("SELECT * FROM base_assets").fetchall()
    already = {r["base_asset_id"] for r in conn.execute("SELECT base_asset_id FROM inventory WHERE location_id=? AND base_asset_id IS NOT NULL",(location_id,))}
    out=[]
    for a in base:
        ac=normalize(a["company"]).replace("METRO","METRO")
        if normalize(a["line"]) != line: continue
        if company not in ac and ac not in company: continue
        station_name = normalize(a["locality"])
        code = normalize(a["station_code"])
        if station_name and (station_name in station_text or station_text.endswith(station_name)) or (code and station_text.startswith(code+" ")):
            d=dict(a); d["already_inventoried"]=a["id"] in already; out.append(d)
    conn.close()
    return jsonify(out)

@app.post("/api/inventory")
@login_required
def create_inventory():
    location_id = request.form.get("location_id", type=int)
    equipment_type = request.form.get("equipment_type","").strip()
    base_asset_id = request.form.get("base_asset_id", type=int)
    serial = request.form.get("serial","").strip()
    asset_identifier = request.form.get("asset_identifier","").strip() or serial
    if not location_id or not equipment_type or not asset_identifier:
        return jsonify({"ok":False,"error":"Local, tipo e identificação/série são obrigatórios."}),400

    conn=db()
    loc=conn.execute("SELECT * FROM locations WHERE id=?",(location_id,)).fetchone()
    if not loc:
        conn.close(); return jsonify({"ok":False,"error":"Local inválido."}),400

    # trava explícita de duplicidade
    dup=conn.execute("""SELECT i.id,u.name technician,i.created_at
        FROM inventory i JOIN users u ON u.id=i.technician_id
        WHERE i.location_id=? AND i.equipment_type=? AND upper(i.asset_identifier)=upper(?)""",
        (location_id,equipment_type,asset_identifier)).fetchone()
    if dup:
        conn.close()
        return jsonify({"ok":False,"duplicate":True,
            "error":f"Este equipamento já foi inventariado por {dup['technician']} em {dup['created_at']}."}),409

    now=datetime.now().isoformat(timespec="seconds")
    try:
        cur=conn.execute("""INSERT INTO inventory
          (location_id,equipment_type,base_asset_id,asset_identifier,serial,supplier,model,exact_position,mount,
           operational_status,connectivity,network_id,label_status,in_base,divergence,notes,technician_id,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (location_id,equipment_type,base_asset_id,asset_identifier,serial,
           request.form.get("supplier",""),request.form.get("model",""),request.form.get("exact_position",""),
           request.form.get("mount",""),request.form.get("operational_status",""),
           request.form.get("connectivity",""),request.form.get("network_id",""),request.form.get("label_status",""),
           request.form.get("in_base",""),request.form.get("divergence",""),request.form.get("notes",""),
           session["user_id"],now))
        inv_id=cur.lastrowid

        for f in request.files.getlist("attachments"):
            if not f or not f.filename: continue
            safe=secure_filename(f.filename)
            stored=f"{inv_id}_{secrets.token_hex(6)}_{safe}"
            f.save(UPLOAD_DIR/stored)
            conn.execute("INSERT INTO attachments(inventory_id,original_name,stored_name,mime_type) VALUES(?,?,?,?)",
                         (inv_id,f.filename,stored,f.mimetype))

        if loc["survey_status"]=="PENDENTE":
            conn.execute("UPDATE locations SET survey_status='EM ANDAMENTO',started_at=? WHERE id=?",(now,location_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback(); conn.close()
        return jsonify({"ok":False,"duplicate":True,"error":"Registro duplicado para este local."}),409
    conn.close()
    return jsonify({"ok":True,"id":inv_id})

@app.post("/api/location/<int:location_id>/complete")
@login_required
def complete_location(location_id):
    conn=db()
    now=datetime.now().isoformat(timespec="seconds")
    conn.execute("UPDATE locations SET survey_status='CONCLUIDA',completed_at=?,completed_by=? WHERE id=?",
                 (now,session["user_id"],location_id))
    conn.commit();conn.close()
    return jsonify({"ok":True})

@app.post("/api/location/<int:location_id>/reopen")
@manager_required
def reopen_location(location_id):
    conn=db()
    conn.execute("UPDATE locations SET survey_status='EM ANDAMENTO',completed_at=NULL,completed_by=NULL WHERE id=?",(location_id,))
    conn.commit();conn.close()
    return jsonify({"ok":True})

@app.get("/api/dashboard")
@manager_required
def dashboard():
    conn=db()
    totals=conn.execute("""
      SELECT COUNT(*) total,
      SUM(CASE WHEN survey_status='PENDENTE' THEN 1 ELSE 0 END) pending,
      SUM(CASE WHEN survey_status='EM ANDAMENTO' THEN 1 ELSE 0 END) progress,
      SUM(CASE WHEN survey_status='CONCLUIDA' THEN 1 ELSE 0 END) completed,
      SUM(expected_atm+expected_validator+expected_pos) expected
      FROM locations
    """).fetchone()
    inv=conn.execute("""
      SELECT COUNT(*) inventoried,
      SUM(CASE WHEN operational_status='Inoperante' THEN 1 ELSE 0 END) inoperative,
      SUM(CASE WHEN divergence IS NOT NULL AND divergence NOT IN ('','Não','Nao') THEN 1 ELSE 0 END) divergences
      FROM inventory
    """).fetchone()
    by_company=conn.execute("""
      SELECT company,COUNT(*) total,
      SUM(CASE WHEN survey_status='CONCLUIDA' THEN 1 ELSE 0 END) completed,
      SUM(CASE WHEN survey_status='EM ANDAMENTO' THEN 1 ELSE 0 END) progress,
      SUM(CASE WHEN survey_status='PENDENTE' THEN 1 ELSE 0 END) pending
      FROM locations GROUP BY company ORDER BY company
    """).fetchall()
    conn.close()
    return jsonify({"totals":dict(totals),"inventory":dict(inv),"by_company":[dict(x) for x in by_company]})

@app.route("/uploads/<path:name>")
@login_required
def uploaded(name):
    return send_from_directory(UPLOAD_DIR,name)

@app.get("/api/inventory/<int:inventory_id>/attachments")
@login_required
def attachments(inventory_id):
    conn=db()
    rows=conn.execute("SELECT * FROM attachments WHERE inventory_id=?",(inventory_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","5000")), debug=False)
