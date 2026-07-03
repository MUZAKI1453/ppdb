from extensions_db import db


class DataWali(db.Model):
    __tablename__ = 'data_wali'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        unique=True
    )

    nama = db.Column(db.String(150))

    nik = db.Column(db.String(20))

    tempat_lahir = db.Column(
        db.String(100)
    )

    tanggal_lahir = db.Column(
        db.Date
    )

    pendidikan = db.Column(
        db.String(50)
    )

    pekerjaan = db.Column(
        db.String(100)
    )

    penghasilan = db.Column(
        db.String(50)
    )

    kebutuhan_khusus = db.Column(
        db.String(100)
    )

    no_hp = db.Column(
        db.String(20)
    )