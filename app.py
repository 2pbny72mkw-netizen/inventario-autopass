
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
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Index, func, case, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError, BotoCoreError

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
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
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

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
                base_status=a.get("base_status", "")
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
            return redirect(url_for("technician"))
        return fn(*args, **kwargs)
    return inner


@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return redirect(url_for("manager" if session.get("role") == "manager" else "technician"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session.update(user_id=user.id, name=user.name, role=user.role)
            return redirect(url_for("manager" if user.role == "manager" else "technician"))
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


@app.get("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"ok": True, "database": "connected"})
    except Exception as exc:
        return jsonify({"ok": False, "database": "error", "detail": str(exc)}), 500


@app.get("/api/locations")
@login_required
def api_locations():
    inventoried = func.count(Inventory.id)
    operational = func.coalesce(func.sum(case((Inventory.operational_status == "Operacional", 1), else_=0)), 0)
    inoperative = func.coalesce(func.sum(case((Inventory.operational_status == "Inoperante", 1), else_=0)), 0)

    rows = (
        db.session.query(
            Location,
            inventoried.label("inventoried"),
            operational.label("operational"),
            inoperative.label("inoperative")
        )
        .outerjoin(Inventory, Inventory.location_id == Location.id)
        .group_by(Location.id)
        .order_by(Location.company, Location.line, Location.location)
        .all()
    )

    out = []
    for loc, inv_count, op_count, inop_count in rows:
        out.append({
            "id": loc.id,
            "company": loc.company,
            "line": loc.line,
            "location": loc.location,
            "base_status": loc.base_status,
            "expected_atm": loc.expected_atm,
            "expected_validator": loc.expected_validator,
            "expected_pos": loc.expected_pos,
            "survey_status": loc.survey_status,
            "started_at": loc.started_at.isoformat(timespec="seconds") if loc.started_at else None,
            "completed_at": loc.completed_at.isoformat(timespec="seconds") if loc.completed_at else None,
            "completed_by": loc.completed_by,
            "inventoried": int(inv_count or 0),
            "operational": int(op_count or 0),
            "inoperative": int(inop_count or 0),
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
            "technician": technician_name,
            "attachments_count": attachment_count,
        })
    return jsonify(out)


@app.get("/api/location/<int:location_id>/assets")
@login_required
def api_assets(location_id):
    loc = db.session.get(Location, location_id)
    if not loc:
        return jsonify([])

    line = normalize(loc.line)
    company = normalize(loc.company)
    station_text = normalize(loc.location)
    already = {
        x[0] for x in db.session.query(Inventory.base_asset_id)
        .filter(Inventory.location_id == location_id, Inventory.base_asset_id.isnot(None))
        .all()
    }

    out = []
    for a in BaseAsset.query.all():
        asset_company = normalize(a.company)
        if normalize(a.line) != line:
            continue
        if company not in asset_company and asset_company not in company:
            continue

        station_name = normalize(a.locality)
        code = normalize(a.station_code)
        station_match = (
            (station_name and (station_name in station_text or station_text.endswith(station_name)))
            or (code and station_text.startswith(code + " "))
        )
        if station_match:
            out.append({
                "id": a.id,
                "asset_key": a.asset_key,
                "description": a.description,
                "company": a.company,
                "station_code": a.station_code,
                "line": a.line,
                "locality": a.locality,
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
                "already_inventoried": a.id in already,
            })
    return jsonify(out)


@app.post("/api/inventory")
@login_required
def create_inventory():
    location_id = request.form.get("location_id", type=int)
    equipment_type = request.form.get("equipment_type", "").strip()
    base_asset_id = request.form.get("base_asset_id", type=int)
    serial = request.form.get("serial", "").strip()
    asset_identifier = request.form.get("asset_identifier", "").strip() or serial

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
        exact_position=request.form.get("exact_position", ""),
        mount=request.form.get("mount", ""),
        operational_status=request.form.get("operational_status", ""),
        connectivity=request.form.get("connectivity", ""),
        network_id=request.form.get("network_id", ""),
        label_status=request.form.get("label_status", ""),
        in_base=request.form.get("in_base", ""),
        divergence=request.form.get("divergence", ""),
        notes=request.form.get("notes", ""),
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


@app.post("/api/location/<int:location_id>/complete")
@login_required
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


@app.get("/api/dashboard")
@manager_required
def dashboard():
    total = Location.query.count()
    pending = Location.query.filter_by(survey_status="PENDENTE").count()
    progress = Location.query.filter_by(survey_status="EM ANDAMENTO").count()
    completed = Location.query.filter_by(survey_status="CONCLUIDA").count()

    expected = db.session.query(
        func.coalesce(
            func.sum(Location.expected_atm + Location.expected_validator + Location.expected_pos), 0
        )
    ).scalar() or 0

    inventoried = Inventory.query.count()
    inoperative = Inventory.query.filter_by(operational_status="Inoperante").count()
    divergences = Inventory.query.filter(
        Inventory.divergence.isnot(None),
        Inventory.divergence.notin_(["", "Não", "Nao"])
    ).count()

    companies = (
        db.session.query(
            Location.company.label("company"),
            func.count(Location.id).label("total"),
            func.sum(case((Location.survey_status == "PENDENTE", 1), else_=0)).label("pending"),
            func.sum(case((Location.survey_status == "EM ANDAMENTO", 1), else_=0)).label("progress"),
            func.sum(case((Location.survey_status == "CONCLUIDA", 1), else_=0)).label("completed")
        )
        .group_by(Location.company)
        .order_by(Location.company)
        .all()
    )

    return jsonify({
        "totals": {
            "total": total,
            "pending": pending,
            "progress": progress,
            "completed": completed,
            "expected": int(expected)
        },
        "inventory": {
            "inventoried": inventoried,
            "inoperative": inoperative,
            "divergences": divergences
        },
        "by_company": [{
            "company": x.company,
            "total": int(x.total or 0),
            "pending": int(x.pending or 0),
            "progress": int(x.progress or 0),
            "completed": int(x.completed or 0),
        } for x in companies]
    })


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
    users = User.query.order_by(User.name).all()
    return render_template("users.html", users=users)


@app.post("/usuarios/novo")
@manager_required
def create_user():
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "technician").strip()

    if not name or not username or not password:
        flash("Nome, usuário e senha são obrigatórios.")
        return redirect(url_for("users_page"))

    if len(password) < 8:
        flash("A senha deve ter pelo menos 8 caracteres.")
        return redirect(url_for("users_page"))

    if role not in ("manager", "technician"):
        role = "technician"

    if User.query.filter(func.lower(User.username) == username.lower()).first():
        flash("Já existe um usuário com esse login.")
        return redirect(url_for("users_page"))

    db.session.add(User(
        name=name,
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        active=True
    ))
    db.session.commit()
    flash("Usuário criado com sucesso.")
    return redirect(url_for("users_page"))


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

    user.active = not user.active
    db.session.commit()
    flash("Status do usuário atualizado.")
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
    # Mensagem exportada no formato:
    # [dd/mm/aaaa, hh:mm:ss] Autor: texto...
    pattern = re.compile(
        r'^\[(\d{2}/\d{2}/\d{4}),\s*(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s?(.*)$'
    )
    messages = []
    current = None
    for raw in chat_text.splitlines():
        line = raw.replace("\u200e", "").replace("\ufeff", "")
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


def _wa_extract_station(text):
    # Ex.: Estação Anhangabau Linha 3-Vermelha Plataforma Formosa
    clean = re.sub(r'<anexado:[^>]+>', '', text or '', flags=re.I).strip()
    m = re.search(
        r'Est[aã]ção\s+(.+?)\s+Linha\s+(\d{1,2})\s*[-–]\s*([A-Za-zÀ-ÿ]+)(.*)',
        clean, flags=re.I | re.S
    )
    if not m:
        return None
    station = re.sub(r'\s+', ' ', m.group(1)).strip(" -")
    number = m.group(2).zfill(2)
    color = m.group(3).upper()
    tail = re.sub(r'\s+', ' ', m.group(4)).strip()
    line_label = f"{number} - {color}"
    return {"station": station, "line": line_label, "detail": tail}


def _wa_equipment_rows(text):
    clean = re.sub(r'<anexado:[^>]+>', '', text or '', flags=re.I)
    rows = []

    # Validadores: captura números depois de VALIDADOR/VALIDADORES/VALIDADOREZ
    for m in re.finditer(r'VALIDADOR(?:ES|EZ)?\s*:?\s*([^\n]+)', clean, flags=re.I):
        nums = re.findall(r'\b\d{2,7}\b', m.group(1))
        for n in nums:
            rows.append({"type": "Validador de Recarga", "identifier": n, "model": ""})

    # ATM: uma linha pode conter um ou vários IDs
    for line in clean.splitlines():
        if re.search(r'\bATM\b', line, flags=re.I):
            label = line.strip()
            # remove patrimônios para não tratá-los como IDs principais
            without_patr = re.sub(r'\(?\s*Patrim[oô]nio\s*\d+\s*\)?', '', label, flags=re.I)
            ids = re.findall(r'\b\d{4,8}\b', without_patr)
            model_match = re.search(r'ATM\s+([^:]+):', label, flags=re.I)
            model = model_match.group(1).strip() if model_match else ""
            for n in ids:
                rows.append({"type": "ATM", "identifier": n, "model": model})

    # Rack sem identificação numérica: gera identificador provisório só para prévia
    rack_count = len(re.findall(r'\bRacks?\b', clean, flags=re.I))
    for idx in range(rack_count):
        rows.append({"type": "Rack de Comunicação", "identifier": f"RACK-{idx+1}", "model": ""})

    # Remove duplicatas dentro da mesma mensagem
    seen = set()
    out = []
    for r in rows:
        key = (r["type"], r["identifier"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _wa_match_location(station_name, line_label):
    ns = normalize(station_name)
    nl = normalize(line_label)

    candidates = Location.query.filter(func.upper(Location.line).like(f"%{line_label.split(' - ')[0]}%")).all()
    exact = []
    for loc in candidates:
        location_text = normalize(loc.location)
        # remove sigla inicial tipo "BGD - BRIGADEIRO"
        if " - " in location_text:
            location_name = location_text.split(" - ", 1)[1]
        else:
            location_name = location_text
        if ns == location_name or ns in location_name or location_name in ns:
            exact.append(loc)

    if len(exact) == 1:
        return exact[0], "SEGURA"
    if len(exact) > 1:
        # prioriza METRO para linhas 1,2,3
        metro = [x for x in exact if normalize(x.company) in ("METRO", "METRÔ")]
        if len(metro) == 1:
            return metro[0], "SEGURA"
        return exact[0], "REVISAR"
    return None, "NAO IDENTIFICADA"


@app.get("/r2-status")
@manager_required
def r2_status():
    ok, message = r2_test_connection()
    status_code = 200 if ok else 500
    return jsonify({
        "ok": ok,
        "storage": "Cloudflare R2",
        "bucket": os.environ.get("R2_BUCKET_NAME", ""),
        "message": message
    }), status_code


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
        current_visit = None
        visit_index = 0

        for msg in messages:
            station = _wa_extract_station(msg["text"])
            attachments = [a for a in _wa_extract_attachments(msg["text"]) if a in available_media]

            if station:
                visit_index += 1
                loc, confidence = _wa_match_location(station["station"], station["line"])
                current_visit = {
                    "visit_index": visit_index,
                    "date": msg["date"],
                    "time": msg["time"],
                    "author": msg["author"],
                    "station_raw": station["station"],
                    "line_raw": station["line"],
                    "detail": station["detail"],
                    "location_id": loc.id if loc else None,
                    "location_name": loc.location if loc else "",
                    "company": loc.company if loc else "",
                    "confidence": confidence,
                    "attachments": list(attachments),
                    "equipment": []
                }

                for eq_index, eq in enumerate(_wa_equipment_rows(msg["text"]), start=1):
                    # Rack não possui ID físico na mensagem; cria ID determinístico por visita.
                    if eq["type"] == "Rack de Comunicação" and eq["identifier"].startswith("RACK-"):
                        dt_ref = msg["date"].replace("/", "") + "-" + msg["time"].replace(":", "")
                        eq["identifier"] = f"RACK-WA-{dt_ref}-{eq_index}"

                    duplicate = False
                    duplicate_info = ""
                    if loc:
                        found = (
                            db.session.query(Inventory, User.name.label("technician"))
                            .join(User, User.id == Inventory.technician_id)
                            .filter(
                                Inventory.location_id == loc.id,
                                Inventory.equipment_type == eq["type"],
                                func.upper(Inventory.asset_identifier) == eq["identifier"].upper()
                            ).first()
                        )
                        if found:
                            duplicate = True
                            inv, tech_name = found
                            duplicate_info = f"Já cadastrado por {tech_name}"

                    eq["duplicate"] = duplicate
                    eq["duplicate_info"] = duplicate_info
                    current_visit["equipment"].append(eq)

                visits.append(current_visit)

            elif current_visit and attachments:
                current_visit["attachments"].extend(
                    a for a in attachments if a not in current_visit["attachments"]
                )

        summary = {
            "messages": len(messages),
            "media_total": len([n for n in names if not n.lower().endswith(".txt")]),
            "visits": len(visits),
            "equipment": sum(len(v["equipment"]) for v in visits),
            "safe": sum(1 for v in visits if v["confidence"] == "SEGURA"),
            "review": sum(1 for v in visits if v["confidence"] == "REVISAR"),
            "unmatched": sum(1 for v in visits if v["confidence"] == "NAO IDENTIFICADA"),
            "duplicates": sum(1 for v in visits for e in v["equipment"] if e["duplicate"]),
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


@app.route("/importar-whatsapp", methods=["GET", "POST"])
@manager_required
def import_whatsapp():
    preview = None
    summary = None
    error = None
    staging_key = None
    import_result = None

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

                    batch_id = uuid.uuid4().hex
                    safe_name = secure_filename(upload.filename) or "whatsapp.zip"
                    staging_key = f"whatsapp/fontes/{batch_id}/{safe_name}"
                    _r2_put_bytes(staging_key, raw, "application/zip")
                except Exception as exc:
                    error = f"Não foi possível analisar o ZIP: {exc}"

        elif action == "import":
            staging_key = request.form.get("staging_key", "").strip()
            mark_completed = request.form.get("mark_completed") == "1"

            if not staging_key:
                error = "Arquivo de origem não encontrado. Analise o ZIP novamente."
            else:
                try:
                    raw = _r2_get_bytes(staging_key)
                    preview, summary = _wa_analyze_archive(raw)

                    inserted = 0
                    skipped_duplicates = 0
                    safe_visits = 0
                    media_uploaded = 0
                    imported_locations = set()
                    uploaded_media = {}

                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        names = set(z.namelist())
                        batch_root = staging_key.rsplit("/", 1)[0].replace("/fontes/", "/midias/")

                        for visit in preview:
                            if visit["confidence"] != "SEGURA" or not visit["location_id"]:
                                continue

                            loc = db.session.get(Location, visit["location_id"])
                            if not loc:
                                continue

                            safe_visits += 1
                            imported_locations.add(loc.id)

                            # Sobe cada mídia apenas uma vez no R2.
                            media_refs = []
                            for media_name in visit["attachments"]:
                                if media_name not in names:
                                    continue
                                if media_name not in uploaded_media:
                                    data = z.read(media_name)
                                    base = secure_filename(Path(media_name).name) or f"midia-{uuid.uuid4().hex}"
                                    object_key = f"{batch_root}/{base}"
                                    mime = mimetypes.guess_type(base)[0] or "application/octet-stream"
                                    _r2_put_bytes(object_key, data, mime)
                                    uploaded_media[media_name] = (object_key, mime)
                                    media_uploaded += 1
                                media_refs.append((media_name, *uploaded_media[media_name]))

                            for eq in visit["equipment"]:
                                existing = Inventory.query.filter(
                                    Inventory.location_id == loc.id,
                                    Inventory.equipment_type == eq["type"],
                                    func.upper(Inventory.asset_identifier) == eq["identifier"].upper()
                                ).first()

                                if existing:
                                    skipped_duplicates += 1
                                    continue

                                try:
                                    dt = datetime.strptime(
                                        f'{visit["date"]} {visit["time"]}',
                                        "%d/%m/%Y %H:%M:%S"
                                    )
                                except Exception:
                                    dt = datetime.utcnow()

                                notes = (
                                    f'Importado do WhatsApp. Responsável informado: {visit["author"]}. '
                                    f'Origem: {staging_key}.'
                                )

                                inv = Inventory(
                                    location_id=loc.id,
                                    equipment_type=eq["type"],
                                    asset_identifier=eq["identifier"],
                                    serial=eq["identifier"],
                                    model=eq.get("model", ""),
                                    exact_position=visit.get("detail", ""),
                                    operational_status="Não informado (WhatsApp)",
                                    connectivity="",
                                    network_id="",
                                    label_status="",
                                    in_base="Sim",
                                    divergence="Não",
                                    notes=notes,
                                    technician_id=session["user_id"],
                                    created_at=dt
                                )
                                db.session.add(inv)
                                db.session.flush()

                                for original_name, object_key, mime in media_refs:
                                    db.session.add(Attachment(
                                        inventory_id=inv.id,
                                        original_name=Path(original_name).name,
                                        stored_name=object_key,
                                        mime_type=mime
                                    ))

                                inserted += 1

                            if mark_completed:
                                loc.survey_status = "CONCLUIDA"
                                loc.completed_at = datetime.utcnow()
                                loc.completed_by = session["user_id"]
                            elif loc.survey_status == "PENDENTE":
                                loc.survey_status = "EM ANDAMENTO"
                                loc.started_at = datetime.utcnow()

                    db.session.commit()

                    import_result = {
                        "safe_visits": safe_visits,
                        "inserted": inserted,
                        "duplicates": skipped_duplicates,
                        "media_uploaded": media_uploaded,
                        "locations": len(imported_locations),
                        "completed": mark_completed
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
        import_result=import_result
    )


with app.app_context():
    db.create_all()
    seed_data()

@app.route("/migrar-usuarios-temporario")
def migrar_usuarios_temporario():
    if request.args.get("key") != os.environ.get("INVENTARIO_SECRET_KEY"):
        return "NAO AUTORIZADO", 403

    try:
        with db.engine.begin() as conn:
            conn.execute(db.text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS user_code VARCHAR(30)
            """))

            conn.execute(db.text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS email VARCHAR(180)
            """))

            conn.execute(db.text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS phone VARCHAR(30)
            """))

            conn.execute(db.text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS photo_url VARCHAR(500)
            """))

            conn.execute(db.text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_code
                ON users (user_code)
            """))

            conn.execute(db.text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email
                ON users (email)
            """))

            conn.execute(db.text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone
                ON users (phone)
            """))

        return "USUARIOS MIGRADOS COM SUCESSO"

    except Exception as e:
        return f"ERRO: {str(e)}", 500
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
