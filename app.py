from flask import Flask, flash, redirect, request, url_for
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import inspect, text

from config import Config
from extensions_db import db, login_manager, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Jangan tampilkan teks "None" di input/textarea template saat data opsional belum diisi.
    app.jinja_env.finalize = lambda value: '' if value is None else value

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'warning'

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        per_file_mb = (app.config.get('PER_FILE_UPLOAD_LIMIT') or 0) / (1024 * 1024)
        flash(
            f'Upload belum bisa diproses karena ukuran data melewati batas server. Pastikan setiap file maksimal {per_file_mb:.0f} MB dan formatnya sesuai, lalu upload ulang.',
            'danger'
        )
        return redirect(request.referrer or url_for('siswa.upload_berkas'))

    from routes.auth import auth
    from routes.admin import admin
    from routes.siswa import siswa

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(siswa)

    with app.app_context():
        from models.user import User
        from models.calon_siswa import CalonSiswa
        from models.berkas import Berkas
        from models.alamat_siswa import AlamatSiswa
        from models.data_ayah import DataAyah
        from models.data_ibu import DataIbu
        from models.data_wali import DataWali
        from models.ujian_sesi import UjianSesi
        from models.soal import Soal
        from models.hasil_ujian import HasilUjian
        from models.jawaban_ujian import JawabanUjian
        from models.pengaturan_ujian import PengaturanUjian

        db.create_all()
        ensure_sqlite_schema_updates()
        create_default_admin()

    return app


def _has_column(inspector, table_name, column_name):
    try:
        return column_name in [col['name'] for col in inspector.get_columns(table_name)]
    except Exception:
        return False


def ensure_sqlite_schema_updates():
    """Migrasi ringan untuk SQLite draft lama.

    db.create_all() tidak mengubah tabel lama. Fungsi ini hanya menambah kolom
    yang dibutuhkan patch baru agar project lama tidak langsung error saat
    dijalankan. Untuk production serius tetap gunakan Flask-Migrate.
    """
    engine = db.engine
    if engine.dialect.name != 'sqlite':
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        if 'ujian_sesi' in tables and not _has_column(inspector, 'ujian_sesi', 'durasi_menit'):
            conn.execute(text('ALTER TABLE ujian_sesi ADD COLUMN durasi_menit INTEGER DEFAULT 60'))
        if 'ujian_sesi' in tables and not _has_column(inspector, 'ujian_sesi', 'jadwal_mulai'):
            conn.execute(text('ALTER TABLE ujian_sesi ADD COLUMN jadwal_mulai DATETIME'))
        if 'ujian_sesi' in tables and not _has_column(inspector, 'ujian_sesi', 'jadwal_selesai'):
            conn.execute(text('ALTER TABLE ujian_sesi ADD COLUMN jadwal_selesai DATETIME'))
        if 'ujian_sesi' in tables:
            conn.execute(text('UPDATE ujian_sesi SET durasi_menit = 60 WHERE durasi_menit IS NULL OR durasi_menit <= 0'))

        if 'soal' in tables and not _has_column(inspector, 'soal', 'sesi_id'):
            conn.execute(text('ALTER TABLE soal ADD COLUMN sesi_id INTEGER'))
        if 'soal' in tables and not _has_column(inspector, 'soal', 'urutan'):
            conn.execute(text('ALTER TABLE soal ADD COLUMN urutan INTEGER DEFAULT 0'))
        if 'soal' in tables:
            soal_columns = {
                'tipe_soal': "TEXT DEFAULT 'pg'",
                'jumlah_pilihan': 'INTEGER DEFAULT 4',
                'gambar_pertanyaan': 'TEXT',
                'pilihan_e': 'TEXT',
                'gambar_pilihan_a': 'TEXT',
                'gambar_pilihan_b': 'TEXT',
                'gambar_pilihan_c': 'TEXT',
                'gambar_pilihan_d': 'TEXT',
                'gambar_pilihan_e': 'TEXT',
                'bobot': 'INTEGER DEFAULT 0',
            }
            for column_name, column_type in soal_columns.items():
                if not _has_column(inspector, 'soal', column_name):
                    conn.execute(text(f'ALTER TABLE soal ADD COLUMN {column_name} {column_type}'))
        if 'hasil_ujian' in tables and not _has_column(inspector, 'hasil_ujian', 'sesi_id'):
            conn.execute(text('ALTER TABLE hasil_ujian ADD COLUMN sesi_id INTEGER'))
        if 'hasil_ujian' in tables:
            hasil_columns = {
                'nilai_pg': 'REAL DEFAULT 0',
                'nilai_esai': 'REAL DEFAULT 0',
                'esai_dikoreksi': 'BOOLEAN DEFAULT 0',
            }
            for column_name, column_type in hasil_columns.items():
                if not _has_column(inspector, 'hasil_ujian', column_name):
                    conn.execute(text(f'ALTER TABLE hasil_ujian ADD COLUMN {column_name} {column_type}'))
        if 'jawaban_ujian' in tables and not _has_column(inspector, 'jawaban_ujian', 'skor_esai'):
            conn.execute(text('ALTER TABLE jawaban_ujian ADD COLUMN skor_esai REAL DEFAULT 0'))

    # Migrasi data ujian lama akademik/psikotes menjadi sesi dinamis.
    try:
        from models.ujian_sesi import UjianSesi
        from models.soal import Soal
        from models.hasil_ujian import HasilUjian

        if Soal.query.filter(Soal.sesi_id.is_(None)).first():
            sesi_akademik = UjianSesi.query.filter_by(judul='Sesi 1').first()
            if not sesi_akademik:
                sesi_akademik = UjianSesi(judul='Sesi 1', urutan=1, aktif=True)
                db.session.add(sesi_akademik)
                db.session.flush()

            sesi_psikotes = UjianSesi.query.filter_by(judul='Sesi 2').first()
            if not sesi_psikotes:
                sesi_psikotes = UjianSesi(judul='Sesi 2', urutan=2, aktif=True)
                db.session.add(sesi_psikotes)
                db.session.flush()

            for soal in Soal.query.filter(Soal.sesi_id.is_(None)).all():
                soal.sesi_id = sesi_psikotes.id if getattr(soal, 'jenis_ujian', None) == 'psikotes' else sesi_akademik.id

            for hasil in HasilUjian.query.filter(HasilUjian.sesi_id.is_(None)).all():
                hasil.sesi_id = sesi_psikotes.id if getattr(hasil, 'jenis_ujian', None) == 'psikotes' else sesi_akademik.id

            db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f'[WARN] Migrasi ringan sesi ujian dilewati: {exc}')


def create_default_admin():
    from models.user import User

    username = Config.DEFAULT_ADMIN_USERNAME
    password = Config.DEFAULT_ADMIN_PASSWORD

    if not username or not password:
        print('[INFO] ADMIN_USERNAME/ADMIN_PASSWORD belum diisi; admin default tidak dibuat otomatis.')
        return

    admin = User.query.filter_by(username=username).first()
    if admin:
        return

    admin = User(
        username=username,
        password=generate_password_hash(password),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print('[INFO] Admin default dari .env berhasil dibuat')


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=Config.DEBUG)
