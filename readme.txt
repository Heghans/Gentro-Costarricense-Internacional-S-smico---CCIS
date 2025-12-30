# Opción 1: usando el archivo de requerimientos (recomendado)
pip install -r requirements.txt

# Opción 2: instalando manualmente
pip install flask mysql-connector-python werkzeug requests python-dotenv

# Por precaución, reinstalar Flask
pip install flask


-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS sismos_db;
USE sismos_db;


-- Tabla de usuarios
CREATE DATABASE sismos_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    fecha_nac DATE,
    password_hash VARCHAR(255) NOT NULL,
    foto_ruta VARCHAR(255),
    ultimo_login DATETIME,
    rol ENUM('admin', 'usuario') DEFAULT 'usuario'
);

-- Tabla de noticias
CREATE TABLE noticias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de sismos (opcional, si deseas almacenar localmente)
CREATE TABLE sismos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lat DECIMAL(9,6) NOT NULL,
    lng DECIMAL(9,6) NOT NULL,
    magnitud DECIMAL(3,1) NOT NULL,
    profundidad DECIMAL(5,1),
    lugar VARCHAR(255),
    fecha DATETIME
);



#En el archivo app.py, busca estas líneas (aprox. líneas 43-53) y coloca tu información de MySQL:

try:
    db = mysql.connector.connect(
        host="localhost",
        user="TU_USUARIO_MYSQL",
        password="TU_CONTRASEÑA",
        database="sismos_db"
    )
    cursor = db.cursor(dictionary=True)
except Error as e:
    print("Error al conectar a MySQL:", e)
    exit(1)



--- OJO -----
Crear administrador inicial

En las líneas 58-69 encontrarás este bloque comentado:

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


Descomenta este bloque solo la primera vez para generar el administrador, luego vuelve a comentarlo.



Ejecutar el proyecto

Desde la terminal, en la carpeta del proyecto:

python app.py


Luego abre tu navegador en:

http://127.0.0.1:5000/

5️⃣ Comandos útiles de MySQL
-- Ver las tablas
SHOW TABLES;

-- Ver datos
SELECT * FROM usuarios;
SELECT * FROM noticias;