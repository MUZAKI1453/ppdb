from extensions_db import db
from datetime import datetime


class Soal(db.Model):
    __tablename__ = 'soal'

    # Jenis ujian: soal Akademik (MTK, IPA, Indo, dll) atau
    # soal Psikotes. Keduanya disimpan di tabel yang sama,
    # dibedakan lewat kolom ini supaya siswa mengerjakan
    # dua sesi ujian yang terpisah.
    JENIS_AKADEMIK = 'akademik'
    JENIS_PSIKOTES = 'psikotes'

    JENIS_PILIHAN = [
        (JENIS_AKADEMIK, 'Akademik'),
        (JENIS_PSIKOTES, 'Psikotes'),
    ]

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # ISI SOAL
    # ==========================

    jenis_ujian = db.Column(
        db.String(20),
        nullable=False,
        default=JENIS_AKADEMIK,
        server_default=JENIS_AKADEMIK
    )

    pertanyaan = db.Column(
        db.Text,
        nullable=False
    )

    pilihan_a = db.Column(
        db.String(255),
        nullable=False
    )

    pilihan_b = db.Column(
        db.String(255),
        nullable=False
    )

    pilihan_c = db.Column(
        db.String(255),
        nullable=False
    )

    pilihan_d = db.Column(
        db.String(255),
        nullable=False
    )

    # Nilai: 'A', 'B', 'C', atau 'D'
    jawaban_benar = db.Column(
        db.String(1),
        nullable=False
    )

    kategori = db.Column(
        db.String(50),
        nullable=True
    )

    dibuat_pada = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ==========================
    # HELPER
    # ==========================
    def pilihan(self):
        # Dipakai di template biar gampang di-loop
        return {
            'A': self.pilihan_a,
            'B': self.pilihan_b,
            'C': self.pilihan_c,
            'D': self.pilihan_d,
        }
