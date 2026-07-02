from extensions_db import db


class AlamatSiswa(db.Model):
    __tablename__ = 'alamat_siswa'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        unique=True
    )

    alamat_jalan = db.Column(db.Text)

    dusun = db.Column(db.String(100))

    rt = db.Column(db.String(5))
    rw = db.Column(db.String(5))

    desa_kelurahan = db.Column(
        db.String(100)
    )

    kecamatan = db.Column(
        db.String(100)
    )

    kabupaten = db.Column(
        db.String(100)
    )

    kode_pos = db.Column(
        db.String(10)
    )
