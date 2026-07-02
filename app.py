from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from extensions_db import db, login_manager


# ==================================================
# Factory Function
# ==================================================
def create_app():
    app = Flask(__name__)

    # ==============================================
    # Load Config
    # ==============================================
    app.config.from_object(Config)

    # ==============================================
    # Init Extensions
    # ==============================================
    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'

    # ==============================================
    # Import Model User
    # ==============================================
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(
            User,
            int(user_id)
        )

    # ==============================================
    # Blueprint
    # ==============================================
    from routes.auth import auth
    from routes.admin import admin
    from routes.siswa import siswa

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(siswa)

    # ==============================================
    # Database Initialization
    # ==============================================
    with app.app_context():
        # --------------------------
        # Import seluruh model
        # agar SQLAlchemy mengenali
        # semua tabel
        # --------------------------

        from models.user import User
        from models.calon_siswa import CalonSiswa
        from models.berkas import Berkas

        from models.alamat_siswa import AlamatSiswa
        from models.data_ayah import DataAyah
        from models.data_ibu import DataIbu
        from models.data_wali import DataWali

        db.create_all()

        create_default_admin()

    return app


# ==================================================
# Admin Default
# ==================================================
def create_default_admin():
    from models.user import User

    admin = User.query.filter_by(
        username='admin'
    ).first()

    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash(
                'admin123'
            ),
            role='admin'
        )

        db.session.add(admin)
        db.session.commit()

        print(
            "[INFO] Admin default berhasil dibuat"
        )


# ==================================================
# Run App
# ==================================================
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
