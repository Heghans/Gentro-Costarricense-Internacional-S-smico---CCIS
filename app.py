# ------------------------------
# Importaciones necesarias
# ------------------------------
# Flask -> Framework web principal
# render_template -> Para mostrar HTML con variables
# request -> Capturar datos de formularios y URL
# redirect, url_for -> Redirigir páginas
# session -> Guardar datos de usuario logueado
# flash -> Mostrar mensajes rápidos en pantalla
# send_from_directory -> Servir archivos
# jsonify -> Devolver datos JSON (API)
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify

# MySQL -> Conexión a la base de datos
import mysql.connector
from mysql.connector import Error

# werkzeug.security -> Encriptar y verificar contraseñas
from werkzeug.security import generate_password_hash, check_password_hash

# Para manejar subida de archivos
from werkzeug.utils import secure_filename

# Librerías estándar
import os
import requests
from datetime import datetime
import threading  # Para ejecutar tareas en segundo plano
import time       # Para manejar pausas en esas tarea

# Configuración base del proyecto
app = Flask(__name__)
app.secret_key = "clave_secreta_segura"  # Clave para sesiones seguras

UPLOAD_FOLDER = "static/uploads"  # Carpeta donde se guardan fotos de perfil
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}  # Tipos de archivos permitidos
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Rutas para los datos de sismos
DATA_PATH = "static/data/sismos.geojson"  # Donde se guardarán los datos descargados
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"  # API oficial de USGS
# Conexión a MySQL
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sismos_db"
    )
    cursor = db.cursor(dictionary=True)
except Error as e:
    print("Error al conectar a MySQL:", e)
    exit(1)




# # Crear admin si no existe
# cursor.execute("SELECT * FROM usuarios WHERE email=%s", ("admin@test.com",))
# admin = cursor.fetchone()
# if not admin:
#     admin_hash = generate_password_hash("root")
#     cursor.execute("""
#         INSERT INTO usuarios (nombre, apellidos, email, telefono, fecha_nac, password_hash, rol)
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#     """, ("Admin", "Sistema", "admin@test.com", "00000000", "1990-01-01", admin_hash, "admin"))
#     db.commit()
#     print("✅ Admin creado con contraseña: root")
    



# Función para actualizar sismos cada 6 horas
# La API devuelve datos en formato GeoJSON que guardamos en un archivo local.
def actualizar_sismos():
    while True:
        try:
            print("Descargando datos de sismos...")
            params = {
                "format": "geojson",
                "starttime": "2025-07-12",
                "endtime": datetime.today().strftime("%Y-%m-%d"),
                "minmagnitude": 4.5
            }
            resp = requests.get(USGS_URL, params=params, timeout=15)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
                with open(DATA_PATH, "wb") as f:
                    f.write(resp.content)
                print("✅ Datos de sismos actualizados")
            else:
                print(f"❌ Error al descargar datos: {resp.status_code}")
        except Exception as e:
            print(f"⚠ Error en actualización: {e}")
        time.sleep(6 * 60 * 60)  # cada 6 horas

# Lanzar hilo de actualización en segundo plano
threading.Thread(target=actualizar_sismos, daemon=True).start()

# Función para validar extensión de archivo
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Noticias disponibles en todas las páginas
def get_noticias():
    cursor.execute("SELECT * FROM noticias ORDER BY fecha DESC")
    return cursor.fetchall()

# Página principal
@app.route("/")
def index():
    return render_template("index.html", noticias=get_noticias())

# Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellidos = request.form["apellidos"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        fecha_nac = request.form["fecha_nac"]
        password = request.form["password"]
        password2 = request.form["password2"]

        if password != password2:
            flash("Las contraseñas no coinciden", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        foto_ruta = None
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto and allowed_file(foto.filename):
                filename = secure_filename(f"{email}_{foto.filename}")
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                foto_ruta = f"{UPLOAD_FOLDER}/{filename}"

        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellidos, email, telefono, fecha_nac, password_hash, foto_ruta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre, apellidos, email, telefono, fecha_nac, password_hash, foto_ruta))
            db.commit()
            flash("Registro exitoso. Ahora puedes iniciar sesión", "success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Error: {e}", "error")

    return render_template("register.html", noticias=get_noticias())

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user is not None and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_nombre"] = user["nombre"]
            session["user_rol"] = user["rol"]

            cursor.execute("UPDATE usuarios SET ultimo_login=%s WHERE id=%s", (datetime.now(), user["id"]))
            db.commit()

            return redirect(url_for("admin" if user["rol"] == "admin" else "mapa"))
        else:
            flash("Credenciales inválidas", "error")

    return render_template("login.html", noticias=get_noticias())

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Panel de administración
@app.route("/admin")
def admin():
    if session.get("user_rol") != "admin":
        return redirect(url_for("login"))
    cursor.execute("SELECT id, nombre, apellidos, email, ultimo_login FROM usuarios WHERE rol='visitante'")
    usuarios = cursor.fetchall()
    return render_template("admin.html", noticias=get_noticias(), usuarios=usuarios)




# ----------------------------
# CRUD Noticias (solo admin)
# ----------------------------
@app.route("/admin/noticias", methods=["GET", "POST"])
def crud_noticias():
    if session.get("user_rol") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form["titulo"]
        contenido = request.form["contenido"]
        cursor.execute(
            "INSERT INTO noticias (titulo, contenido, fecha) VALUES (%s, %s, NOW())",
            (titulo, contenido)
        )
        db.commit()
        flash("Noticia agregada correctamente", "success")
        return redirect(url_for("crud_noticias"))

    cursor.execute("SELECT * FROM noticias ORDER BY fecha DESC")
    todas_noticias = cursor.fetchall()
    return render_template("crud_noticias.html", noticias=get_noticias(), todas_noticias=todas_noticias)

@app.route("/admin/noticias/editar/<int:noticia_id>", methods=["GET", "POST"])
def editar_noticia(noticia_id):
    if session.get("user_rol") != "admin":
        return redirect(url_for("login"))

    cursor.execute("SELECT * FROM noticias WHERE id=%s", (noticia_id,))
    noticia = cursor.fetchone()

    if not noticia:
        flash("⚠ Noticia no encontrada", "error")
        return redirect(url_for("crud_noticias"))

    if request.method == "POST":
        titulo = request.form["titulo"]
        contenido = request.form["contenido"]
        cursor.execute(
            "UPDATE noticias SET titulo=%s, contenido=%s WHERE id=%s",
            (titulo, contenido, noticia_id)
        )
        db.commit()
        flash("Noticia actualizada correctamente", "success")
        return redirect(url_for("crud_noticias"))

    return render_template("editar_noticia.html", noticias=get_noticias(), noticia=noticia)

@app.route("/admin/noticias/eliminar/<int:noticia_id>")
def eliminar_noticia(noticia_id):
    if session.get("user_rol") != "admin":
        return redirect(url_for("login"))

    cursor.execute("DELETE FROM noticias WHERE id=%s", (noticia_id,))
    db.commit()
    flash("🗑 Noticia eliminada correctamente", "success")
    return redirect(url_for("crud_noticias"))


# Eliminar usuario
@app.route("/admin/eliminar_usuario/<int:user_id>")
def eliminar_usuario(user_id):
    if session.get("user_rol") != "admin":
        return redirect(url_for("login"))
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
    db.commit()
    flash("Usuario eliminado", "success")
    return redirect(url_for("admin"))

# Perfil de usuario
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()

    if request.method == "POST":
        nombre = request.form["nombre"]
        fecha_nac = request.form["fecha_nac"]
        password = request.form["password"]

        password_hash = user["password_hash"]
        if password:
            password_hash = generate_password_hash(password)

        foto_ruta = user["foto_ruta"]
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto and allowed_file(foto.filename):
                filename = secure_filename(f"{user['email']}_{foto.filename}")
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                foto_ruta = f"{UPLOAD_FOLDER}/{filename}"

        cursor.execute("""
            UPDATE usuarios SET nombre=%s, fecha_nac=%s, password_hash=%s, foto_ruta=%s WHERE id=%s
        """, (nombre, fecha_nac, password_hash, foto_ruta, user["id"]))
        db.commit()

        flash("Perfil actualizado", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", noticias=get_noticias(), user=user)

# Página del mapa
@app.route("/mapa")
def mapa():
    return render_template("mapa.html", noticias=get_noticias())

@app.route("/api/sismos_filtrados")
def api_sismos_filtrados():
    # Parámetros GET
    min_magnitud = request.args.get("min_magnitud", 0)
    start_time = request.args.get("start_time", "2025-01-01")
    end_time = request.args.get("end_time", datetime.today().strftime("%Y-%m-%d"))

    # 🔹 En vez de llamar siempre a la API, leemos el archivo cacheado
    try:
        with open(DATA_PATH, "rb") as f:
            data = requests.compat.json.loads(f.read())
    except Exception as e:
        return jsonify({"error": f"No se pudieron cargar los datos: {e}"}), 500

    # Convertir datos
    sismos = []
    for feature in data.get("features", []):
        coords = feature["geometry"]["coordinates"]
        props = feature["properties"]
        if props["mag"] >= float(min_magnitud):
            fecha_sismo = datetime.utcfromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            if start_time <= fecha_sismo.split(" ")[0] <= end_time:
                sismos.append({
                    "lat": coords[1],
                    "lng": coords[0],
                    "magnitud": props["mag"],
                    "profundidad": coords[2],
                    "fecha": fecha_sismo,
                    "lugar": props["place"]
                })

    return jsonify(sismos)


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
