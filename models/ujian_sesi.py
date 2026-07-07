from datetime import datetime

from extensions_db import db


class UjianSesi(db.Model):
    __tablename__ = 'ujian_sesi'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(120), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    urutan = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_pada = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    soal = db.relationship(
        'Soal',
        backref='sesi',
        lazy=True,
        cascade='all, delete-orphan',
    )

    hasil_ujian = db.relationship(
        'HasilUjian',
        backref='sesi',
        lazy=True,
    )

    @property
    def jumlah_soal(self):
        return len(self.soal or [])

    def __repr__(self):
        return f'<UjianSesi {self.urutan}. {self.judul}>'
