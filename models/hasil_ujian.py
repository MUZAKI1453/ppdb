from extensions_db import db
from datetime import datetime


class HasilUjian(db.Model):
    __tablename__ = 'hasil_ujian'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        unique=True,
        nullable=False
    )

    # ==========================
    # STATUS UJIAN
    # ==========================
    STATUS_BELUM = "Belum Mengerjakan"
    STATUS_SELESAI = "Selesai"

    status = db.Column(
        db.String(30),
        default=STATUS_BELUM
    )

    jumlah_soal = db.Column(
        db.Integer,
        default=0
    )

    jumlah_benar = db.Column(
        db.Integer,
        default=0
    )

    nilai = db.Column(
        db.Float,
        default=0
    )

    waktu_mulai = db.Column(
        db.DateTime,
        nullable=True
    )

    waktu_selesai = db.Column(
        db.DateTime,
        nullable=True
    )

    # ==========================
    # RELASI JAWABAN
    # ==========================

    jawaban = db.relationship(
        'JawabanUjian',
        backref='hasil_ujian',
        cascade='all, delete-orphan'
    )

    # ==========================
    # HELPER
    # ==========================
    def is_selesai(self):
        return self.status == self.STATUS_SELESAI
