from extensions_db import db


class JawabanUjian(db.Model):
    __tablename__ = 'jawaban_ujian'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    hasil_ujian_id = db.Column(
        db.Integer,
        db.ForeignKey('hasil_ujian.id'),
        nullable=False
    )

    soal_id = db.Column(
        db.Integer,
        db.ForeignKey('soal.id'),
        nullable=False
    )

    # Untuk PG berisi 'A', 'B', 'C', 'D', atau 'E'.
    # Untuk esai berisi teks jawaban siswa.
    jawaban_dipilih = db.Column(
        db.Text,
        nullable=True
    )

    benar = db.Column(
        db.Boolean,
        default=False
    )

    skor_esai = db.Column(
        db.Float,
        default=0,
        server_default='0'
    )

    # ==========================
    # RELASI SOAL
    # ==========================

    soal = db.relationship(
        'Soal'
    )
