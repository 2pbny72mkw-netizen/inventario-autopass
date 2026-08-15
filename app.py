import os
import json
import secrets
import unicodedata
import re
import zipfile
import io
import boto3
import uuid
import mimetypes
import hashlib
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import time
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Index, func, case, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError, BotoCoreError
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BASE_DATA_VERSION = "1408-5"
DASHBOARD_RELEASE = "v1.4-operacional-dashboard-v5"
# Denominadores executivos oficiais informados para o parque contratado.
OFFICIAL_PARK = {
    "ATM": 590,
    "POS": 972,
    "VALIDADOR": 629,  # Recarga
    "BLOQUEIO": 1610,
}
OFFICIAL_PARK_TOTAL = sum(OFFICIAL_PARK.values())  # 3.801
EXPECTED_CACHE_TTL_SECONDS = 600
_expected_cache = {"at": 0.0, "data": None}
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Render fornece DATABASE_URL. Para teste local, usa SQLite automaticamente.
database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if not database_url:
    database_url = f"sqlite:///{BASE_DIR / 'inventario_local.db'}"

app = Flask(__name__)
app.secret_key = os.environ.get("INVENTARIO_SECRET_KEY", "chave-local-apenas-para-desenvolvimento")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 160 * 1024 * 1024

# Mantém conexões saudáveis em hospedagens gerenciadas.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    username = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    
    user_code = db.Column(db.String(30), unique=True, index=True)
    email = db.Column(db.String(180), unique=True, index=True)
    phone = db.Column(db.String(30), unique=True, index=True)
    photo_url = db.Column(db.String(500))


class TechnicianPosition(db.Model):
    __tablename__ = "technician_positions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    captured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = db.Column(db.String(40), nullable=False, default="browser")

class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(180), nullable=False)
    line = db.Column(db.String(180), nullable=False)
    location = db.Column(db.String(220), nullable=False)
    base_status = db.Column(db.String(80))
    expected_atm = db.Column(db.Integer, nullable=False, default=0)
    expected_validator = db.Column(db.Integer, nullable=False, default=0)
    expected_pos = db.Column(db.Integer, nullable=False, default=0)
    survey_status = db.Column(db.String(30), nullable=False, default="PENDENTE", index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reference_latitude = db.Column(db.Float)
    reference_longitude = db.Column(db.Float)
    reference_source = db.Column(db.String(120))
    reference_updated_at = db.Column(db.DateTime)

    __table_args__ = (
        UniqueConstraint("company", "line", "location", name="uq_location_company_line_name"),
    )


class BaseAsset(db.Model):
    __tablename__ = "base_assets"
    id = db.Column(db.Integer, primary_key=True)
    asset_key = db.Column(db.String(255), unique=True, index=True)
    description = db.Column(db.String(500))
    company = db.Column(db.String(180))
    station_code = db.Column(db.String(80))
    line = db.Column(db.String(180))
    locality = db.Column(db.String(220))
    serial = db.Column(db.String(180))
    qrcode_id = db.Column(db.String(180))
    top_id = db.Column(db.String(180))
    products = db.Column(db.String(255))
    model = db.Column(db.String(180))
    supplier = db.Column(db.String(180))
    transactions = db.Column(db.String(255))
    pix = db.Column(db.String(80))
    mount = db.Column(db.String(80))
    base_status = db.Column(db.String(80))
    equipment_type = db.Column(db.String(50), index=True)
    location_code = db.Column(db.String(80))
    terminal_number = db.Column(db.String(120))
    application = db.Column(db.String(180))
    bom_id = db.Column(db.String(120))
    bu_id = db.Column(db.String(120))
    software_version = db.Column(db.String(120))
    quantity = db.Column(db.Integer)
    base_notes = db.Column(db.Text)
    leasing_status = db.Column(db.String(120))
    contract_end = db.Column(db.String(80))
    installation_type = db.Column(db.String(180))
    installation_date = db.Column(db.String(80))


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    equipment_type = db.Column(db.String(100), nullable=False)
    base_asset_id = db.Column(db.Integer, db.ForeignKey("base_assets.id"))
    asset_identifier = db.Column(db.String(220), nullable=False)
    serial = db.Column(db.String(220))
    supplier = db.Column(db.String(180))
    model = db.Column(db.String(180))
    application = db.Column(db.String(180))
    bom_id = db.Column(db.String(120))
    bu_id = db.Column(db.String(120))
    validator_top_id = db.Column(db.String(120))
    software_version = db.Column(db.String(120))
    exact_position = db.Column(db.Text)
    mount = db.Column(db.String(100))
    operational_status = db.Column(db.String(120), nullable=False)
    connectivity = db.Column(db.String(120))
    network_id = db.Column(db.String(220))
    label_status = db.Column(db.String(80))
    in_base = db.Column(db.String(80))
    divergence = db.Column(db.String(180))
    notes = db.Column(db.Text)
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    gps_accuracy = db.Column(db.Float)
    gps_captured_at = db.Column(db.DateTime)

    __table_args__ = (
        UniqueConstraint(
            "location_id", "equipment_type", "asset_identifier",
            name="uq_inventory_location_type_identifier"
        ),
    )


class Attachment(db.Model):
    __tablename__ = "attachments"
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False)
    original_name = db.Column(db.String(300), nullable=False)
    stored_name = db.Column(db.String(400), nullable=False)
    mime_type = db.Column(db.String(180))


Index("idx_inventory_location", Inventory.location_id)


class FieldEvidenceVisit(db.Model):
    __tablename__ = "field_evidence_visits"
    id = db.Column(db.Integer, primary_key=True)
    source_key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    source_batch = db.Column(db.String(120), index=True)
    source_date = db.Column(db.String(20))
    source_time = db.Column(db.String(20))
    author = db.Column(db.String(180))
    station_raw = db.Column(db.String(220))
    line_raw = db.Column(db.String(120))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), index=True)
    match_confidence = db.Column(db.String(40), index=True)
    match_score = db.Column(db.Float)
    report_text = db.Column(db.Text)
    competition_text = db.Column(db.Text)
    storage_source = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class FieldEvidenceItem(db.Model):
    __tablename__ = "field_evidence_items"
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("field_evidence_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_type = db.Column(db.String(80), nullable=False, index=True)
    identifier = db.Column(db.String(220), nullable=False)
    model = db.Column(db.String(180))
    serial = db.Column(db.String(220))
    patrimony = db.Column(db.String(120))
    operational_status = db.Column(db.String(120))
    source_line = db.Column(db.Text)
    base_asset_id = db.Column(db.Integer, db.ForeignKey("base_assets.id"))
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"))
    audit_status = db.Column(db.String(80), index=True)
    audit_detail = db.Column(db.Text)

    __table_args__ = (
        UniqueConstraint("visit_id", "equipment_type", "identifier", name="uq_field_evidence_visit_item"),
    )


class FieldEvidenceMedia(db.Model):
    __tablename__ = "field_evidence_media"
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("field_evidence_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    sha256 = db.Column(db.String(64), nullable=False, unique=True, index=True)
    original_name = db.Column(db.String(300), nullable=False)
    mime_type = db.Column(db.String(180))
    storage_kind = db.Column(db.String(30), nullable=False)
    storage_key = db.Column(db.String(700), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


Index("idx_field_evidence_location", FieldEvidenceVisit.location_id)
Index("idx_field_evidence_item_audit", FieldEvidenceItem.audit_status)


def normalize(value):
    value = unicodedata.normalize("NFD", value or "").encode("ascii", "ignore").decode()
    return " ".join(value.upper().strip().split())


def seed_data():
    # Usuários iniciais somente quando a tabela está vazia.
    if User.query.count() == 0:
        db.session.add_all([
            User(
                name="Administrador",
                username="admin",
                password_hash=generate_password_hash("Admin@123"),
                role="manager",
                active=True
            ),
            User(
                name="Técnico de Campo",
                username="tecnico",
                password_hash=generate_password_hash("Tecnico@123"),
                role="technician",
                active=True
            )
        ])
        db.session.commit()

    if Location.query.count() == 0:
        data = json.loads((DATA_DIR / "locations.json").read_text(encoding="utf-8"))
        for x in data:
            db.session.add(Location(
                company=x["company"],
                line=x["line"],
                location=x["location"],
                base_status=x.get("base_status", ""),
                expected_atm=x.get("expected_atm", 0),
                expected_validator=x.get("expected_validator", 0),
                expected_pos=x.get("expected_pos", 0),
                survey_status="PENDENTE"
            ))
        db.session.commit()

    if BaseAsset.query.count() == 0:
        data = json.loads((DATA_DIR / "atm_assets.json").read_text(encoding="utf-8"))
        for a in data:
            db.session.add(BaseAsset(
                asset_key=a.get("asset_key", ""),
                description=a.get("description", ""),
                company=a.get("company", ""),
                station_code=a.get("station_code", ""),
                line=a.get("line", ""),
                locality=a.get("locality", ""),
                serial=a.get("serial", ""),
                qrcode_id=a.get("qrcode_id", ""),
                top_id=a.get("top_id", ""),
                products=a.get("products", ""),
                model=a.get("model", ""),
                supplier=a.get("supplier", ""),
                transactions=a.get("transactions", ""),
                pix=a.get("pix", ""),
                mount=a.get("mount", ""),
                base_status=a.get("base_status", ""),
                equipment_type="ATM"
            ))
        db.session.commit()



def r2_client():
    endpoint = os.environ.get("R2_ENDPOINT_URL", "").strip()
    access_key = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()

    if not endpoint or not access_key or not secret_key:
        raise RuntimeError("Variáveis do R2 não configuradas no Render.")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto"
    )


def r2_test_connection():
    bucket = os.environ.get("R2_BUCKET_NAME", "").strip()
    if not bucket:
        return False, "R2_BUCKET_NAME não configurado."

    key = "diagnostico/render-r2-test.txt"
    body = b"Inventario Autopass - teste de conexao Render para Cloudflare R2"

    try:
        client = r2_client()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="text/plain; charset=utf-8"
        )
        obj = client.get_object(Bucket=bucket, Key=key)
        returned = obj["Body"].read()

        if returned != body:
            return False, "O arquivo foi gravado, mas a leitura retornou conteúdo diferente."

        client.delete_object(Bucket=bucket, Key=key)
        return True, "Conexão validada: gravação, leitura e exclusão concluídas."
    except (ClientError, BotoCoreError, RuntimeError) as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner


def manager_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "manager":
            return redirect(url_for("manager" if session.get("role") == "consultation" else "technician"))
        return fn(*args, **kwargs)
    return inner


def dashboard_required(fn):
    """Permite acesso ao painel para Gestor e Consulta."""
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") not in ("manager", "consultation"):
            return redirect(url_for("technician"))
        return fn(*args, **kwargs)
    return inner


def field_required(fn):
    """Permite gravação de campo apenas para Gestor e Técnico."""
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") not in ("manager", "technician"):
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Perfil Consulta possui acesso somente leitura."}), 403
            return redirect(url_for("manager"))
        return fn(*args, **kwargs)
    return inner


@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return redirect(url_for("manager" if session.get("role") in ("manager", "consultation") else "technician"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session.update(user_id=user.id, name=user.name, role=user.role)
            return redirect(url_for("manager" if user.role in ("manager", "consultation") else "technician"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/tecnico")
@field_required
def technician():
    return render_template("technician.html")


@app.route("/gerencial")
@dashboard_required
def manager():
    return render_template("manager.html")



def _load_technician_schedule():
    path = DATA_DIR / "technician_schedule_v5.json"
    if not path.exists():
        return {"technicians": [], "support": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _schedule_today(schedule, today=None):
    today = today or datetime.now().date().isoformat()
    return [x for x in schedule.get("technicians", []) if today in x.get("days", [])]


@app.post("/api/tecnico/position")
@field_required
def technician_position_update():
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("latitude")); lon = float(data.get("longitude"))
        acc = float(data.get("accuracy")) if data.get("accuracy") is not None else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Coordenadas inválidas"}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"ok": False, "error": "Coordenadas fora do intervalo"}), 400
    row = TechnicianPosition(user_id=session["user_id"], latitude=lat, longitude=lon, accuracy=acc, captured_at=datetime.utcnow())
    db.session.add(row); db.session.commit()
    return jsonify({"ok": True, "captured_at": row.captured_at.isoformat() + "Z"})


@app.get("/api/equipes/status")
@dashboard_required
def teams_status_api():
    schedule = _load_technician_schedule()
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
    scheduled = _schedule_today(schedule, today)
    users = User.query.filter(User.active.is_(True)).all()
    users_by_name = {normalize(u.name): u for u in users}
    rows=[]
    now=datetime.utcnow()
    for tech in scheduled:
        user=users_by_name.get(normalize(tech.get("name")))
        pos=None
        if user:
            pos=TechnicianPosition.query.filter_by(user_id=user.id).order_by(TechnicianPosition.captured_at.desc()).first()
        minutes=None
        if pos: minutes=max(0,int((now-pos.captured_at).total_seconds()//60))
        if minutes is None: freshness="SEM SINAL"
        elif minutes <= 5: freshness="ATUAL"
        elif minutes <= 15: freshness="ATENÇÃO"
        else: freshness="ATRASADO"
        rows.append({
            **tech,
            "user_id": user.id if user else None,
            "photo_url": (f"/usuarios/{user.id}/foto" if user and user.photo_url else None),
            "latitude": pos.latitude if pos else None,
            "longitude": pos.longitude if pos else None,
            "accuracy": pos.accuracy if pos else None,
            "captured_at": (pos.captured_at.isoformat() + "Z") if pos else None,
            "minutes_since": minutes,
            "freshness": freshness,
        })
    local_now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return jsonify({
        "ok": True,
        "date": today,
        "time": local_now.strftime("%H:%M"),
        "scheduled": len(rows),
        "technicians": rows,
        "support": schedule.get("support", [])
    })


@app.get("/equipes")
@dashboard_required
def teams_page():
    return render_template("teams.html")


@app.get("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"ok": True, "database": "connected", "release": "v5.1-central-operacional"})
    except Exception as exc:
        return jsonify({"ok": False, "database": "error", "detail": str(exc)}), 500


def _canonical_equipment_type(value):
    value = normalize(value)
    aliases = {
        "ATM": "ATM", "VALIDADOR": "VALIDADOR", "VALIDADOR DE RECARGA": "VALIDADOR",
        "POS": "POS", "POS DE BILHETERIA": "POS", "TDI": "TDI", "BLOQUEIO": "BLOQUEIO"
    }
    return aliases.get(value, value or "OUTRO")


def _base_asset_matches_location(asset, loc):
    if "INATIVO" in normalize(asset.base_status):
        return False
    asset_line = re.sub(r"^L(?=\\d{2}\\s*-)", "", normalize(asset.line))
    loc_line = re.sub(r"^L(?=\\d{2}\\s*-)", "", normalize(loc.line))
    if asset_line != loc_line:
        return False
    ac, lc = normalize(asset.company), normalize(loc.company)
    if ac and lc and lc not in ac and ac not in lc:
        return False
    station_text = normalize(loc.location)
    station_name = normalize(asset.locality)
    code = normalize(asset.location_code or asset.station_code)
    return bool((station_name and (station_name in station_text or station_text.endswith(station_name))) or
                (code and station_text.startswith(code + " ")))


def _normalize_line_key(value):
    return re.sub(r"^L(?=\d{2}\s*-)", "", normalize(value))


def _invalidate_expected_cache():
    _expected_cache["at"] = 0.0
    _expected_cache["data"] = None


def _expected_assets_by_location(force=False):
    """Associa a base detalhada às localidades com índice por linha e cache em memória.

    A versão anterior comparava cada ativo com todas as localidades em toda chamada.
    Esta versão limita candidatos pela linha e reutiliza o resultado por 10 minutos.
    """
    now = time.monotonic()
    if (
        not force
        and _expected_cache.get("data") is not None
        and now - float(_expected_cache.get("at") or 0) < EXPECTED_CACHE_TTL_SECONDS
    ):
        return _expected_cache["data"]

    locations = Location.query.all()
    result = {
        loc.id: {"ATM": 0, "VALIDADOR": 0, "POS": 0, "TDI": 0, "BLOQUEIO": 0}
        for loc in locations
    }

    by_line = {}
    for loc in locations:
        by_line.setdefault(_normalize_line_key(loc.line), []).append(loc)

    assets = BaseAsset.query.all()
    valid_types = {"ATM", "VALIDADOR", "POS", "TDI", "BLOQUEIO"}
    for asset in assets:
        if "INATIVO" in normalize(asset.base_status):
            continue
        typ = _canonical_equipment_type(asset.equipment_type)
        if typ not in valid_types:
            continue

        candidates = by_line.get(_normalize_line_key(asset.line), ())
        if not candidates:
            continue

        qty = max(1, int(asset.quantity or 1))
        ac = normalize(asset.company)
        station_name = normalize(asset.locality)
        code = normalize(asset.location_code or asset.station_code)

        for loc in candidates:
            lc = normalize(loc.company)
            if ac and lc and lc not in ac and ac not in lc:
                continue
            station_text = normalize(loc.location)
            matched = bool(
                (station_name and (station_name in station_text or station_text.endswith(station_name)))
                or (code and station_text.startswith(code + " "))
            )
            if matched:
                result[loc.id][typ] += qty
                break

    _expected_cache["at"] = now
    _expected_cache["data"] = result
    return result


@app.get("/api/locations")
@login_required
def api_locations():
    expected_map = _expected_assets_by_location()

    # Inventário agregado em consultas pequenas, sem outer join pesado em todas as colunas.
    inv_rows = (
        db.session.query(
            Inventory.location_id,
            Inventory.equipment_type,
            func.count(Inventory.id),
            func.coalesce(func.sum(case((Inventory.operational_status == "Inoperante", 1), else_=0)), 0),
            func.coalesce(func.sum(case((
                Inventory.divergence.isnot(None)
                & (~Inventory.divergence.in_(["", "Não", "Nao"]))
            , 1), else_=0)), 0),
        )
        .group_by(Inventory.location_id, Inventory.equipment_type)
        .all()
    )

    inv_by_loc = {}
    for location_id, equipment_type, count, inop, divergence_count in inv_rows:
        bucket = inv_by_loc.setdefault(location_id, {
            "total": 0,
            "inoperative": 0,
            "divergences": 0,
            "by_type": {"ATM":0,"VALIDADOR":0,"POS":0,"TDI":0,"BLOQUEIO":0,"OUTRO":0},
        })
        canonical = _canonical_equipment_type(equipment_type)
        if canonical not in bucket["by_type"]:
            canonical = "OUTRO"
        bucket["by_type"][canonical] += int(count or 0)
        bucket["total"] += int(count or 0)
        bucket["inoperative"] += int(inop or 0)
        bucket["divergences"] += int(divergence_count or 0)

    rows = Location.query.order_by(Location.company, Location.line, Location.location).all()

    out = []
    for loc in rows:
        inv = inv_by_loc.get(loc.id, {
            "total":0, "inoperative":0, "divergences":0,
            "by_type":{"ATM":0,"VALIDADOR":0,"POS":0,"TDI":0,"BLOQUEIO":0,"OUTRO":0}
        })
        exp_by_type = expected_map.get(loc.id, {})
        out.append({
            "id": loc.id,
            "company": loc.company,
            "line": loc.line,
            "location": loc.location,
            "base_status": loc.base_status,
            "expected_atm": loc.expected_atm,
            "expected_validator": loc.expected_validator,
            "expected_pos": loc.expected_pos,
            "expected_by_type": exp_by_type,
            "expected_total": sum(exp_by_type.values()),
            "inventoried_by_type": inv["by_type"],
            "survey_status": loc.survey_status,
            "started_at": loc.started_at.isoformat(timespec="seconds") if loc.started_at else None,
            "completed_at": loc.completed_at.isoformat(timespec="seconds") if loc.completed_at else None,
            "completed_by": loc.completed_by,
            "reference_latitude": loc.reference_latitude,
            "reference_longitude": loc.reference_longitude,
            "reference_source": loc.reference_source,
            "reference_updated_at": loc.reference_updated_at.isoformat(timespec="seconds") if loc.reference_updated_at else None,
            "inventoried": int(inv["total"]),
            "inoperative": int(inv["inoperative"]),
            "divergences": int(inv["divergences"]),
        })
    return jsonify(out)


@app.get("/api/location/<int:location_id>/inventory")
@login_required
def api_location_inventory(location_id):
    rows = (
        db.session.query(Inventory, User.name.label("technician"))
        .join(User, User.id == Inventory.technician_id)
        .filter(Inventory.location_id == location_id)
        .order_by(Inventory.created_at.desc())
        .all()
    )
    out = []
    for inv, technician_name in rows:
        attachment_count = Attachment.query.filter_by(inventory_id=inv.id).count()
        out.append({
            "id": inv.id,
            "location_id": inv.location_id,
            "equipment_type": inv.equipment_type,
            "base_asset_id": inv.base_asset_id,
            "asset_identifier": inv.asset_identifier,
            "serial": inv.serial,
            "supplier": inv.supplier,
            "model": inv.model,
            "application": inv.application,
            "bom_id": inv.bom_id,
            "bu_id": inv.bu_id,
            "validator_top_id": inv.validator_top_id,
            "software_version": inv.software_version,
            "exact_position": inv.exact_position,
            "mount": inv.mount,
            "operational_status": inv.operational_status,
            "connectivity": inv.connectivity,
            "network_id": inv.network_id,
            "label_status": inv.label_status,
            "in_base": inv.in_base,
            "divergence": inv.divergence,
            "notes": inv.notes,
            "created_at": inv.created_at.isoformat(timespec="seconds"),
            "updated_at": inv.updated_at.isoformat(timespec="seconds") if inv.updated_at else None,
            "latitude": inv.latitude,
            "longitude": inv.longitude,
            "gps_accuracy": inv.gps_accuracy,
            "gps_captured_at": inv.gps_captured_at.isoformat(timespec="seconds") if inv.gps_captured_at else None,
            "technician": technician_name,
            "attachments_count": attachment_count,
            "can_manage": session.get("role") == "manager",
        })
    return jsonify(out)


@app.get("/api/location/<int:location_id>/assets")
@login_required
def api_assets(location_id):
    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify([])

    requested_type = normalize(request.args.get("equipment_type", ""))
    type_aliases = {
        "ATM": "ATM",
        "VALIDADOR": "VALIDADOR",
        "VALIDADOR DE RECARGA": "VALIDADOR",
        "POS": "POS",
        "POS DE BILHETERIA": "POS",
        "TDI": "TDI",
        "BLOQUEIO": "BLOQUEIO",
    }
    requested_type = type_aliases.get(requested_type, requested_type)

    line = normalize(loc.line)
    company = normalize(loc.company)
    station_text = normalize(loc.location)

    already = {
        x[0]
        for x in db.session.query(Inventory.base_asset_id)
        .filter(
            Inventory.location_id == location_id,
            Inventory.base_asset_id.isnot(None)
        )
        .all()
    }

    out = []
    for a in BaseAsset.query.all():
        asset_type = normalize(a.equipment_type or "ATM")
        if requested_type and asset_type != requested_type:
            continue

        # Inventário de campo: não oferece estoque/inativos como ativo previsto.
        if "INATIVO" in normalize(a.base_status):
            continue

        asset_company = normalize(a.company)
        asset_line = normalize(a.line)
        # Algumas planilhas antigas usam L01 - AZUL; a localidade usa 01 - AZUL.
        asset_line_cmp = re.sub(r"^L(?=\d{2}\s*-)", "", asset_line)
        line_cmp = re.sub(r"^L(?=\d{2}\s*-)", "", line)
        if asset_line_cmp != line_cmp:
            continue
        if company not in asset_company and asset_company not in company:
            continue

        station_name = normalize(a.locality)
        code = normalize(a.location_code or a.station_code)
        station_match = (
            (station_name and (station_name in station_text or station_text.endswith(station_name)))
            or (code and station_text.startswith(code + " "))
        )
        if not station_match:
            continue

        out.append({
            "id": a.id,
            "equipment_type": a.equipment_type or "ATM",
            "asset_key": a.asset_key,
            "description": a.description,
            "company": a.company,
            "station_code": a.station_code,
            "location_code": a.location_code,
            "line": a.line,
            "locality": a.locality,
            "terminal_number": a.terminal_number,
            "serial": a.serial,
            "qrcode_id": a.qrcode_id,
            "top_id": a.top_id,
            "products": a.products,
            "model": a.model,
            "supplier": a.supplier,
            "transactions": a.transactions,
            "pix": a.pix,
            "mount": a.mount,
            "base_status": a.base_status,
            "application": a.application,
            "bom_id": a.bom_id,
            "bu_id": a.bu_id,
            "software_version": a.software_version,
            "quantity": a.quantity,
            "base_notes": a.base_notes,
            "leasing_status": a.leasing_status,
            "contract_end": a.contract_end,
            "installation_type": a.installation_type,
            "installation_date": a.installation_date,
            "already_inventoried": a.id in already,
        })

    return jsonify(out)

def _optional_float(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return float(value.replace(",", "."))
    except (TypeError, ValueError):
        return None


def _optional_iso_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        # O navegador envia ISO 8601. Normaliza "Z" para compatibilidade.
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


@app.post("/api/inventory")
@field_required
def create_inventory():
    location_id = request.form.get("location_id", type=int)
    equipment_type = request.form.get("equipment_type", "").strip()
    base_asset_id = request.form.get("base_asset_id", type=int)
    serial = request.form.get("serial", "").strip()
    asset_identifier = request.form.get("asset_identifier", "").strip() or serial
    latitude = _optional_float(request.form.get("latitude"))
    longitude = _optional_float(request.form.get("longitude"))
    gps_accuracy = _optional_float(request.form.get("gps_accuracy"))
    gps_captured_at = _optional_iso_datetime(request.form.get("gps_captured_at"))

    if not location_id or not equipment_type or not asset_identifier:
        return jsonify({"ok": False, "error": "Local, tipo e identificação/série são obrigatórios."}), 400

    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify({"ok": False, "error": "Local inválido."}), 400

    duplicate = (
        db.session.query(Inventory, User.name.label("technician"))
        .join(User, User.id == Inventory.technician_id)
        .filter(
            Inventory.location_id == location_id,
            Inventory.equipment_type == equipment_type,
            func.upper(Inventory.asset_identifier) == asset_identifier.upper()
        )
        .first()
    )
    if duplicate:
        inv, technician_name = duplicate
        when = inv.created_at.strftime("%d/%m/%Y %H:%M")
        return jsonify({
            "ok": False,
            "duplicate": True,
            "error": f"Este equipamento já foi inventariado por {technician_name} em {when}."
        }), 409

    now = datetime.utcnow()
    inv = Inventory(
        location_id=location_id,
        equipment_type=equipment_type,
        base_asset_id=base_asset_id,
        asset_identifier=asset_identifier,
        serial=serial,
        supplier=request.form.get("supplier", ""),
        model=request.form.get("model", ""),
        application=request.form.get("application", ""),
        bom_id=request.form.get("bom_id", ""),
        bu_id=request.form.get("bu_id", ""),
        validator_top_id=request.form.get("validator_top_id", ""),
        software_version=request.form.get("software_version", ""),
        exact_position=request.form.get("exact_position", ""),
        mount=request.form.get("mount", ""),
        operational_status=request.form.get("operational_status", ""),
        connectivity=request.form.get("connectivity", ""),
        network_id=request.form.get("network_id", ""),
        label_status=request.form.get("label_status", ""),
        in_base=request.form.get("in_base", ""),
        divergence=request.form.get("divergence", ""),
        notes=request.form.get("notes", ""),
        latitude=latitude,
        longitude=longitude,
        gps_accuracy=gps_accuracy,
        gps_captured_at=gps_captured_at,
        technician_id=session["user_id"],
        created_at=now
    )

    try:
        db.session.add(inv)
        db.session.flush()

        # Armazenamento local temporário.
        # Em produção, vamos trocar esta parte por storage central (R2/S3).
        for f in request.files.getlist("attachments"):
            if not f or not f.filename:
                continue
            safe = secure_filename(f.filename)
            stored = f"{inv.id}_{secrets.token_hex(6)}_{safe}"
            f.save(UPLOAD_DIR / stored)
            db.session.add(Attachment(
                inventory_id=inv.id,
                original_name=f.filename,
                stored_name=stored,
                mime_type=f.mimetype
            ))

        if loc.survey_status == "PENDENTE":
            loc.survey_status = "EM ANDAMENTO"
            loc.started_at = now

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "duplicate": True, "error": "Registro duplicado para este local."}), 409

    return jsonify({"ok": True, "id": inv.id})


@app.route("/api/inventory/<int:inventory_id>", methods=["PUT", "PATCH"])
@manager_required
def update_inventory(inventory_id):
    inv = db.session.get(Inventory, inventory_id)
    if not inv:
        return jsonify({"ok": False, "error": "Registro não encontrado."}), 404

    location_id = request.form.get("location_id", type=int) or inv.location_id
    equipment_type = request.form.get("equipment_type", inv.equipment_type or "").strip()
    base_asset_id = request.form.get("base_asset_id", type=int)
    serial = request.form.get("serial", inv.serial or "").strip()
    asset_identifier = request.form.get("asset_identifier", inv.asset_identifier or "").strip() or serial

    if not location_id or not equipment_type or not asset_identifier:
        return jsonify({"ok": False, "error": "Local, tipo e identificação/série são obrigatórios."}), 400

    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify({"ok": False, "error": "Local inválido."}), 400

    duplicate = Inventory.query.filter(
        Inventory.id != inventory_id,
        Inventory.location_id == location_id,
        Inventory.equipment_type == equipment_type,
        func.upper(Inventory.asset_identifier) == asset_identifier.upper()
    ).first()
    if duplicate:
        return jsonify({
            "ok": False,
            "duplicate": True,
            "error": "Já existe outro equipamento com esta identificação neste local."
        }), 409

    inv.location_id = location_id
    inv.equipment_type = equipment_type
    inv.base_asset_id = base_asset_id
    inv.asset_identifier = asset_identifier
    inv.serial = serial
    inv.supplier = request.form.get("supplier", inv.supplier or "")
    inv.model = request.form.get("model", inv.model or "")
    inv.application = request.form.get("application", inv.application or "")
    inv.bom_id = request.form.get("bom_id", inv.bom_id or "")
    inv.bu_id = request.form.get("bu_id", inv.bu_id or "")
    inv.validator_top_id = request.form.get("validator_top_id", inv.validator_top_id or "")
    inv.software_version = request.form.get("software_version", inv.software_version or "")
    inv.exact_position = request.form.get("exact_position", inv.exact_position or "")
    inv.mount = request.form.get("mount", inv.mount or "")
    inv.operational_status = request.form.get("operational_status", inv.operational_status or "")
    inv.connectivity = request.form.get("connectivity", inv.connectivity or "")
    inv.network_id = request.form.get("network_id", inv.network_id or "")
    inv.label_status = request.form.get("label_status", inv.label_status or "")
    inv.in_base = request.form.get("in_base", inv.in_base or "")
    inv.divergence = request.form.get("divergence", inv.divergence or "")
    inv.notes = request.form.get("notes", inv.notes or "")

    if request.form.get("latitude") not in (None, ""):
        inv.latitude = _optional_float(request.form.get("latitude"))
    if request.form.get("longitude") not in (None, ""):
        inv.longitude = _optional_float(request.form.get("longitude"))
    if request.form.get("gps_accuracy") not in (None, ""):
        inv.gps_accuracy = _optional_float(request.form.get("gps_accuracy"))
    if request.form.get("gps_captured_at") not in (None, ""):
        inv.gps_captured_at = _optional_iso_datetime(request.form.get("gps_captured_at"))

    inv.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({"ok": True, "id": inv.id, "message": "Cadastro atualizado com sucesso."})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "duplicate": True, "error": "A alteração geraria um registro duplicado."}), 409
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.delete("/api/inventory/<int:inventory_id>")
@manager_required
def delete_inventory(inventory_id):
    inv = db.session.get(Inventory, inventory_id)
    if not inv:
        return jsonify({"ok": False, "error": "Registro não encontrado."}), 404

    location_id = inv.location_id
    try:
        attachments = Attachment.query.filter_by(inventory_id=inventory_id).all()
        for attachment in attachments:
            try:
                if attachment.stored_name:
                    file_path = UPLOAD_DIR / attachment.stored_name
                    if file_path.exists():
                        file_path.unlink()
            except Exception:
                pass
            db.session.delete(attachment)

        db.session.delete(inv)
        db.session.flush()

        remaining = Inventory.query.filter_by(location_id=location_id).count()
        if remaining == 0:
            loc = db.session.get(Location, location_id)
            if loc:
                loc.survey_status = "PENDENTE"
                loc.started_at = None
                loc.completed_at = None
                loc.completed_by = None

        db.session.commit()
        return jsonify({"ok": True, "id": inventory_id, "message": "Cadastro excluído com sucesso."})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.post("/api/location/<int:location_id>/complete")
@field_required
def complete_location(location_id):
    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify({"ok": False, "error": "Local inválido."}), 404

    loc.survey_status = "CONCLUIDA"
    loc.completed_at = datetime.utcnow()
    loc.completed_by = session["user_id"]
    db.session.commit()
    return jsonify({"ok": True})


@app.post("/api/location/<int:location_id>/reopen")
@manager_required
def reopen_location(location_id):
    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify({"ok": False, "error": "Local inválido."}), 404

    loc.survey_status = "EM ANDAMENTO"
    loc.completed_at = None
    loc.completed_by = None
    db.session.commit()
    return jsonify({"ok": True})



@app.post("/api/location/<int:location_id>/reference-position")
@manager_required
def save_location_reference_position(location_id):
    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify({"ok": False, "error": "Localidade não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("latitude"))
        lon = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Latitude/longitude inválidas."}), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"ok": False, "error": "Coordenadas fora do intervalo válido."}), 400

    loc.reference_latitude = lat
    loc.reference_longitude = lon
    loc.reference_source = (data.get("source") or "Gestor - mapa").strip()[:120]
    loc.reference_updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "ok": True,
        "location_id": loc.id,
        "reference_latitude": loc.reference_latitude,
        "reference_longitude": loc.reference_longitude,
        "reference_source": loc.reference_source
    })


@app.get("/api/gps/recent")
@dashboard_required
def api_recent_gps():
    limit = request.args.get("limit", default=20, type=int) or 20
    limit = max(1, min(limit, 100))

    rows = (
        db.session.query(
            Inventory,
            User.name.label("technician_name"),
            User.user_code.label("technician_code"),
            Location.location.label("location_name"),
            Location.company.label("company"),
            Location.line.label("line")
        )
        .join(User, User.id == Inventory.technician_id)
        .join(Location, Location.id == Inventory.location_id)
        .filter(
            Inventory.latitude.isnot(None),
            Inventory.longitude.isnot(None)
        )
        .order_by(
            func.coalesce(Inventory.gps_captured_at, Inventory.created_at).desc()
        )
        .limit(limit)
        .all()
    )

    total_inventory = Inventory.query.count()
    gps_inventory = Inventory.query.filter(
        Inventory.latitude.isnot(None),
        Inventory.longitude.isnot(None)
    ).count()

    return jsonify({
        "summary": {
            "total_inventory": total_inventory,
            "with_gps": gps_inventory,
            "without_gps": max(0, total_inventory - gps_inventory),
            "coverage_pct": round((gps_inventory / total_inventory * 100), 1) if total_inventory else 0
        },
        "items": [{
            "inventory_id": inv.id,
            "location_id": inv.location_id,
            "location_name": location_name,
            "company": company,
            "line": line,
            "equipment_type": inv.equipment_type,
            "asset_identifier": inv.asset_identifier,
            "technician": technician_name,
            "technician_code": technician_code,
            "latitude": inv.latitude,
            "longitude": inv.longitude,
            "gps_accuracy": inv.gps_accuracy,
            "gps_captured_at": inv.gps_captured_at.isoformat(timespec="seconds") if inv.gps_captured_at else None,
            "created_at": inv.created_at.isoformat(timespec="seconds") if inv.created_at else None
        } for inv, technician_name, technician_code, location_name, company, line in rows]
    })


@app.get("/api/dashboard")
@dashboard_required
def dashboard():
    total = Location.query.count()
    pending = Location.query.filter_by(survey_status="PENDENTE").count()
    progress = Location.query.filter_by(survey_status="EM ANDAMENTO").count()
    completed = Location.query.filter_by(survey_status="CONCLUIDA").count()

    inv_rows = (
        db.session.query(Inventory.equipment_type, func.count(Inventory.id))
        .group_by(Inventory.equipment_type)
        .all()
    )
    inventoried_by_type = {"ATM":0,"VALIDADOR":0,"POS":0,"TDI":0,"BLOQUEIO":0}
    inventoried_total = 0
    for typ, count in inv_rows:
        count = int(count or 0)
        inventoried_total += count
        canonical = _canonical_equipment_type(typ)
        if canonical in inventoried_by_type:
            inventoried_by_type[canonical] += count

    classified_inventoried = sum(inventoried_by_type.values())
    unclassified = max(0, inventoried_total - classified_inventoried)
    inoperative = Inventory.query.filter_by(operational_status="Inoperante").count()
    divergences = Inventory.query.filter(
        Inventory.divergence.isnot(None),
        Inventory.divergence.notin_(["", "Não", "Nao"])
    ).count()

    technical_tdi_expected = int(
        db.session.query(func.coalesce(func.sum(func.coalesce(BaseAsset.quantity, 1)), 0))
        .filter(
            func.upper(func.coalesce(BaseAsset.equipment_type, "")) == "TDI",
            ~func.upper(func.coalesce(BaseAsset.base_status, "")).like("%INATIVO%")
        )
        .scalar() or 0
    )

    by_type = []
    for typ in ["ATM", "VALIDADOR", "POS", "TDI", "BLOQUEIO"]:
        # TDI continua como controle técnico separado do parque executivo oficial.
        exp = technical_tdi_expected if typ == "TDI" else int(OFFICIAL_PARK.get(typ, 0))
        inv = int(inventoried_by_type.get(typ, 0))
        by_type.append({
            "type": typ,
            "expected": exp,
            "inventoried": inv,
            "missing": max(0, exp - inv) if exp else 0,
            "coverage_pct": round(min(100, inv / exp * 100), 1) if exp else 0,
            "official": typ in OFFICIAL_PARK,
        })

    companies = (
        db.session.query(
            Location.company.label("company"),
            func.count(Location.id).label("total"),
            func.sum(case((Location.survey_status == "PENDENTE", 1), else_=0)).label("pending"),
            func.sum(case((Location.survey_status == "EM ANDAMENTO", 1), else_=0)).label("progress"),
            func.sum(case((Location.survey_status == "CONCLUIDA", 1), else_=0)).label("completed"),
        )
        .group_by(Location.company)
        .order_by(Location.company)
        .all()
    )

    official_inventoried = sum(
        min(int(inventoried_by_type.get(typ, 0)), int(exp))
        for typ, exp in OFFICIAL_PARK.items()
    )

    return jsonify({
        "release": DASHBOARD_RELEASE,
        "official_park": {
            "total": OFFICIAL_PARK_TOTAL,
            "by_type": OFFICIAL_PARK,
            "note": "TDI é acompanhado separadamente e não compõe o total oficial de 3.801."
        },
        "totals": {
            "total": total,
            "pending": pending,
            "progress": progress,
            "completed": completed,
            "expected": OFFICIAL_PARK_TOTAL,
            "missing": max(0, OFFICIAL_PARK_TOTAL - official_inventoried),
        },
        "inventory": {
            "inventoried": inventoried_total,
            "official_inventoried": official_inventoried,
            "classified": classified_inventoried,
            "unclassified": unclassified,
            "inoperative": inoperative,
            "divergences": divergences,
        },
        "by_type": by_type,
        "by_company": [{
            "company": x.company,
            "total": int(x.total or 0),
            "pending": int(x.pending or 0),
            "progress": int(x.progress or 0),
            "completed": int(x.completed or 0),
        } for x in companies],
    })



@app.get("/api/export/excel")
@dashboard_required
def export_dashboard_excel():
    company = (request.args.get("company") or "").strip()
    line = (request.args.get("line") or "").strip()
    equipment_type = _canonical_equipment_type(request.args.get("type") or "")
    if equipment_type == "OUTRO":
        equipment_type = ""

    expected_map = _expected_assets_by_location()
    locations = Location.query.order_by(Location.company, Location.line, Location.location).all()

    inv_rows = (
        db.session.query(
            Inventory.location_id,
            Inventory.equipment_type,
            func.count(Inventory.id),
            func.coalesce(func.sum(case((Inventory.operational_status == "Inoperante", 1), else_=0)), 0),
            func.coalesce(func.sum(case((
                Inventory.divergence.isnot(None)
                & (~Inventory.divergence.in_(["", "Não", "Nao"]))
            , 1), else_=0)), 0),
        )
        .group_by(Inventory.location_id, Inventory.equipment_type)
        .all()
    )

    inv_map = {}
    for loc_id, typ, count, inop, divs in inv_rows:
        b = inv_map.setdefault(loc_id, {
            "total":0, "inoperative":0, "divergences":0,
            "by_type":{"ATM":0,"VALIDADOR":0,"POS":0,"TDI":0,"BLOQUEIO":0,"OUTRO":0}
        })
        canonical = _canonical_equipment_type(typ)
        if canonical not in b["by_type"]:
            canonical = "OUTRO"
        b["by_type"][canonical] += int(count or 0)
        b["total"] += int(count or 0)
        b["inoperative"] += int(inop or 0)
        b["divergences"] += int(divs or 0)

    selected = []
    for loc in locations:
        if company and loc.company != company:
            continue
        if line and loc.line != line:
            continue
        exp = expected_map.get(loc.id, {})
        inv = inv_map.get(loc.id, {
            "total":0,"inoperative":0,"divergences":0,
            "by_type":{"ATM":0,"VALIDADOR":0,"POS":0,"TDI":0,"BLOQUEIO":0,"OUTRO":0}
        })
        if equipment_type and int(exp.get(equipment_type, 0) or 0) <= 0 and int(inv["by_type"].get(equipment_type,0) or 0) <= 0:
            continue
        selected.append((loc, exp, inv))

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo Executivo"

    title_fill = PatternFill("solid", fgColor="17365D")
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    white_font = Font(color="FFFFFF", bold=True)
    bold = Font(bold=True)

    ws["A1"] = "Inventário Autopass — Resumo Executivo"
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = title_fill
    ws.merge_cells("A1:F1")
    ws["A2"] = f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A3"] = f"Filtros: Empresa={company or 'Todas'} | Linha={line or 'Todas'} | Tipo={equipment_type or 'Todos'}"

    official_rows = [
        ("ATM", OFFICIAL_PARK["ATM"]),
        ("POS", OFFICIAL_PARK["POS"]),
        ("Recarga", OFFICIAL_PARK["VALIDADOR"]),
        ("Bloqueio", OFFICIAL_PARK["BLOQUEIO"]),
        ("TOTAL OFICIAL", OFFICIAL_PARK_TOTAL),
    ]
    ws.append([])
    ws.append(["Produto", "Parque oficial"])
    for cell in ws[5]:
        cell.fill = header_fill
        cell.font = bold
    for row in official_rows:
        ws.append(list(row))

    wsl = wb.create_sheet("Localidades")
    headers = [
        "Empresa","Linha","Localidade","Status","Tipo filtrado",
        "Previsto","Inventariado","Faltante","Cobertura %",
        "Divergências","Inoperantes"
    ]
    wsl.append(headers)
    for cell in wsl[1]:
        cell.fill = title_fill
        cell.font = white_font
        cell.alignment = Alignment(horizontal="center")

    for loc, exp, inv in selected:
        if equipment_type:
            expected = int(exp.get(equipment_type, 0) or 0)
            inventoried = int(inv["by_type"].get(equipment_type, 0) or 0)
        else:
            expected = int(sum(exp.values()))
            inventoried = int(inv["total"])
        missing = max(0, expected - inventoried)
        coverage = round(min(100, inventoried / expected * 100), 1) if expected else 0
        wsl.append([
            loc.company, loc.line, loc.location, loc.survey_status,
            equipment_type or "Todos", expected, inventoried, missing, coverage,
            int(inv["divergences"]), int(inv["inoperative"])
        ])

    wsi = wb.create_sheet("Inventário Realizado")
    inv_headers = [
        "ID","Empresa","Linha","Localidade","Tipo","Identificação","Série",
        "Modelo","Status","Divergência","Data","Latitude","Longitude"
    ]
    wsi.append(inv_headers)
    for cell in wsi[1]:
        cell.fill = title_fill
        cell.font = white_font

    query = (
        db.session.query(Inventory, Location)
        .join(Location, Location.id == Inventory.location_id)
        .order_by(Inventory.created_at.desc())
    )
    if company:
        query = query.filter(Location.company == company)
    if line:
        query = query.filter(Location.line == line)
    for inv, loc in query.all():
        canonical = _canonical_equipment_type(inv.equipment_type)
        if equipment_type and canonical != equipment_type:
            continue
        wsi.append([
            inv.id, loc.company, loc.line, loc.location, canonical,
            inv.asset_identifier, inv.serial, inv.model, inv.operational_status,
            inv.divergence, inv.created_at.strftime("%d/%m/%Y %H:%M") if inv.created_at else "",
            inv.latitude, inv.longitude
        ])


    # Evidências de campo (WhatsApp) — fonte separada do inventário canônico.
    if FieldEvidenceVisit.query.count():
        ws_ev = wb.create_sheet("Evidências de Campo")
        ev_headers = [
            "Data", "Hora", "Responsável", "Estação informada", "Linha informada",
            "Localidade associada", "Confiança", "Tipo", "Identificador", "Modelo",
            "Série", "Patrimônio", "Status operacional", "Auditoria", "Mídias"
        ]
        ws_ev.append(ev_headers)
        for c in ws_ev[1]:
            c.font = Font(bold=True)
        evidence_rows = (
            db.session.query(FieldEvidenceVisit, FieldEvidenceItem)
            .join(FieldEvidenceItem, FieldEvidenceItem.visit_id == FieldEvidenceVisit.id)
            .order_by(FieldEvidenceVisit.source_date, FieldEvidenceVisit.source_time)
            .all()
        )
        media_counts = dict(
            db.session.query(FieldEvidenceMedia.visit_id, func.count(FieldEvidenceMedia.id))
            .group_by(FieldEvidenceMedia.visit_id).all()
        )
        for visit, item in evidence_rows:
            loc = db.session.get(Location, visit.location_id) if visit.location_id else None
            ws_ev.append([
                visit.source_date, visit.source_time, visit.author, visit.station_raw, visit.line_raw,
                loc.location if loc else "", visit.match_confidence,
                item.equipment_type, item.identifier, item.model or "", item.serial or "",
                item.patrimony or "", item.operational_status or "", item.audit_status or "",
                int(media_counts.get(visit.id, 0)),
            ])

    for sheet in wb.worksheets:
        for col in range(1, sheet.max_column + 1):
            letter = get_column_letter(col)
            width = 10
            for row in range(1, min(sheet.max_row, 300) + 1):
                value = sheet.cell(row=row, column=col).value
                if value is not None:
                    width = max(width, min(42, len(str(value)) + 2))
            sheet.column_dimensions[letter].width = width
        sheet.freeze_panes = "A2" if sheet.title != "Resumo Executivo" else "A5"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"autopass_dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/uploads/<path:name>")
@login_required
def uploaded(name):
    return send_from_directory(UPLOAD_DIR, name)


@app.get("/api/inventory/<int:inventory_id>/attachments")
@login_required
def attachments(inventory_id):
    rows = Attachment.query.filter_by(inventory_id=inventory_id).all()
    return jsonify([{
        "id": a.id,
        "inventory_id": a.inventory_id,
        "original_name": a.original_name,
        "stored_name": a.stored_name,
        "mime_type": a.mime_type
    } for a in rows])


@app.route("/usuarios")
@manager_required
def users_page():
    users = User.query.order_by(User.active.desc(), User.name).all()
    return render_template("users.html", users=users)


def _normalize_optional_email(value):
    value = (value or "").strip().lower()
    return value or None


def _normalize_optional_phone(value):
    digits = re.sub(r"\D", "", value or "")
    return digits or None


def _next_user_code(role):
    prefixes = {
        "technician": "T",
        "manager": "G",
        "consultation": "C",
    }
    prefix = prefixes.get(role, "U")
    existing = (
        db.session.query(User.user_code)
        .filter(User.user_code.isnot(None), User.user_code.like(f"{prefix}%"))
        .all()
    )
    highest = 0
    for (code,) in existing:
        match = re.fullmatch(rf"{prefix}(\d+)", (code or "").upper())
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1:03d}"


@app.post("/usuarios/novo")
@manager_required
def create_user():
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "technician").strip()
    email = _normalize_optional_email(request.form.get("email"))
    phone = _normalize_optional_phone(request.form.get("phone"))

    if not name or not username or not password:
        flash("Nome, usuário e senha são obrigatórios.")
        return redirect(url_for("users_page"))

    if role not in ("manager", "technician", "consultation"):
        flash("Perfil de acesso inválido.")
        return redirect(url_for("users_page"))

    if len(password) < 8:
        flash("A senha deve ter pelo menos 8 caracteres.")
        return redirect(url_for("users_page"))

    if User.query.filter(func.lower(User.username) == username).first():
        flash("Já existe um usuário com esse login.")
        return redirect(url_for("users_page"))

    if email and User.query.filter(func.lower(User.email) == email).first():
        flash("Já existe um usuário com esse e-mail.")
        return redirect(url_for("users_page"))

    if phone and User.query.filter(User.phone == phone).first():
        flash("Já existe um usuário com esse celular.")
        return redirect(url_for("users_page"))

    user_code = _next_user_code(role)
    user = User(
        name=name,
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        active=True,
        user_code=user_code,
        email=email,
        phone=phone,
    )

    photo = request.files.get("photo")
    if photo and photo.filename and role in ("manager", "technician"):
        if not (photo.mimetype or "").startswith("image/"):
            flash("A foto do usuário deve ser uma imagem.")
            return redirect(url_for("users_page"))
        data = photo.read()
        if len(data) > 3 * 1024 * 1024:
            flash("A foto do usuário deve ter no máximo 3 MB.")
            return redirect(url_for("users_page"))
        safe_name = secure_filename(photo.filename) or "foto.jpg"
        object_key = f"usuarios/{user_code}/{uuid.uuid4().hex}-{safe_name}"
        _r2_put_bytes(object_key, data, photo.mimetype or "image/jpeg")
        user.photo_url = object_key

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Não foi possível criar o usuário porque existe um dado duplicado.")
        return redirect(url_for("users_page"))

    flash(f"Usuário {user.name} criado com sucesso. Código: {user.user_code}.")
    return redirect(url_for("users_page"))


@app.get("/usuarios/<int:user_id>/foto")
@manager_required
def user_photo(user_id):
    user = db.session.get(User, user_id)
    if not user or not user.photo_url:
        return "", 404

    try:
        obj = r2_client().get_object(
            Bucket=os.environ["R2_BUCKET_NAME"],
            Key=user.photo_url
        )
        return Response(
            obj["Body"].read(),
            mimetype=obj.get("ContentType") or "image/jpeg",
            headers={"Cache-Control": "private, max-age=300"}
        )
    except Exception:
        return "", 404


def _active_manager_count(exclude_user_id=None):
    query = User.query.filter_by(role="manager", active=True)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.count()


@app.post("/usuarios/<int:user_id>/toggle")
@manager_required
def toggle_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Usuário não encontrado.")
        return redirect(url_for("users_page"))

    if user.id == session.get("user_id"):
        flash("Você não pode desativar o próprio usuário enquanto está conectado.")
        return redirect(url_for("users_page"))

    if user.active and user.role == "manager" and _active_manager_count(exclude_user_id=user.id) == 0:
        flash("Não é possível desativar o último Gestor ativo.")
        return redirect(url_for("users_page"))

    user.active = not user.active
    db.session.commit()
    flash("Status do usuário atualizado.")
    return redirect(url_for("users_page"))


@app.post("/usuarios/<int:user_id>/editar")
@manager_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Usuário não encontrado.")
        return redirect(url_for("users_page"))

    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip().lower()
    role = request.form.get("role", user.role).strip()
    user_code = request.form.get("user_code", "").strip().upper()
    email = _normalize_optional_email(request.form.get("email"))
    phone = _normalize_optional_phone(request.form.get("phone"))

    if not name or not username:
        flash("Nome e usuário são obrigatórios.")
        return redirect(url_for("users_page"))

    if role not in ("manager", "technician", "consultation"):
        flash("Perfil de acesso inválido.")
        return redirect(url_for("users_page"))

    if not user_code:
        user_code = user.user_code or _next_user_code(role)

    duplicate_username = User.query.filter(
        User.id != user.id,
        func.lower(User.username) == username
    ).first()
    if duplicate_username:
        flash("Já existe outro usuário com esse login.")
        return redirect(url_for("users_page"))

    duplicate_code = User.query.filter(
        User.id != user.id,
        func.upper(User.user_code) == user_code
    ).first()
    if duplicate_code:
        flash("Já existe outro usuário com esse código.")
        return redirect(url_for("users_page"))

    if email:
        duplicate_email = User.query.filter(
            User.id != user.id,
            func.lower(User.email) == email
        ).first()
        if duplicate_email:
            flash("Já existe outro usuário com esse e-mail.")
            return redirect(url_for("users_page"))

    if phone:
        duplicate_phone = User.query.filter(
            User.id != user.id,
            User.phone == phone
        ).first()
        if duplicate_phone:
            flash("Já existe outro usuário com esse celular.")
            return redirect(url_for("users_page"))

    # Evita retirar o último acesso administrativo do sistema.
    if user.role == "manager" and role != "manager":
        if user.id == session.get("user_id"):
            flash("Você não pode alterar o próprio perfil de Gestor enquanto está conectado.")
            return redirect(url_for("users_page"))
        if _active_manager_count(exclude_user_id=user.id) == 0:
            flash("Não é possível alterar o perfil do último Gestor ativo.")
            return redirect(url_for("users_page"))

    old_photo_key = user.photo_url
    new_photo_key = None

    photo = request.files.get("photo")
    if photo and photo.filename:
        if role == "consultation":
            flash("Foto não é necessária para o perfil Consulta.")
            return redirect(url_for("users_page"))
        if not (photo.mimetype or "").startswith("image/"):
            flash("A foto do usuário deve ser uma imagem.")
            return redirect(url_for("users_page"))

        data = photo.read()
        if len(data) > 3 * 1024 * 1024:
            flash("A foto do usuário deve ter no máximo 3 MB.")
            return redirect(url_for("users_page"))

        safe_name = secure_filename(photo.filename) or "foto.jpg"
        new_photo_key = f"usuarios/{user_code}/{uuid.uuid4().hex}-{safe_name}"
        _r2_put_bytes(new_photo_key, data, photo.mimetype or "image/jpeg")

    remove_photo = request.form.get("remove_photo") == "1"

    user.name = name
    user.username = username
    user.role = role
    user.user_code = user_code
    user.email = email
    user.phone = phone

    if new_photo_key:
        user.photo_url = new_photo_key
    elif remove_photo:
        user.photo_url = None

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if new_photo_key:
            try:
                r2_client().delete_object(
                    Bucket=os.environ["R2_BUCKET_NAME"],
                    Key=new_photo_key
                )
            except Exception:
                pass
        flash("Não foi possível salvar porque existe um dado duplicado.")
        return redirect(url_for("users_page"))

    # Remove do R2 a foto antiga somente depois de a atualização do banco ter sido confirmada.
    if old_photo_key and old_photo_key != user.photo_url:
        try:
            r2_client().delete_object(
                Bucket=os.environ["R2_BUCKET_NAME"],
                Key=old_photo_key
            )
        except Exception:
            pass

    if user.id == session.get("user_id"):
        session["name"] = user.name
        session["role"] = user.role

    flash(f"Usuário {user.name} atualizado com sucesso.")
    return redirect(url_for("users_page"))


@app.post("/usuarios/<int:user_id>/senha")
@manager_required
def reset_user_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Usuário não encontrado.")
        return redirect(url_for("users_page"))

    password = request.form.get("password", "")
    if len(password) < 8:
        flash("A nova senha deve ter pelo menos 8 caracteres.")
        return redirect(url_for("users_page"))

    user.password_hash = generate_password_hash(password)
    db.session.commit()
    flash(f"Senha de {user.name} alterada.")
    return redirect(url_for("users_page"))



def _wa_parse_messages(chat_text):
    pattern = re.compile(
        r'^\[(\d{2}/\d{2}/\d{4}),\s*(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s?(.*)$'
    )
    messages = []
    current = None
    for raw in chat_text.splitlines():
        line = (
            raw.replace("\u200e", "")
               .replace("\ufeff", "")
               .replace("\u202a", "")
               .replace("\u202c", "")
        )
        m = pattern.match(line)
        if m:
            if current:
                messages.append(current)
            current = {
                "date": m.group(1),
                "time": m.group(2),
                "author": m.group(3).strip(),
                "text": m.group(4).strip()
            }
        elif current is not None:
            current["text"] += "\n" + line
    if current:
        messages.append(current)
    return messages


def _wa_extract_attachments(text):
    return re.findall(r'<anexado:\s*([^>]+)>', text or "", flags=re.I)


_WA_LINE_COLORS = {
    1: "AZUL", 2: "VERDE", 3: "VERMELHA", 4: "AMARELA", 5: "LILAS",
    7: "RUBI", 8: "DIAMANTE", 9: "ESMERALDA", 10: "TURQUESA",
    11: "CORAL", 12: "SAFIRA", 13: "JADE", 15: "PRATA", 17: "OURO",
}


def _wa_extract_station(text):
    clean = re.sub(r'<anexado:[^>]+>', '', text or '', flags=re.I)
    m = re.search(
        r'Est[aã]ção\s+(.+?)\s+Linha\s+(\d{1,2})(?:\s*[-–]\s*([A-Za-zÀ-ÿ]+))?',
        clean, flags=re.I | re.S
    )
    if not m:
        return None
    station = re.sub(r'\s+', ' ', m.group(1)).strip(" -")
    number = int(m.group(2))
    color = (m.group(3) or _WA_LINE_COLORS.get(number, "")).upper()
    tail = clean[m.end():].splitlines()[0].strip() if m.end() < len(clean) else ""
    if normalize(station) in {"MOTIVA", "METRO", "CPTM"} and tail:
        station = tail.split("*", 1)[0].strip(" -")
    return {
        "station": station,
        "line_number": number,
        "line": f"{number:02d} - {color}" if color else f"{number:02d}",
    }


def _wa_split_competition(text):
    m = re.search(r'\*?\s*Concorr[eê]ncia\s*\*?', text or "", flags=re.I)
    if not m:
        m = re.search(r'\*?\s*concorrencia\s*\*?', text or "", flags=re.I)
    if not m:
        return text or "", ""
    return (text or "")[:m.start()], (text or "")[m.end():]


def _wa_equipment_rows(text, visit_token="WA"):
    official, competition = _wa_split_competition(text)
    clean = re.sub(r'<anexado:[^>]+>', '', official or '', flags=re.I)
    rows = []
    provisional_index = 0

    for raw_line in clean.splitlines():
        line = re.sub(r'\s+', ' ', raw_line).strip()
        if not line:
            continue

        # POS: TOPs de 6-8 dígitos. SN e patrimônio são atributos, não identificadores.
        if re.search(r'\bPOS\b', line, flags=re.I):
            tmp = re.sub(r'\bSN\s*[A-Za-z0-9]+\b', ' ', line, flags=re.I)
            tmp = re.sub(r'Patrim[oô]nio\s*(?:off|[A-Za-z0-9]+)', ' ', tmp, flags=re.I)
            for ident in re.findall(r'\b\d{6,8}\b', tmp):
                rows.append({
                    "type": "POS", "identifier": ident, "model": "",
                    "serial": "", "patrimony": "", "status": "Não informado",
                    "source_line": line, "provisional": False
                })

        # ATM inclui equipamentos descritos em campo como TCI / TCI NEO / MK / MK NEO.
        if re.search(r'\b(?:ATM|TCI)\b', line, flags=re.I):
            tmp = re.sub(r'\(?\s*Patrim[oô]nio\s*(?:off|\d+)\s*\)?', ' ', line, flags=re.I)
            tmp = re.sub(r'\bSN\s*[A-Za-z0-9]+\b', ' ', tmp, flags=re.I)
            ids = re.findall(r'\b\d{4,8}\b', tmp)
            model_match = re.search(r'\b(?:ATM|TCI)\s*([^:]*?)(?::|$)', line, flags=re.I)
            model = model_match.group(1).strip() if model_match else ""
            if ids:
                for ident in ids:
                    rows.append({
                        "type": "ATM", "identifier": ident, "model": model,
                        "serial": "", "patrimony": "",
                        "status": "Inoperante" if re.search(r'inoperante', line, re.I) else "Não informado",
                        "source_line": line, "provisional": False
                    })
            elif re.search(r'inoperante', line, re.I):
                provisional_index += 1
                rows.append({
                    "type": "ATM",
                    "identifier": f"ATM-SID-{visit_token}-{provisional_index}",
                    "model": model, "serial": "", "patrimony": "",
                    "status": "Inoperante", "source_line": line, "provisional": True
                })

        # Validadores de recarga.
        if re.search(r'\bVALIDADOR', line, flags=re.I):
            nums = re.findall(r'\b\d{2,5}\b', line)
            for ident in [x for x in nums if int(x) > 20]:
                rows.append({
                    "type": "VALIDADOR", "identifier": ident, "model": "",
                    "serial": "", "patrimony": "", "status": "Não informado",
                    "source_line": line, "provisional": False
                })

    # POS em linhas detalhadas: TOP SN patrimônio.
    for m in re.finditer(
        r'\b(\d{6,8})\s+SN\s+([A-Za-z0-9]+)(?:\s+Patrim[oô]nio\s+([A-Za-z0-9]+))?',
        clean, flags=re.I
    ):
        ident, serial, patrimony = m.group(1), m.group(2), (m.group(3) or "")
        existing = next((x for x in rows if x["type"] == "POS" and x["identifier"] == ident), None)
        if existing:
            existing["serial"] = serial
            existing["patrimony"] = patrimony
        else:
            rows.append({
                "type": "POS", "identifier": ident, "model": "",
                "serial": serial, "patrimony": patrimony, "status": "Não informado",
                "source_line": m.group(0), "provisional": False
            })

    # Rack/Hack é guardado como evidência, sem contaminar os Big Numbers oficiais.
    rack_mentions = re.findall(r'\b(?:RACK|HACK)\b', clean, flags=re.I)
    for idx in range(len(rack_mentions)):
        rows.append({
            "type": "RACK", "identifier": f"RACK-{visit_token}-{idx + 1}",
            "model": "", "serial": "", "patrimony": "",
            "status": "Não informado", "source_line": "Rack citado no relatório",
            "provisional": True
        })

    seen = set()
    out = []
    for row in rows:
        key = (row["type"], row["identifier"])
        if key not in seen:
            seen.add(key)
            out.append(row)

    competition_summary = {}
    for type_name, regex in (
        ("ATM", r'(\d+)\s+ATMs?'),
        ("VALIDADOR", r'(\d+)\s+validadores?'),
        ("TERMINAL", r'(\d+)\s+terminais?'),
    ):
        vals = [int(x) for x in re.findall(regex, competition or "", flags=re.I)]
        if vals:
            competition_summary[type_name] = sum(vals)

    return out, (competition or "").strip(), competition_summary


def _wa_location_name(loc):
    if not loc:
        return ""
    name = normalize(loc.location)
    return name.split(" - ", 1)[1] if " - " in name else name


def _wa_match_location(station_name, line_number):
    aliases = {
        "BRAZ CUBAS": "BRAS CUBAS",
        "ENG MANOEL FEIO": "MANOEL FEIO",
        "ENG GOULART": "ENGENHEIRO GOULART",
        "GUARULHOS": "GUARULHOS CECAP",
        "AEROPORTO": "AEROPORTO GUARULHOS",
    }
    target = aliases.get(normalize(station_name), normalize(station_name))

    all_locations = Location.query.all()
    same_line = []
    other_line = []
    for loc in all_locations:
        m = re.match(r'(\d+)', loc.line or "")
        ln = int(m.group(1)) if m else None
        name = _wa_location_name(loc)
        score = SequenceMatcher(None, target, name).ratio()
        if target in name or name in target:
            score = max(score, 0.93)
        bucket = same_line if ln == line_number else other_line
        bucket.append((score, loc))

    same_line.sort(key=lambda x: x[0], reverse=True)
    other_line.sort(key=lambda x: x[0], reverse=True)

    if same_line and same_line[0][0] >= 0.72:
        score, loc = same_line[0]
        return loc, ("SEGURA" if score >= 0.82 else "REVISAR"), round(score, 3)

    # Estações compartilhadas podem aparecer no WhatsApp com uma linha que ainda não existe
    # como Location separada (ex.: Luz / Brás). Mantém como revisão, sem atribuição automática.
    if other_line and other_line[0][0] >= 0.90:
        score, _loc = other_line[0]
        return None, "REVISAR", round(score, 3)

    return None, "NAO IDENTIFICADA", 0.0


def _wa_visit_source_key(msg, station):
    seed = "|".join([
        msg["date"], msg["time"], normalize(msg["author"]),
        normalize(station["station"]), str(station["line_number"]),
        normalize(re.sub(r'<anexado:[^>]+>', '', msg["text"], flags=re.I))
    ])
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]


def _wa_analyze_archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        chat_names = [n for n in names if n.lower().endswith("_chat.txt") or n.lower().endswith(".txt")]
        if not chat_names:
            raise ValueError("O ZIP não contém o arquivo _chat.txt.")

        chat_text = z.read(chat_names[0]).decode("utf-8", errors="replace")
        messages = _wa_parse_messages(chat_text)
        available_media = set(names)

        visits = []
        active_by_author = {}
        pending_media = {}
        seen_visit_keys = set()

        def msg_dt(msg):
            try:
                return datetime.strptime(f'{msg["date"]} {msg["time"]}', "%d/%m/%Y %H:%M:%S")
            except Exception:
                return datetime.utcnow()

        for msg in messages:
            author = msg["author"]
            dt = msg_dt(msg)
            station = _wa_extract_station(msg["text"])
            attachments = [a for a in _wa_extract_attachments(msg["text"]) if a in available_media]

            if station:
                source_key = _wa_visit_source_key(msg, station)
                active = active_by_author.get(author)

                # Concorrência/continuação da mesma estação é incorporada à mesma visita.
                if (
                    active
                    and normalize(active["station_raw"]) == normalize(station["station"])
                    and active["line_number"] == station["line_number"]
                    and (dt - active["_last_dt"]).total_seconds() <= 5400
                ):
                    signature = normalize(re.sub(r'<anexado:[^>]+>', '', msg["text"], flags=re.I))
                    if signature and signature not in active["_signatures"]:
                        active["_signatures"].add(signature)
                        active["messages"].append(msg)
                        eqs, comp_text, comp_summary = _wa_equipment_rows(msg["text"], active["source_key"][:10])
                        existing_keys = {(x["type"], x["identifier"]) for x in active["equipment"]}
                        for eq in eqs:
                            if (eq["type"], eq["identifier"]) not in existing_keys:
                                active["equipment"].append(eq)
                                existing_keys.add((eq["type"], eq["identifier"]))
                        if comp_text:
                            active["competition_text"] = (active["competition_text"] + "\n" + comp_text).strip()
                        for k, v in comp_summary.items():
                            active["competition_summary"][k] = active["competition_summary"].get(k, 0) + v
                    for name in attachments:
                        if name not in active["attachments"]:
                            active["attachments"].append(name)
                    active["_last_dt"] = dt
                    continue

                if source_key in seen_visit_keys:
                    continue
                seen_visit_keys.add(source_key)

                loc, confidence, score = _wa_match_location(station["station"], station["line_number"])
                eqs, comp_text, comp_summary = _wa_equipment_rows(msg["text"], source_key[:10])
                visit = {
                    "source_key": source_key,
                    "date": msg["date"],
                    "time": msg["time"],
                    "author": author,
                    "station_raw": station["station"],
                    "line_number": station["line_number"],
                    "line_raw": station["line"],
                    "location_id": loc.id if loc else None,
                    "location_name": loc.location if loc else "",
                    "company": loc.company if loc else "",
                    "confidence": confidence,
                    "match_score": score,
                    "messages": [msg],
                    "equipment": eqs,
                    "competition_text": comp_text,
                    "competition_summary": comp_summary,
                    "attachments": list(dict.fromkeys(attachments)),
                    "_last_dt": dt,
                    "_signatures": {
                        normalize(re.sub(r'<anexado:[^>]+>', '', msg["text"], flags=re.I))
                    },
                }

                # Fotos enviadas pouco antes do texto da estação.
                pending = pending_media.get(author, [])
                keep = []
                for pdt, name in pending:
                    if 0 <= (dt - pdt).total_seconds() <= 900:
                        if name not in visit["attachments"]:
                            visit["attachments"].append(name)
                    else:
                        keep.append((pdt, name))
                pending_media[author] = keep

                visits.append(visit)
                active_by_author[author] = visit

            else:
                active = active_by_author.get(author)

                if attachments:
                    if active and 0 <= (dt - active["_last_dt"]).total_seconds() <= 5400:
                        for name in attachments:
                            if name not in active["attachments"]:
                                active["attachments"].append(name)
                        active["_last_dt"] = dt
                    else:
                        pending_media.setdefault(author, [])
                        for name in attachments:
                            pending_media[author].append((dt, name))

                # POS e complementos enviados em mensagem seguinte pertencem à última estação
                # do mesmo técnico, desde que dentro de 90 minutos.
                if active and 0 <= (dt - active["_last_dt"]).total_seconds() <= 5400:
                    clean = re.sub(r'<anexado:[^>]+>', '', msg["text"]).strip()
                    if clean and clean != "Mensagem apagada":
                        eqs, comp_text, comp_summary = _wa_equipment_rows(msg["text"], active["source_key"][:10])
                        if eqs or re.search(r'\bPOS\b|\bSN\b|Patrim|concorr|autoriz', clean, flags=re.I):
                            signature = normalize(clean)
                            if signature and signature not in active["_signatures"]:
                                active["_signatures"].add(signature)
                                active["messages"].append(msg)
                            existing_keys = {(x["type"], x["identifier"]) for x in active["equipment"]}
                            for eq in eqs:
                                if (eq["type"], eq["identifier"]) not in existing_keys:
                                    active["equipment"].append(eq)
                                    existing_keys.add((eq["type"], eq["identifier"]))
                            if comp_text:
                                active["competition_text"] = (active["competition_text"] + "\n" + comp_text).strip()
                            for k, v in comp_summary.items():
                                active["competition_summary"][k] = active["competition_summary"].get(k, 0) + v
                            active["_last_dt"] = dt

        for visit in visits:
            visit.pop("_last_dt", None)
            visit.pop("_signatures", None)

            # Comparação preliminar com a base e inventário atual.
            for eq in visit["equipment"]:
                eq["base_status"] = "NÃO CONFRONTADO"
                eq["inventory_status"] = "NÃO CONFRONTADO"
                eq["audit_status"] = "PENDENTE"
                eq["base_asset_id"] = None
                eq["inventory_id"] = None

                if eq["type"] == "RACK":
                    eq["audit_status"] = "EVIDÊNCIA FORA DO PARQUE OFICIAL"
                    continue

                type_map = {
                    "ATM": "ATM",
                    "VALIDADOR": "VALIDADOR",
                    "POS": "POS",
                }
                base_type = type_map.get(eq["type"], eq["type"])
                candidates = BaseAsset.query.filter(
                    func.upper(BaseAsset.equipment_type) == base_type,
                    (
                        (func.upper(func.coalesce(BaseAsset.terminal_number, "")) == eq["identifier"].upper())
                        | (func.upper(func.coalesce(BaseAsset.top_id, "")) == eq["identifier"].upper())
                        | (func.upper(func.coalesce(BaseAsset.serial, "")) == eq["identifier"].upper())
                    )
                ).all()

                if candidates:
                    chosen = candidates[0]
                    eq["base_asset_id"] = chosen.id
                    if visit["location_id"]:
                        loc = db.session.get(Location, visit["location_id"])
                        same_line = normalize(chosen.line) == normalize(loc.line)
                        same_name = (
                            normalize(chosen.locality) in normalize(loc.location)
                            or normalize(_wa_location_name(loc)) in normalize(chosen.locality)
                        )
                        if same_line and same_name:
                            eq["base_status"] = "BASE CONFERE"
                        else:
                            eq["base_status"] = "BASE EM OUTRA LOCALIDADE"
                    else:
                        eq["base_status"] = "ENCONTRADO NA BASE"
                else:
                    eq["base_status"] = "NÃO PREVISTO NA BASE"

                if visit["location_id"]:
                    inv_type = {
                        "ATM": "ATM",
                        "VALIDADOR": "Validador de Recarga",
                        "POS": "POS de Bilheteria",
                    }.get(eq["type"], eq["type"])
                    inv = Inventory.query.filter(
                        Inventory.location_id == visit["location_id"],
                        Inventory.equipment_type == inv_type,
                        func.upper(Inventory.asset_identifier) == eq["identifier"].upper()
                    ).first()
                    if inv:
                        eq["inventory_id"] = inv.id
                        eq["inventory_status"] = "JÁ INVENTARIADO"
                    else:
                        eq["inventory_status"] = "AINDA NÃO INVENTARIADO"

                if eq["inventory_id"]:
                    eq["audit_status"] = "CONFORME / JÁ INVENTARIADO"
                elif eq["base_status"] == "BASE CONFERE":
                    eq["audit_status"] = "CONFIRMADO EM CAMPO / FALTA PROMOVER"
                elif eq["base_status"] == "BASE EM OUTRA LOCALIDADE":
                    eq["audit_status"] = "DIVERGÊNCIA DE LOCALIDADE"
                elif eq["base_status"] == "NÃO PREVISTO NA BASE":
                    eq["audit_status"] = "NOVO / NÃO PREVISTO"
                else:
                    eq["audit_status"] = "PENDENTE DE REVISÃO"

        summary = {
            "messages": len(messages),
            "media_total": len([n for n in names if not n.lower().endswith(".txt")]),
            "visits": len(visits),
            "equipment": sum(len(v["equipment"]) for v in visits),
            "safe": sum(1 for v in visits if v["confidence"] == "SEGURA"),
            "review": sum(1 for v in visits if v["confidence"] == "REVISAR"),
            "unmatched": sum(1 for v in visits if v["confidence"] == "NAO IDENTIFICADA"),
            "duplicates": sum(
                1 for v in visits for e in v["equipment"]
                if e.get("inventory_status") == "JÁ INVENTARIADO"
            ),
            "by_type": {
                t: sum(1 for v in visits for e in v["equipment"] if e["type"] == t)
                for t in ("ATM", "VALIDADOR", "POS", "RACK")
            },
            "audit": {
                status: sum(1 for v in visits for e in v["equipment"] if e["audit_status"] == status)
                for status in sorted({
                    e["audit_status"] for v in visits for e in v["equipment"]
                })
            },
            "media_linked": len({a for v in visits for a in v["attachments"]}),
        }
        return visits, summary


def _r2_put_bytes(key, data, content_type=None):
    kwargs = {
        "Bucket": os.environ["R2_BUCKET_NAME"],
        "Key": key,
        "Body": data
    }
    if content_type:
        kwargs["ContentType"] = content_type
    r2_client().put_object(**kwargs)


def _r2_get_bytes(key):
    obj = r2_client().get_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=key)
    return obj["Body"].read()


def _r2_available():
    required = ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
    return all(os.environ.get(x, "").strip() for x in required)


def _wa_stage_archive(raw, filename):
    batch_id = uuid.uuid4().hex
    safe_name = secure_filename(filename) or "whatsapp.zip"
    if _r2_available():
        key = f"whatsapp/fontes/{batch_id}/{safe_name}"
        _r2_put_bytes(key, raw, "application/zip")
        return f"r2:{key}", batch_id, "R2"

    staging_dir = UPLOAD_DIR / "whatsapp_staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    path = staging_dir / f"{batch_id}_{safe_name}"
    path.write_bytes(raw)
    return f"local:{path.name}", batch_id, "LOCAL TEMPORÁRIO"


def _wa_load_staged(staging_key):
    if staging_key.startswith("r2:"):
        return _r2_get_bytes(staging_key[3:])
    if staging_key.startswith("local:"):
        path = UPLOAD_DIR / "whatsapp_staging" / staging_key[6:]
        return path.read_bytes()
    raise ValueError("Origem de importação inválida.")


def _evidence_store_media(data, original_name, batch_id):
    sha = hashlib.sha256(data).hexdigest()
    existing = FieldEvidenceMedia.query.filter_by(sha256=sha).first()
    if existing:
        return existing, False

    safe_name = secure_filename(Path(original_name).name) or f"midia-{sha[:12]}"
    mime = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

    if _r2_available():
        key = f"whatsapp/evidencias/{batch_id}/{sha[:12]}_{safe_name}"
        _r2_put_bytes(key, data, mime)
        return FieldEvidenceMedia(
            sha256=sha, original_name=safe_name, mime_type=mime,
            storage_kind="r2", storage_key=key
        ), True

    evidence_dir = UPLOAD_DIR / "field_evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stored = f"{sha[:16]}_{safe_name}"
    (evidence_dir / stored).write_bytes(data)
    return FieldEvidenceMedia(
        sha256=sha, original_name=safe_name, mime_type=mime,
        storage_kind="local", storage_key=stored
    ), True


def _evidence_summary():
    visits = FieldEvidenceVisit.query.count()
    items = FieldEvidenceItem.query.count()
    media = FieldEvidenceMedia.query.count()
    matched = FieldEvidenceItem.query.filter(
        FieldEvidenceItem.audit_status.in_((
            "CONFORME / JÁ INVENTARIADO",
            "CONFIRMADO EM CAMPO / FALTA PROMOVER",
        ))
    ).count()
    review = FieldEvidenceItem.query.filter(
        ~FieldEvidenceItem.audit_status.in_((
            "CONFORME / JÁ INVENTARIADO",
            "CONFIRMADO EM CAMPO / FALTA PROMOVER",
            "EVIDÊNCIA FORA DO PARQUE OFICIAL",
        ))
    ).count()
    return {
        "visits": visits,
        "items": items,
        "media": media,
        "matched": matched,
        "review": review,
        "unresolved_visits": FieldEvidenceVisit.query.filter(FieldEvidenceVisit.location_id.is_(None)).count(),
    }


@app.route("/importar-whatsapp", methods=["GET", "POST"])
@manager_required
def import_whatsapp():
    preview = None
    summary = None
    error = None
    staging_key = None
    import_result = None
    storage_note = "Cloudflare R2" if _r2_available() else "armazenamento local temporário"

    if request.method == "POST":
        action = request.form.get("action", "analyze")

        if action == "analyze":
            upload = request.files.get("zip_file")
            if not upload or not upload.filename.lower().endswith(".zip"):
                error = "Selecione um arquivo ZIP exportado pelo WhatsApp."
            else:
                try:
                    raw = upload.read()
                    preview, summary = _wa_analyze_archive(raw)
                    staging_key, _batch_id, storage_note = _wa_stage_archive(raw, upload.filename)
                except Exception as exc:
                    error = f"Não foi possível analisar o ZIP: {type(exc).__name__}: {exc}"

        elif action == "import":
            staging_key = request.form.get("staging_key", "").strip()
            if not staging_key:
                error = "Arquivo de origem não encontrado. Analise o ZIP novamente."
            else:
                try:
                    raw = _wa_load_staged(staging_key)
                    preview, summary = _wa_analyze_archive(raw)
                    batch_id = hashlib.sha256(raw).hexdigest()[:16]
                    inserted_visits = 0
                    updated_visits = 0
                    inserted_items = 0
                    skipped_items = 0
                    media_uploaded = 0

                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        names = set(z.namelist())

                        for visit in preview:
                            row = FieldEvidenceVisit.query.filter_by(source_key=visit["source_key"]).first()
                            report_text = "\n\n".join(
                                f'[{m["date"]} {m["time"]}] {m["author"]}: {m["text"]}'
                                for m in visit["messages"]
                            )

                            if not row:
                                row = FieldEvidenceVisit(
                                    source_key=visit["source_key"],
                                    source_batch=batch_id,
                                    source_date=visit["date"],
                                    source_time=visit["time"],
                                    author=visit["author"],
                                    station_raw=visit["station_raw"],
                                    line_raw=visit["line_raw"],
                                    location_id=visit["location_id"],
                                    match_confidence=visit["confidence"],
                                    match_score=visit["match_score"],
                                    report_text=report_text,
                                    competition_text=visit["competition_text"],
                                    storage_source="R2" if _r2_available() else "LOCAL"
                                )
                                db.session.add(row)
                                db.session.flush()
                                inserted_visits += 1
                            else:
                                row.location_id = visit["location_id"]
                                row.match_confidence = visit["confidence"]
                                row.match_score = visit["match_score"]
                                row.report_text = report_text
                                row.competition_text = visit["competition_text"]
                                updated_visits += 1

                            for eq in visit["equipment"]:
                                existing_item = FieldEvidenceItem.query.filter_by(
                                    visit_id=row.id,
                                    equipment_type=eq["type"],
                                    identifier=eq["identifier"]
                                ).first()
                                if existing_item:
                                    skipped_items += 1
                                    continue

                                item = FieldEvidenceItem(
                                    visit_id=row.id,
                                    equipment_type=eq["type"],
                                    identifier=eq["identifier"],
                                    model=eq.get("model", ""),
                                    serial=eq.get("serial", ""),
                                    patrimony=eq.get("patrimony", ""),
                                    operational_status=eq.get("status", ""),
                                    source_line=eq.get("source_line", ""),
                                    base_asset_id=eq.get("base_asset_id"),
                                    inventory_id=eq.get("inventory_id"),
                                    audit_status=eq.get("audit_status", "PENDENTE"),
                                    audit_detail=(
                                        f'Base: {eq.get("base_status", "")}. '
                                        f'Inventário: {eq.get("inventory_status", "")}.'
                                    )
                                )
                                db.session.add(item)
                                inserted_items += 1

                            existing_media_hashes = {
                                x.sha256 for x in FieldEvidenceMedia.query.filter_by(visit_id=row.id).all()
                            }
                            for media_name in visit["attachments"]:
                                if media_name not in names:
                                    continue
                                data = z.read(media_name)
                                sha = hashlib.sha256(data).hexdigest()
                                if sha in existing_media_hashes:
                                    continue

                                global_media = FieldEvidenceMedia.query.filter_by(sha256=sha).first()
                                if global_media:
                                    # Uma mídia pertence a uma visita no modelo. Se repetida em outro relatório,
                                    # não duplica o arquivo; registra a repetição no texto de auditoria.
                                    continue

                                media_obj, is_new = _evidence_store_media(data, media_name, batch_id)
                                media_obj.visit_id = row.id
                                if is_new:
                                    db.session.add(media_obj)
                                    media_uploaded += 1
                                existing_media_hashes.add(sha)

                    db.session.commit()
                    import_result = {
                        "inserted_visits": inserted_visits,
                        "updated_visits": updated_visits,
                        "inserted_items": inserted_items,
                        "skipped_items": skipped_items,
                        "media_uploaded": media_uploaded,
                        "storage": "R2" if _r2_available() else "LOCAL TEMPORÁRIO",
                    }

                except Exception as exc:
                    db.session.rollback()
                    error = f"Erro durante a importação: {type(exc).__name__}: {exc}"

    return render_template(
        "import_whatsapp.html",
        preview=preview,
        summary=summary,
        error=error,
        staging_key=staging_key,
        import_result=import_result,
        storage_note=storage_note,
    )


@app.get("/api/evidencias-campo/resumo")
@dashboard_required
def field_evidence_summary_api():
    return jsonify({"ok": True, **_evidence_summary()})


@app.get("/evidencias-campo")
@dashboard_required
def field_evidence_page():
    q = request.args.get("q", "").strip()
    audit = request.args.get("audit", "").strip()
    location_id = request.args.get("location_id", type=int)
    visit_id = request.args.get("visit", type=int)

    query = FieldEvidenceVisit.query
    if location_id:
        query = query.filter(FieldEvidenceVisit.location_id == location_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (FieldEvidenceVisit.station_raw.ilike(like))
            | (FieldEvidenceVisit.author.ilike(like))
            | (FieldEvidenceVisit.line_raw.ilike(like))
        )
    if audit:
        query = query.join(
            FieldEvidenceItem,
            FieldEvidenceItem.visit_id == FieldEvidenceVisit.id
        ).filter(FieldEvidenceItem.audit_status == audit).distinct()

    visits = query.order_by(
        FieldEvidenceVisit.source_date.desc(),
        FieldEvidenceVisit.source_time.desc()
    ).limit(250).all()

    selected = db.session.get(FieldEvidenceVisit, visit_id) if visit_id else None
    selected_items = []
    selected_media = []
    selected_location = None
    if selected:
        selected_items = FieldEvidenceItem.query.filter_by(visit_id=selected.id).order_by(
            FieldEvidenceItem.equipment_type, FieldEvidenceItem.identifier
        ).all()
        selected_media = FieldEvidenceMedia.query.filter_by(visit_id=selected.id).order_by(
            FieldEvidenceMedia.id
        ).all()
        selected_location = db.session.get(Location, selected.location_id) if selected.location_id else None

    audit_statuses = [
        x[0] for x in db.session.query(FieldEvidenceItem.audit_status)
        .filter(FieldEvidenceItem.audit_status.isnot(None))
        .distinct().order_by(FieldEvidenceItem.audit_status).all()
    ]

    visit_cards = []
    for visit in visits:
        item_count = FieldEvidenceItem.query.filter_by(visit_id=visit.id).count()
        media_count = FieldEvidenceMedia.query.filter_by(visit_id=visit.id).count()
        review_count = FieldEvidenceItem.query.filter(
            FieldEvidenceItem.visit_id == visit.id,
            ~FieldEvidenceItem.audit_status.in_((
                "CONFORME / JÁ INVENTARIADO",
                "CONFIRMADO EM CAMPO / FALTA PROMOVER",
                "EVIDÊNCIA FORA DO PARQUE OFICIAL",
            ))
        ).count()
        loc = db.session.get(Location, visit.location_id) if visit.location_id else None
        visit_cards.append({
            "visit": visit, "items": item_count, "media": media_count,
            "review": review_count, "location": loc
        })

    return render_template(
        "field_evidence.html",
        summary=_evidence_summary(),
        visit_cards=visit_cards,
        selected=selected,
        selected_items=selected_items,
        selected_media=selected_media,
        selected_location=selected_location,
        audit_statuses=audit_statuses,
        q=q,
        audit=audit,
    )


@app.get("/evidencias-campo/midia/<int:media_id>")
@dashboard_required
def field_evidence_media(media_id):
    media = db.session.get(FieldEvidenceMedia, media_id)
    if not media:
        return "Mídia não encontrada.", 404

    if media.storage_kind == "r2":
        try:
            raw = _r2_get_bytes(media.storage_key)
            return send_file(
                io.BytesIO(raw),
                mimetype=media.mime_type or "application/octet-stream",
                download_name=media.original_name,
                max_age=3600,
            )
        except Exception:
            return "Não foi possível recuperar a mídia do R2.", 502

    return send_from_directory(
        UPLOAD_DIR / "field_evidence",
        media.storage_key,
        mimetype=media.mime_type,
        max_age=3600,
    )


@app.post("/evidencias-campo/item/<int:item_id>/promover")
@manager_required
def promote_evidence_item(item_id):
    item = db.session.get(FieldEvidenceItem, item_id)
    if not item:
        flash("Evidência não encontrada.")
        return redirect(url_for("field_evidence_page"))

    visit = db.session.get(FieldEvidenceVisit, item.visit_id)
    if not visit or not visit.location_id:
        flash("A evidência precisa estar associada a uma localidade antes de ser promovida.")
        return redirect(url_for("field_evidence_page", visit=visit.id if visit else None))

    type_map = {
        "ATM": "ATM",
        "VALIDADOR": "Validador de Recarga",
        "POS": "POS de Bilheteria",
    }
    inv_type = type_map.get(item.equipment_type)
    if not inv_type:
        flash("Esse tipo é mantido somente como evidência e não pode ser promovido automaticamente.")
        return redirect(url_for("field_evidence_page", visit=visit.id))

    existing = Inventory.query.filter(
        Inventory.location_id == visit.location_id,
        Inventory.equipment_type == inv_type,
        func.upper(Inventory.asset_identifier) == item.identifier.upper()
    ).first()
    if existing:
        item.inventory_id = existing.id
        item.audit_status = "CONFORME / JÁ INVENTARIADO"
        db.session.commit()
        flash("O equipamento já existia no inventário. A evidência foi vinculada.")
        return redirect(url_for("field_evidence_page", visit=visit.id))

    now = datetime.utcnow()
    inv = Inventory(
        location_id=visit.location_id,
        equipment_type=inv_type,
        base_asset_id=item.base_asset_id,
        asset_identifier=item.identifier,
        serial=item.serial or item.identifier,
        supplier="",
        model=item.model or "",
        exact_position="Importado após revisão da evidência de campo do WhatsApp.",
        mount="",
        operational_status=item.operational_status or "Não informado",
        connectivity="",
        network_id="",
        label_status="",
        in_base="Sim" if item.base_asset_id else "Não",
        divergence="Não" if item.base_asset_id else "Sim - identificação",
        notes=f"Evidência WhatsApp V4. Visita #{visit.id}. Responsável: {visit.author}.",
        technician_id=session["user_id"],
        created_at=now,
    )
    db.session.add(inv)
    db.session.flush()
    item.inventory_id = inv.id
    item.audit_status = "CONFORME / JÁ INVENTARIADO"
    db.session.commit()
    flash(f"{item.equipment_type} {item.identifier} promovido para o inventário.")
    return redirect(url_for("field_evidence_page", visit=visit.id))


@app.post("/evidencias-campo/visita/<int:visit_id>/associar")
@manager_required
def associate_evidence_visit(visit_id):
    visit = db.session.get(FieldEvidenceVisit, visit_id)
    if not visit:
        flash("Visita não encontrada.")
        return redirect(url_for("field_evidence_page"))

    location_id = request.form.get("location_id", type=int)
    loc = db.session.get(Location, location_id) if location_id else None
    if not loc:
        flash("Localidade inválida.")
        return redirect(url_for("field_evidence_page", visit=visit.id))

    visit.location_id = loc.id
    visit.match_confidence = "REVISADA PELO GESTOR"
    db.session.commit()
    flash(f"Evidência associada a {loc.location}.")
    return redirect(url_for("field_evidence_page", visit=visit.id))


def migrate_base_asset_columns():
    with db.engine.begin() as conn:
        statements = [
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS equipment_type VARCHAR(50)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS location_code VARCHAR(80)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS terminal_number VARCHAR(120)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS application VARCHAR(180)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS bom_id VARCHAR(120)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS bu_id VARCHAR(120)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS software_version VARCHAR(120)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS quantity INTEGER",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS base_notes TEXT",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS leasing_status VARCHAR(120)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS contract_end VARCHAR(80)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS installation_type VARCHAR(180)",
            "ALTER TABLE base_assets ADD COLUMN IF NOT EXISTS installation_date VARCHAR(80)",
            "CREATE INDEX IF NOT EXISTS ix_base_assets_equipment_type ON base_assets (equipment_type)",
        ]
        for statement in statements:
            conn.execute(db.text(statement))
        conn.execute(db.text("""
            UPDATE base_assets
            SET equipment_type = 'ATM'
            WHERE equipment_type IS NULL OR TRIM(equipment_type) = ''
        """))


def migrate_inventory_validator_columns():
    with db.engine.begin() as conn:
        statements = [
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS application VARCHAR(180)",
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS bom_id VARCHAR(120)",
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS bu_id VARCHAR(120)",
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS validator_top_id VARCHAR(120)",
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS software_version VARCHAR(120)",
        ]
        for statement in statements:
            conn.execute(db.text(statement))


@app.get("/admin/migrar-base-assets")
@manager_required
def migrar_base_assets():
    try:
        migrate_base_asset_columns()
        return jsonify({
            "ok": True,
            "mensagem": "Estrutura base_assets atualizada com sucesso.",
            "dados_preservados": True
        })
    except Exception as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 500


@app.get("/admin/migrar-inventory-validator")
@manager_required
def migrar_inventory_validator():
    try:
        migrate_inventory_validator_columns()
        return jsonify({
            "ok": True,
            "mensagem": "Estrutura Inventory atualizada para Validador.",
            "dados_preservados": True
        })
    except Exception as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 500



def sync_base_assets_1408(force=False):
    """Sincroniza a base detalhada das abas ATM, VALIDADOR, POS, TDI e BLOQUEIO."""
    source = DATA_DIR / "base_assets_1408.json"
    if not source.exists():
        return {"ok": False, "reason": "arquivo ausente", "inserted": 0, "updated": 0}

    rows = json.loads(source.read_text(encoding="utf-8"))

    # Atualiza automaticamente quando a estrutura/mapeamento da base muda.
    # As sentinelas evitam regravar milhares de linhas em todo cold start.
    if not force:
        sentinels = {
            "L01-PPQ-POS-13301": ("POS", "01 - AZUL", "METRO"),
            "TDI|SAC|220|1500070008": ("TDI", "02 - VERDE", "METRO"),
            "BLOQ|09 - ESMERALDA|OSASCO|356406": ("BLOQUEIO", "09 - ESMERALDA", "VIA MOBILIDADE"),
        }
        current_ok = True
        for key, expected in sentinels.items():
            obj = BaseAsset.query.filter_by(asset_key=key).first()
            if not obj:
                current_ok = False
                break
            if (normalize(obj.equipment_type), normalize(obj.line), normalize(obj.company)) != tuple(normalize(x) for x in expected):
                current_ok = False
                break
        if current_ok:
            return {"ok": True, "reason": "base 1408-5 já sincronizada", "inserted": 0, "updated": 0}

    existing = {x.asset_key: x for x in BaseAsset.query.all() if x.asset_key}
    allowed = {
        "equipment_type", "description", "company", "station_code", "location_code",
        "line", "locality", "terminal_number", "serial", "qrcode_id", "top_id",
        "products", "model", "supplier", "transactions", "pix", "mount",
        "base_status", "application", "bom_id", "bu_id", "software_version",
        "quantity", "base_notes", "leasing_status", "contract_end",
        "installation_type", "installation_date"
    }

    inserted = updated = 0
    for row in rows:
        key = (row.get("asset_key") or "").strip()
        if not key:
            continue
        obj = existing.get(key)
        if obj is None:
            obj = BaseAsset(asset_key=key)
            db.session.add(obj)
            existing[key] = obj
            inserted += 1
        else:
            updated += 1
        for field in allowed:
            if field in row:
                setattr(obj, field, row.get(field))

    db.session.commit()
    _invalidate_expected_cache()
    return {"ok": True, "reason": "sincronizada", "inserted": inserted, "updated": updated, "total": len(rows)}


@app.get("/api/base/summary")
@manager_required
def api_base_summary():
    rows = (
        db.session.query(BaseAsset.equipment_type, func.count(BaseAsset.id))
        .filter(~func.upper(func.coalesce(BaseAsset.base_status, "")).like("%INATIVO%"))
        .group_by(BaseAsset.equipment_type)
        .all()
    )
    return jsonify({
        "ok": True,
        "base_version": BASE_DATA_VERSION,
        "active_by_type": {str(k or "ATM"): int(v or 0) for k, v in rows}
    })


@app.get("/admin/sincronizar-base-1408")
@manager_required
def admin_sync_base_1408():
    try:
        return jsonify(sync_base_assets_1408(force=True))
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "erro": str(exc)}), 500

def migrate_location_reference_columns():
    with db.engine.begin() as conn:
        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_latitude DOUBLE PRECISION
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_longitude DOUBLE PRECISION
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_source VARCHAR(120)
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_updated_at TIMESTAMP
        """))

def migrate_location_reference_columns():
    with db.engine.begin() as conn:
        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_latitude DOUBLE PRECISION
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_longitude DOUBLE PRECISION
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_source VARCHAR(120)
        """))

        conn.execute(db.text("""
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS reference_updated_at TIMESTAMP
        """))

@app.route("/debug-conciliar-estacoes")
@manager_required
def debug_conciliar_estacoes():
    import json
    import re
    import unicodedata
    import urllib.parse
    import urllib.request
    from difflib import SequenceMatcher

    base_url = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows"

    def normalizar(texto):
        texto = texto or ""
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = texto.upper().strip()

        # Remove siglas internas, com ou sem espaços ao redor do hífen.
        # Exemplos: JOD- JOAO DIAS, LUZ - LUZ, BTO - SAO BENTO.
        m = re.match(r"^([A-Z0-9]{1,4})\s*-\s*(.+)$", texto)
        if m:
            texto = m.group(2).strip()

        texto = texto.replace("–", "-").replace("—", "-").replace("-", " ")
        texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()

        aliases = {
            "BARRA FUNDA": "PALMEIRAS BARRA FUNDA",
            "PALMEIRAS BARRA FUNDA": "PALMEIRAS BARRA FUNDA",
            "LAPA A": "LAPA LINHA 7",
            "LAPA B": "LAPA LINHA 8",
            "MANOEL FEIO": "ENGENHEIRO MANOEL FEIO",
            "JARDIM HELENA": "JARDIM HELENA VILA MARA",
            "JARDIM SAO PAULO": "AYRTON SENNA JARDIM SAO PAULO",
            "LIBERDADE": "JAPAO LIBERDADE",
            "PORTUGUESA TIETE": "PORTUGUESA TIETE",
            "BRESSER MOOCA": "BRESSER MOOCA",
            "CORINTHIANS ITAQUERA": "CORINTHIANS ITAQUERA",
            "GUILHERMINA ESPERANCA": "GUILHERMINA ESPERANCA",
            "SANTOS IMIGRANTES": "SANTOS IMIGRANTES",
            "USP LESTE": "USP LESTE",
            "GUARULHOS CECAP": "GUARULHOS CECAP",
            "AEROPORTO GUARULHOS": "AEROPORTO GUARULHOS",
            "JOAO DIAS": "JOAO DIAS",
            "INTERLAGOS": "PRIMAVERA INTERLAGOS",
            "MENDES": "MENDES BRUNO COVAS",
            "SANTO AMARO": "SANTO AMARO LINHA 9",
        }
        return aliases.get(texto, texto)

    def normalizar_linha(texto):
        texto = normalizar(texto)
        cores = {
            "01 AZUL": "AZUL", "1 AZUL": "AZUL",
            "02 VERDE": "VERDE", "2 VERDE": "VERDE",
            "03 VERMELHA": "VERMELHA", "3 VERMELHA": "VERMELHA",
            "04 AMARELA": "AMARELA", "4 AMARELA": "AMARELA",
            "05 LILAS": "LILAS", "5 LILAS": "LILAS",
            "06 LARANJA": "LARANJA", "6 LARANJA": "LARANJA",
            "07 RUBI": "RUBI", "7 RUBI": "RUBI",
            "08 DIAMANTE": "DIAMANTE", "8 DIAMANTE": "DIAMANTE",
            "09 ESMERALDA": "ESMERALDA", "9 ESMERALDA": "ESMERALDA",
            "10 TURQUESA": "TURQUESA",
            "11 CORAL": "CORAL",
            "12 SAFIRA": "SAFIRA",
            "13 JADE": "JADE",
            "15 PRATA": "PRATA",
            "17 OURO": "OURO",
        }
        return cores.get(texto, texto)

    def carregar_camada(nome):
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": nome,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
        }
        url = base_url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "InventarioAutopass/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8")).get("features", [])

    def preparar_estacoes():
        features = carregar_camada("estacao_metro") + carregar_camada("estacao_trem")
        saida = []
        for f in features:
            p = f.get("properties", {})
            g = f.get("geometry", {})
            coords = g.get("coordinates", [])
            if len(coords) < 2:
                continue
            saida.append({
                "nome": p.get("nm_estacao_metro_trem"),
                "nome_norm": normalizar(p.get("nm_estacao_metro_trem")),
                "linha": p.get("nm_linha_metro_trem"),
                "linha_norm": normalizar_linha(p.get("nm_linha_metro_trem")),
                "empresa": p.get("nm_empresa_metro_trem"),
                "situacao": p.get("tx_situacao_metro_trem"),
                "longitude": coords[0],
                "latitude": coords[1],
            })
        return saida

    def empresa_compativel(company, estacao):
        company = normalizar(company)
        linha = estacao["linha_norm"]

        if company == "METRO":
            return linha in {
                "AZUL", "VERDE", "VERMELHA", "AMARELA", "LILAS",
                "LARANJA", "PRATA", "OURO",
            }
        if company == "CPTM":
            return linha in {"RUBI", "TURQUESA", "CORAL", "SAFIRA", "JADE"}
        if company == "VIA MOBILIDADE":
            return linha in {"LILAS", "DIAMANTE", "ESMERALDA", "OURO"}
        return False

    def melhor_match(loc, estacoes):
        nome_loc = normalizar(loc.location)
        linha_loc = normalizar_linha(loc.line)

        candidatos = [
            e for e in estacoes
            if e["situacao"] == "OPERANDO" and empresa_compativel(loc.company, e)
        ]

        mesma_linha = [e for e in candidatos if e["linha_norm"] == linha_loc]
        if mesma_linha:
            candidatos = mesma_linha

        # Match exato/alias tem prioridade absoluta.
        for e in candidatos:
            if nome_loc == e["nome_norm"]:
                return {
                    "location_id": loc.id,
                    "company": loc.company,
                    "line": loc.line,
                    "location": loc.location,
                    "estacao_encontrada": e["nome"],
                    "linha_geosampa": e["linha"],
                    "empresa_geosampa": e["empresa"],
                    "latitude": e["latitude"],
                    "longitude": e["longitude"],
                    "score": 1.0,
                    "confianca": "ALTA",
                }

        melhor = None
        melhor_score = 0.0
        for e in candidatos:
            score = SequenceMatcher(None, nome_loc, e["nome_norm"]).ratio()
            if e["linha_norm"] == linha_loc:
                score += 0.08
            if score > melhor_score:
                melhor_score = score
                melhor = e

        if not melhor:
            return None

        if melhor_score >= 0.93:
            confianca = "ALTA"
        elif melhor_score >= 0.78:
            confianca = "REVISAR"
        else:
            confianca = "BAIXA"

        return {
            "location_id": loc.id,
            "company": loc.company,
            "line": loc.line,
            "location": loc.location,
            "estacao_encontrada": melhor["nome"],
            "linha_geosampa": melhor["linha"],
            "empresa_geosampa": melhor["empresa"],
            "latitude": melhor["latitude"],
            "longitude": melhor["longitude"],
            "score": round(min(melhor_score, 1.0), 3),
            "confianca": confianca,
        }

    try:
        estacoes = preparar_estacoes()
        localidades = (
            Location.query
            .filter(Location.company.in_(["METRO", "CPTM", "VIA MOBILIDADE"]))
            .order_by(Location.company, Location.line, Location.location)
            .all()
        )

        resultados = []
        for loc in localidades:
            match = melhor_match(loc, estacoes)
            if match:
                resultados.append(match)
            else:
                resultados.append({
                    "location_id": loc.id,
                    "company": loc.company,
                    "line": loc.line,
                    "location": loc.location,
                    "estacao_encontrada": None,
                    "latitude": None,
                    "longitude": None,
                    "score": 0,
                    "confianca": "NAO ENCONTRADA",
                })

        resumo = {
            "total_localidades": len(resultados),
            "alta": sum(1 for x in resultados if x["confianca"] == "ALTA"),
            "revisar": sum(1 for x in resultados if x["confianca"] == "REVISAR"),
            "baixa": sum(1 for x in resultados if x["confianca"] == "BAIXA"),
            "nao_encontrada": sum(1 for x in resultados if x["confianca"] == "NAO ENCONTRADA"),
        }

        return jsonify({"ok": True, "resumo": resumo, "resultados": resultados})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

with app.app_context():
    migrate_location_reference_columns()
    db.create_all()
    migrate_base_asset_columns()
    migrate_inventory_validator_columns()
    seed_data()
    sync_base_assets_1408(force=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
