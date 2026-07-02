from extensions_db import db
from datetime import datetime


class Berkas(db.Model):
    __tablename__ = 'berkas'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    calon_siswa_id = db.Column(
        db.Integer,
        db.ForeignKey('calon_siswa.id'),
        nullable=False
    )

    # field bermasalah
    field_bermasalah = db.Column(
        db.String(255),
        nullable=True
    )

    # ==========================
    # FILE UPLOAD
    # ==========================
    pas_foto = db.Column(db.String(255))
    kartu_keluarga = db.Column(db.String(255))
    akta_lahir = db.Column(db.String(255))
    ijazah = db.Column(db.String(255))
    ktp_orang_tua = db.Column(db.String(255))

    # ==========================
    # STATUS VERIFIKASI
    # ==========================
    STATUS_BELUM = "Belum Diverifikasi"
    STATUS_REVISI = "Revisi"
    STATUS_DITOLAK = "Ditolak"
    STATUS_DITERIMA = "Diverifikasi"

    status_verifikasi = db.Column(
        db.String(30),
        default=STATUS_BELUM
    )

    catatan_verifikasi = db.Column(
        db.Text,
        nullable=True
    )

    tanggal_verifikasi = db.Column(
        db.DateTime,
        nullable=True
    )

    tanggal_upload = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ==========================
    # HELPER (BIAR AMAN DI TEMPLATE)
    # ==========================
    def is_diverifikasi(self):
        return self.status_verifikasi == self.STATUS_DITERIMA

    def is_ditolak(self):
        return self.status_verifikasi == self.STATUS_DITOLAK

    def is_revisi(self):
        return self.status_verifikasi == self.STATUS_REVISI

    def is_pending(self):
        return self.status_verifikasi == self.STATUS_BELUM

    @property
    def list_field_bermasalah(self):
        if not self.field_bermasalah:
            return []
        return self.field_bermasalah.split(',')