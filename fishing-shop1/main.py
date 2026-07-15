import os
import uuid
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import SHOP_NAME, TELEGRAM_URL, TELEGRAM_USERNAME, telegram_order_link
from database import get_db, init_db

load_dotenv()

SOCIAL_PRESETS = {
    "telegram": ("Telegram", "✈"),
    "instagram": ("Instagram", "📸"),
    "tiktok": ("TikTok", "🎵"),
    "facebook": ("Facebook", "👤"),
    "youtube": ("YouTube", "▶"),
    "viber": ("Viber", "💬"),
}


def build_order_text(name, price, weight=""):
    text = f"Привіт! Хочу замовити:\n{name}\nЦіна: {float(price):.0f} ₴"
    if weight:
        text += f"\nФасування: {weight}"
    return text


def build_order_url(name, price, weight=""):
    return telegram_order_link(build_order_text(name, price, weight))

BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123"))


@app.context_processor
def inject_globals():
    return {
        "shop_name": SHOP_NAME,
        "telegram_url": TELEGRAM_URL,
        "telegram_username": TELEGRAM_USERNAME,
        "current_category": None,
        "search_query": None,
        "social_links": get_social_links(),
        "build_order_url": build_order_url,
        "general_telegram_url": telegram_order_link(
            "Привіт! Цікавлюсь прикормками TREIL ZOOM"
        ),
    }


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(UPLOAD_FOLDER / name)
    return name


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return wrapped


TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ye",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "y", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "",
    "ю": "yu", "я": "ya", "'": "", "’": "",
}


def slugify(text: str) -> str:
    import re
    text = text.strip().lower()
    result = []
    for ch in text:
        if ch in TRANSLIT:
            result.append(TRANSLIT[ch])
        elif ch.isalnum():
            result.append(ch)
        elif ch in " -_":
            result.append("-")
    slug = re.sub(r"-+", "-", "".join(result)).strip("-")
    return slug or "category"


def get_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM categories ORDER BY sort_order, name"
    ).fetchall()
    conn.close()
    return rows


def get_social_links(active_only=True):
    conn = get_db()
    query = "SELECT * FROM social_links"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY sort_order, id"
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def ensure_default_social():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM social_links").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO social_links (name, url, icon, sort_order, is_active) VALUES (?, ?, ?, ?, 1)",
            ("Telegram", TELEGRAM_URL, "✈", 0),
        )
        conn.commit()
    conn.close()


def get_categories_with_counts():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT c.*, COUNT(p.id) AS product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        GROUP BY c.id
        ORDER BY c.sort_order, c.name
        """
    ).fetchall()
    conn.close()
    return rows


def get_product_images(conn, product_id):
    return conn.execute(
        "SELECT * FROM product_images WHERE product_id = ? ORDER BY sort_order, id",
        (product_id,),
    ).fetchall()


def get_products(category_slug=None, search_query=None, featured_only=False, active_only=True):
    conn = get_db()
    query = """
        SELECT p.*, c.name AS category_name, c.slug AS category_slug,
               (SELECT filename FROM product_images pi
                WHERE pi.product_id = p.id ORDER BY sort_order, id LIMIT 1) AS main_image
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    if active_only:
        query += " AND p.is_active = 1"
    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)
    if featured_only:
        query += " AND p.is_featured = 1"
    if search_query:
        term = f"%{search_query.strip()}%"
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.weight LIKE ?)"
        params.extend([term, term, term])
    query += " ORDER BY p.sort_order, p.updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


@app.route("/")
def index():
    category = request.args.get("category", "").strip() or None
    search = request.args.get("q", "").strip() or None
    products = get_products(category_slug=category, search_query=search)
    featured = get_products(featured_only=True)[:4] if not category and not search else []
    return render_template(
        "index.html",
        products=products,
        featured=featured,
        categories=get_categories(),
        current_category=category,
        search_query=search,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = get_db()
    product = conn.execute(
        """
        SELECT p.*, c.name AS category_name, c.slug AS category_slug
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ? AND p.is_active = 1
        """,
        (product_id,),
    ).fetchone()
    if not product:
        conn.close()
        abort(404)
    images = get_product_images(conn, product_id)
    if not images:
        row = conn.execute(
            "SELECT filename FROM product_images WHERE product_id = ? ORDER BY sort_order, id LIMIT 1",
            (product_id,),
        ).fetchone()
        if row:
            images = [row]
    conn.close()

    order_text = build_order_text(product["name"], product["price"], product["weight"] or "")

    return render_template(
        "product.html",
        product=product,
        images=images,
        categories=get_categories(),
        telegram_order_url=telegram_order_link(order_text),
    )


# --- Admin ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("password", ""))
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Невірний логін або пароль", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    products = conn.execute(
        """
        SELECT p.*, c.name AS category_name,
               (SELECT filename FROM product_images pi
                WHERE pi.product_id = p.id ORDER BY sort_order, id LIMIT 1) AS main_image
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.sort_order, p.updated_at DESC
        """
    ).fetchall()
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "active": conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0],
        "categories": conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
    }
    conn.close()
    return render_template(
        "admin/dashboard.html", products=products, stats=stats
    )


@app.route("/admin/categories", methods=["GET", "POST"])
@login_required
def admin_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip() or slugify(name)
        sort_order = request.form.get("sort_order", "0").strip()
        sort_order = int(sort_order) if sort_order.isdigit() else 0
        if not name:
            flash("Вкажіть назву категорії", "error")
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO categories (name, slug, sort_order) VALUES (?, ?, ?)",
                    (name, slug, sort_order),
                )
                conn.commit()
                flash(f"Категорію «{name}» додано", "success")
            except Exception:
                flash("Така категорія вже існує (slug зайнятий)", "error")
            conn.close()
        return redirect(url_for("admin_categories"))

    return render_template(
        "admin/categories.html",
        categories=get_categories_with_counts(),
    )


@app.route("/admin/categories/<int:cat_id>/edit", methods=["GET", "POST"])
@login_required
def admin_category_edit(cat_id):
    conn = get_db()
    category = conn.execute(
        "SELECT * FROM categories WHERE id = ?", (cat_id,)
    ).fetchone()
    if not category:
        conn.close()
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip() or slugify(name)
        sort_order = request.form.get("sort_order", "0").strip()
        sort_order = int(sort_order) if sort_order.isdigit() else 0
        if not name:
            flash("Вкажіть назву", "error")
        else:
            try:
                conn.execute(
                    "UPDATE categories SET name=?, slug=?, sort_order=? WHERE id=?",
                    (name, slug, sort_order, cat_id),
                )
                conn.commit()
                flash("Категорію збережено", "success")
                conn.close()
                return redirect(url_for("admin_categories"))
            except Exception:
                flash("Slug вже зайнятий іншою категорією", "error")
        conn.close()
        return redirect(url_for("admin_category_edit", cat_id=cat_id))

    conn.close()
    return render_template("admin/category_form.html", category=category)


@app.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
def admin_category_delete(cat_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM products WHERE category_id = ?", (cat_id,)
    ).fetchone()[0]
    if count > 0:
        flash(f"Не можна видалити — у категорії {count} товар(ів). Спочатку перенеси їх.", "error")
    else:
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        flash("Категорію видалено", "success")
    conn.close()
    return redirect(url_for("admin_categories"))


@app.route("/admin/products/new", methods=["GET", "POST"])
@login_required
def admin_product_new():
    if request.method == "POST":
        return _save_product()
    return render_template(
        "admin/product_form.html", product=None, images=[], categories=get_categories()
    )


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def admin_product_edit(product_id):
    conn = get_db()
    if request.method == "POST":
        conn.close()
        return _save_product(product_id)
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        abort(404)
    images = get_product_images(conn, product_id)
    conn.close()
    return render_template(
        "admin/product_form.html",
        product=product,
        images=images,
        categories=get_categories(),
    )


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@login_required
def admin_product_delete(product_id):
    conn = get_db()
    images = conn.execute(
        "SELECT filename FROM product_images WHERE product_id = ?", (product_id,)
    ).fetchall()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    for img in images:
        path = UPLOAD_FOLDER / img["filename"]
        if path.exists():
            path.unlink()
    flash("Товар видалено", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/image/<int:image_id>/delete", methods=["POST"])
@login_required
def admin_image_delete(product_id, image_id):
    conn = get_db()
    row = conn.execute(
        "SELECT filename FROM product_images WHERE id = ? AND product_id = ?",
        (image_id, product_id),
    ).fetchone()
    if row:
        conn.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        conn.commit()
        path = UPLOAD_FOLDER / row["filename"]
        if path.exists():
            path.unlink()
    conn.close()
    flash("Фото видалено", "success")
    return redirect(url_for("admin_product_edit", product_id=product_id))


def _save_product(product_id=None):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    weight = request.form.get("weight", "").strip()
    price = request.form.get("price", "0").replace(",", ".")
    category_id = request.form.get("category_id") or None
    sort_order = request.form.get("sort_order", "0").strip()
    is_active = 1 if request.form.get("is_active") else 0
    is_featured = 1 if request.form.get("is_featured") else 0

    if not name:
        flash("Вкажіть назву", "error")
        return redirect(request.referrer or url_for("admin_dashboard"))

    try:
        price = float(price)
        sort_order = int(sort_order) if sort_order.isdigit() else 0
    except ValueError:
        flash("Некоректна ціна", "error")
        return redirect(request.referrer or url_for("admin_dashboard"))

    conn = get_db()
    fields = (name, description, price, weight, category_id, sort_order, is_active, is_featured)
    if product_id:
        conn.execute(
            """
            UPDATE products SET name=?, description=?, price=?, weight=?,
                category_id=?, sort_order=?, is_active=?, is_featured=?,
                updated_at=datetime('now') WHERE id=?
            """,
            (*fields, product_id),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO products (name, description, price, weight, category_id,
                sort_order, is_active, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            fields,
        )
        product_id = cur.lastrowid

    existing = conn.execute(
        "SELECT COUNT(*) FROM product_images WHERE product_id = ?", (product_id,)
    ).fetchone()[0]
    for i, file in enumerate(request.files.getlist("images")):
        filename = save_upload(file)
        if filename:
            conn.execute(
                "INSERT INTO product_images (product_id, filename, sort_order) VALUES (?, ?, ?)",
                (product_id, filename, existing + i),
            )

    conn.commit()
    conn.close()
    flash("Збережено", "success")
    return redirect(url_for("admin_product_edit", product_id=product_id))


@app.route("/admin/social", methods=["GET", "POST"])
@login_required
def admin_social():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "add":
            name = request.form.get("name", "").strip()
            url = request.form.get("url", "").strip()
            icon = request.form.get("icon", "🔗").strip() or "🔗"
            sort_order = request.form.get("sort_order", "0").strip()
            sort_order = int(sort_order) if sort_order.isdigit() else 0
            if not name or not url:
                flash("Вкажіть назву та посилання", "error")
            else:
                if not url.startswith(("http://", "https://", "tg://", "viber://")):
                    url = "https://" + url
                conn.execute(
                    "INSERT INTO social_links (name, url, icon, sort_order, is_active) VALUES (?, ?, ?, ?, 1)",
                    (name, url, icon, sort_order),
                )
                conn.commit()
                flash(f"«{name}» додано", "success")
        elif action == "toggle":
            link_id = request.form.get("link_id")
            row = conn.execute(
                "SELECT is_active FROM social_links WHERE id = ?", (link_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE social_links SET is_active = ? WHERE id = ?",
                    (0 if row["is_active"] else 1, link_id),
                )
                conn.commit()
                flash("Оновлено", "success")
        elif action == "delete":
            link_id = request.form.get("link_id")
            conn.execute("DELETE FROM social_links WHERE id = ?", (link_id,))
            conn.commit()
            flash("Видалено", "success")
        conn.close()
        return redirect(url_for("admin_social"))

    links = conn.execute(
        "SELECT * FROM social_links ORDER BY sort_order, id"
    ).fetchall()
    conn.close()
    return render_template("admin/social.html", links=links, presets=SOCIAL_PRESETS)


@app.route("/admin/social/<int:link_id>/edit", methods=["GET", "POST"])
@login_required
def admin_social_edit(link_id):
    conn = get_db()
    link = conn.execute(
        "SELECT * FROM social_links WHERE id = ?", (link_id,)
    ).fetchone()
    if not link:
        conn.close()
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        icon = request.form.get("icon", "🔗").strip() or "🔗"
        sort_order = request.form.get("sort_order", "0").strip()
        sort_order = int(sort_order) if sort_order.isdigit() else 0
        is_active = 1 if request.form.get("is_active") else 0
        if not name or not url:
            flash("Вкажіть назву та посилання", "error")
        else:
            if not url.startswith(("http://", "https://", "tg://", "viber://")):
                url = "https://" + url
            conn.execute(
                "UPDATE social_links SET name=?, url=?, icon=?, sort_order=?, is_active=? WHERE id=?",
                (name, url, icon, sort_order, is_active, link_id),
            )
            conn.commit()
            flash("Збережено", "success")
            conn.close()
            return redirect(url_for("admin_social"))
        conn.close()
        return redirect(url_for("admin_social_edit", link_id=link_id))

    conn.close()
    return render_template("admin/social_form.html", link=link, presets=SOCIAL_PRESETS)


if __name__ == "__main__":
    init_db()
    ensure_default_social()
    app.run(debug=True, host="127.0.0.1", port=5000)
