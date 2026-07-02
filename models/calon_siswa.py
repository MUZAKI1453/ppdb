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
    # DATA PRIBADI SISWA
    # ==========================

    nama_lengkap = db.Column(
        db.String(150)
    )

    nisn = db.Column(
        db.String(20)
    )

    nik = db.Column(
        db.String(20)
    )

    no_registrasi_akta = db.Column(
        db.String(50)
    )

    tempat_lahir = db.Column(
        db.String(100)
    )

    tanggal_lahir = db.Column(
        db.Date
    )

    jenis_kelamin = db.Column(
        db.String(20)
    )

    agama = db.Column(
        db.String(30)
    )

    kewarganegaraan = db.Column(
        db.String(30)
    )

    kebutuhan_khusus = db.Column(
        db.String(100)
    )

    status_tinggal = db.Column(
        db.String(50)
    )

    moda_transportasi = db.Column(
        db.String(50)
    )

    anak_ke = db.Column(
        db.Integer
    )

    tinggi_badan = db.Column(
        db.Integer
    )

    berat_badan = db.Column(
        db.Integer
    )

    jarak_ke_sekolah = db.Column(
        db.String(50)
    )

    waktu_tempuh = db.Column(
        db.String(50)
    )

    jumlah_saudara_kandung = db.Column(
        db.Integer
    )

    # ==========================
    # DATA KONTAK
    # ==========================

    no_hp = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(100)
    )

    # ==========================
    # DATA SEKOLAH ASAL
    # ==========================

    asal_sekolah = db.Column(
        db.String(150)
    )

    tahun_lulus = db.Column(
        db.String(10)
    )

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

    # Catatan alasan saat admin menolak pendaftaran.
    # Diisi ulang ke None setiap kali siswa mengisi
    # ulang data (mengikuti pola reset pada Berkas).
    catatan_verifikasi = db.Column(
        db.Text
    )

    # Waktu admin melakukan aksi verifikasi/tolak
    # terakhir kali, untuk keperluan audit/log.
    tanggal_verifikasi = db.Column(
        db.DateTime
    )

    # ==========================
    # RELASI BERKAS
    # ==========================

    berkas = db.relationship(
        'Berkas',
        backref='calon_siswa',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # ==========================
    # RELASI ALAMAT
    # ==========================

    alamat = db.relationship(
        'AlamatSiswa',
        backref='calon_siswa',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # ==========================
    # RELASI AYAH
    # ==========================

    ayah = db.relationship(
        'DataAyah',
        backref='calon_siswa',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # ==========================
    # RELASI IBU
    # ==========================

    ibu = db.relationship(
        'DataIbu',
        backref='calon_siswa',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # ==========================
    # RELASI WALI
    # ==========================

    wali = db.relationship(
        'DataWali',
        backref='calon_siswa',
        uselist=False,
        cascade='all, delete-orphan'
    )