from datetime import datetime

from extensions_db import db


class UjianSesi(db.Model):
    __tablename__ = 'ujian_sesi'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(120), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    urutan = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True)
    durasi_menit = db.Column(db.Integer, nullable=False, default=60, server_default='60')
    jadwal_mulai = db.Column(db.DateTime, nullable=True)
    jadwal_selesai = db.Column(db.DateTime, nullable=True)
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

    @property
    def sudah_dijadwalkan(self):
        return bool(self.jadwal_mulai and self.jadwal_selesai)

    def status_jadwal(self, now=None):
        now = now or datetime.now()
        if not self.sudah_dijadwalkan:
            return 'belum_dijadwalkan'
        if now < self.jadwal_mulai:
            return 'belum_dibuka'
        if now <= self.jadwal_selesai:
            return 'dibuka'
        return 'ditutup'

    def is_terbuka(self, now=None):
        return self.aktif and self.status_jadwal(now) == 'dibuka'

    @property
    def jadwal_label(self):
        if not self.sudah_dijadwalkan:
            return 'Belum dijadwalkan'
        tanggal = self.jadwal_mulai.strftime('%d-%m-%Y')
        jam_mulai = self.jadwal_mulai.strftime('%H:%M')
        jam_selesai = self.jadwal_selesai.strftime('%H:%M')
        return f'{tanggal}, {jam_mulai} - {jam_selesai}'

    @property
    def durasi_label(self):
        menit = self.durasi_menit or 0
        jam = menit // 60
        sisa_menit = menit % 60

        if jam and sisa_menit:
            return f'{jam} jam {sisa_menit} menit'
        if jam:
            return f'{jam} jam'
        return f'{menit} menit'

    def __repr__(self):
        return f'<UjianSesi {self.urutan}. {self.judul}>'
