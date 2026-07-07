from datetime import datetime

from extensions_db import db


class PengaturanUjian(db.Model):
    __tablename__ = 'pengaturan_ujian'

    id = db.Column(db.Integer, primary_key=True)
    jadwal_mulai = db.Column(db.DateTime, nullable=True)
    jadwal_selesai = db.Column(db.DateTime, nullable=True)
    panduan = db.Column(db.Text, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_pada = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    @classmethod
    def get_or_create(cls):
        pengaturan = cls.query.get(1)
        if not pengaturan:
            pengaturan = cls(
                id=1,
                panduan=(
                    'Pastikan koneksi internet stabil, gunakan perangkat yang siap, '
                    'kerjakan sesi ujian secara berurutan, dan jangan keluar dari mode ujian aman.'
                ),
            )
            db.session.add(pengaturan)
            db.session.commit()
        return pengaturan

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
        return self.status_jadwal(now) == 'dibuka'

    @property
    def jadwal_label(self):
        if not self.sudah_dijadwalkan:
            return 'Belum dijadwalkan'
        tanggal = self.jadwal_mulai.strftime('%d-%m-%Y')
        jam_mulai = self.jadwal_mulai.strftime('%H:%M')
        jam_selesai = self.jadwal_selesai.strftime('%H:%M')
        return f'{tanggal}, {jam_mulai} - {jam_selesai} WIB'
