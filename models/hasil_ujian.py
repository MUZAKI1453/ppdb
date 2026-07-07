from extensions_db import db
from datetime import datetime


class HasilUjian(db.Model):
    __tablename__ = 'hasil_ujian'

    __table_args__ = (
        db.UniqueConstraint(
            'calon_siswa_id', 'sesi_id',
            name='uq_hasil_ujian_siswa_sesi'
        ),
    )

    # Kolom/konstanta lama dipertahankan untuk kompatibilitas data lama.
    JENIS_AKADEMIK = 'akademik'
    JENIS_PSIKOTES = 'psikotes'
    JENIS_PILIHAN = [
        (JENIS_AKADEMIK, 'Sesi 1'),
        (JENIS_PSIKOTES, 'Sesi 2'),
    ]

    id = db.Column(db.Integer, primary_key=True)

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        nullable=False
    )

    sesi_id = db.Column(
        db.Integer,
        db.ForeignKey('ujian_sesi.id'),
        nullable=True
    )

    jenis_ujian = db.Column(
        db.String(20),
        nullable=False,
        default=JENIS_AKADEMIK,
        server_default=JENIS_AKADEMIK
    )

    STATUS_BELUM = 'Belum Mengerjakan'
    STATUS_SELESAI = 'Selesai'

    status = db.Column(db.String(30), default=STATUS_BELUM)
    jumlah_soal = db.Column(db.Integer, default=0)
    jumlah_benar = db.Column(db.Integer, default=0)
    nilai = db.Column(db.Float, default=0)
    waktu_mulai = db.Column(db.DateTime, nullable=True)
    waktu_selesai = db.Column(db.DateTime, nullable=True)

    jawaban = db.relationship(
        'JawabanUjian',
        backref='hasil_ujian',
        cascade='all, delete-orphan'
    )

    def is_selesai(self):
        return self.status == self.STATUS_SELESAI

    def label_sesi(self):
        if self.sesi:
            return self.sesi.judul
        return dict(self.JENIS_PILIHAN).get(self.jenis_ujian, self.jenis_ujian)

    def label_jenis(self):
        return self.label_sesi()
