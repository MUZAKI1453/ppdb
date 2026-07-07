from extensions_db import db
from datetime import datetime


class Soal(db.Model):
    __tablename__ = 'soal'

    # Konstanta lama dipertahankan untuk kompatibilitas database lama.
    JENIS_AKADEMIK = 'akademik'
    JENIS_PSIKOTES = 'psikotes'
    JENIS_PILIHAN = [
        (JENIS_AKADEMIK, 'Sesi 1'),
        (JENIS_PSIKOTES, 'Sesi 2'),
    ]

    TIPE_PG = 'pg'
    TIPE_ESAI = 'esai'

    id = db.Column(db.Integer, primary_key=True)

    sesi_id = db.Column(
        db.Integer,
        db.ForeignKey('ujian_sesi.id'),
        nullable=True
    )

    # Kolom lama tidak dipakai di UI baru, tetapi dibiarkan agar data lama tidak rusak.
    jenis_ujian = db.Column(
        db.String(20),
        nullable=False,
        default=JENIS_AKADEMIK,
        server_default=JENIS_AKADEMIK
    )

    tipe_soal = db.Column(db.String(20), nullable=False, default=TIPE_PG, server_default=TIPE_PG)
    jumlah_pilihan = db.Column(db.Integer, nullable=False, default=4, server_default='4')

    pertanyaan = db.Column(db.Text, nullable=False)
    gambar_pertanyaan = db.Column(db.String(255), nullable=True)

    pilihan_a = db.Column(db.Text, nullable=True)
    pilihan_b = db.Column(db.Text, nullable=True)
    pilihan_c = db.Column(db.Text, nullable=True)
    pilihan_d = db.Column(db.Text, nullable=True)
    pilihan_e = db.Column(db.Text, nullable=True)

    gambar_pilihan_a = db.Column(db.String(255), nullable=True)
    gambar_pilihan_b = db.Column(db.String(255), nullable=True)
    gambar_pilihan_c = db.Column(db.String(255), nullable=True)
    gambar_pilihan_d = db.Column(db.String(255), nullable=True)
    gambar_pilihan_e = db.Column(db.String(255), nullable=True)

    jawaban_benar = db.Column(db.String(1), nullable=True)
    bobot = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    kategori = db.Column(db.String(50), nullable=True)
    urutan = db.Column(db.Integer, default=0)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    def is_pilihan_ganda(self):
        return (self.tipe_soal or self.TIPE_PG) == self.TIPE_PG

    def is_esai(self):
        return (self.tipe_soal or self.TIPE_PG) == self.TIPE_ESAI

    def pilihan(self):
        data = {
            'A': self.pilihan_a,
            'B': self.pilihan_b,
            'C': self.pilihan_c,
            'D': self.pilihan_d,
        }
        if (self.jumlah_pilihan or 4) >= 5 or self.pilihan_e or self.gambar_pilihan_e:
            data['E'] = self.pilihan_e
        return data

    def gambar_pilihan(self, huruf):
        return getattr(self, f'gambar_pilihan_{huruf.lower()}', None)
