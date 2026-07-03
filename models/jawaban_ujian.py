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

    # Nilai: 'A', 'B', 'C', 'D', atau None jika tidak dijawab
    jawaban_dipilih = db.Column(
        db.String(1),
        nullable=True
    )

    benar = db.Column(
        db.Boolean,
        default=False
    )

    # ==========================
    # RELASI SOAL
    # ==========================

    soal = db.relationship(
        'Soal'
    )
