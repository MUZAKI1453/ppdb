from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from extensions_db import db, login_manager


# ==================================================
# Factory Function
# Membuat dan mengkonfigurasi aplikasi Flask
# ==================================================
def create_app():
    app = Flask(__name__)

    # Memuat konfigurasi aplikasi
    app.config.from_object(Config)

    # Inisialisasi extension
    db.init_app(app)
    login_manager.init_app(app)

    # Redirect ke halaman login jika belum login
    login_manager.login_view = 'auth.login'

    # ==============================================
    # User Loader Flask-Login
    # Mengambil data user dari session login
    # ==============================================
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ==============================================
    # Registrasi Blueprint
    # ==============================================
    from routes.auth import auth
    from routes.admin import admin
    from routes.siswa import siswa
    from models.berkas import Berkas

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(siswa)

    # ==============================================
    # Inisialisasi Database & Admin Default
    # ==============================================
    with app.app_context():
        # Membuat seluruh tabel jika belum ada
        db.create_all()

        create_default_admin()

    return app


# ==================================================
# Seeder Admin Default
# Akan membuat akun admin otomatis jika belum ada
# ==================================================
def create_default_admin():
    from models.user import User
    from models.calon_siswa import CalonSiswa

    admin = User.query.filter_by(
        username='admin'
    ).first()

    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )

        db.session.add(admin)
        db.session.commit()

        print("[INFO] Admin default berhasil dibuat")


# ==================================================
# Entry Point Aplikasi
# ==================================================
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
