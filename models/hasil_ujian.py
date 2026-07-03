from extensions_db import db
from datetime import datetime


class HasilUjian(db.Model):
    __tablename__ = 'hasil_ujian'

    # Satu siswa sekarang bisa punya 2 baris hasil ujian:
    # satu untuk 'akademik' dan satu untuk 'psikotes'.
    # Kombinasi (calon_siswa_id, jenis_ujian) dibuat unik
    # lewat __table_args__ di bawah, menggantikan
    # unique=True yang lama di calon_siswa_id.
    __table_args__ = (
        db.UniqueConstraint(
            'calon_siswa_id', 'jenis_ujian',
            name='uq_hasil_ujian_siswa_jenis'
        ),
    )

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

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        nullable=False
    )

    jenis_ujian = db.Column(
        db.String(20),
        nullable=False,
        default=JENIS_AKADEMIK,
        server_default=JENIS_AKADEMIK
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

    def label_jenis(self):
        return dict(self.JENIS_PILIHAN).get(self.jenis_ujian, self.jenis_ujian)
