from extensions_db import db


class CalonSiswa(db.Model):

    __tablename__ = 'calon_siswa'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        unique=True
    )

    # ==========================
    # DATA PRIBADI
    # ==========================

    nama_lengkap = db.Column(db.String(150))
    nisn = db.Column(db.String(20))
    nik = db.Column(db.String(20))

    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.Date)

    jenis_kelamin = db.Column(db.String(20))
    agama = db.Column(db.String(30))

    # ==========================
    # DATA KONTAK
    # ==========================

    alamat = db.Column(db.Text)

    no_hp = db.Column(db.String(20))
    email = db.Column(db.String(100))

    # ==========================
    # DATA ORANG TUA
    # ==========================

    nama_ayah = db.Column(db.String(150))
    pekerjaan_ayah = db.Column(db.String(100))

    nama_ibu = db.Column(db.String(150))
    pekerjaan_ibu = db.Column(db.String(100))

    no_hp_ortu = db.Column(db.String(20))

    # ==========================
    # DATA SEKOLAH
    # ==========================

    asal_sekolah = db.Column(db.String(150))
    tahun_lulus = db.Column(db.String(10))

    # ==========================
    # STATUS PPDB
    # ==========================

    status_verifikasi = db.Column(
        db.String(30),
        default='Belum Diverifikasi'
    )

    status_kelulusan = db.Column(
        db.String(30),
        default='Menunggu'
    )

    # ==========================
    # RELASI BERKAS KE CALON SISWA
    # ==========================

    berkas = db.relationship(
        'Berkas',
        backref='calon_siswa',
        uselist=False
    )