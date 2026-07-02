from flask import Blueprint, render_template, request, flash, url_for, redirect, send_from_directory
from flask_login import login_required, current_user
from models.calon_siswa import CalonSiswa
from models.alamat_siswa import AlamatSiswa
from models.data_ayah import DataAyah
from models.data_ibu import DataIbu
from models.data_wali import DataWali
from extensions_db import db
from models.berkas import Berkas
from config import Config
from datetime import datetime

admin = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'
)


# ==================================================
# Dashboard Admin
# ==================================================
@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    total_pendaftar = CalonSiswa.query.count()

    data_diverifikasi = CalonSiswa.query.filter_by(
        status_verifikasi='Diverifikasi'
    ).count()

    berkas_diverifikasi = Berkas.query.filter_by(
        status_verifikasi='Diverifikasi'
    ).count()

    berkas_ditolak = Berkas.query.filter_by(
        status_verifikasi=Berkas.STATUS_DITOLAK
    ).count()

    menunggu_verifikasi = (
            total_pendaftar - data_diverifikasi
    )

    total_berkas_masuk = Berkas.query.count()

    periode_ppdb = "2026 / 2027"

    return render_template(
        'admin/dashboard.html',
        total_pendaftar=total_pendaftar,
        data_diverifikasi=data_diverifikasi,
        berkas_diverifikasi=berkas_diverifikasi,
        berkas_ditolak=berkas_ditolak,
        menunggu_verifikasi=menunggu_verifikasi,
        total_berkas_masuk=total_berkas_masuk,
        periode_ppdb=periode_ppdb
    )


# ==================================================
# Menampilkan seluruh data calon siswa / Read, URL :
# /admin/calon-siswa
# ==================================================
@admin.route('/calon-siswa')
@login_required
def calon_siswa():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    data_siswa = CalonSiswa.query.all()

    return render_template(
        'admin/calon_siswa.html',
        data_siswa=data_siswa
    )


# ==================================================
# DETAIL CALON SISWA / READ DETAIL, URL :
# /admin/calon-siswa/<id>
# ==================================================
@admin.route('/calon-siswa/<int:id>')
@login_required
def detail_siswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)

    return render_template(
        'admin/detail_siswa.html',
        siswa=siswa
    )


# ==================================================
# EDIT CALON SISWA / UPDATE
# URL : /admin/calon-siswa/edit/<id>
# ==================================================
@admin.route(
    '/calon-siswa/edit/<int:id>',
    methods=['GET', 'POST']
)
@login_required
def edit_siswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)

    if request.method == 'POST':

        # ==========================
        # DATA PRIBADI SISWA
        # ==========================

        siswa.nama_lengkap = request.form.get(
            'nama_lengkap'
        )

        siswa.nisn = request.form.get(
            'nisn'
        )

        siswa.nik = request.form.get(
            'nik'
        )

        siswa.no_registrasi_akta = request.form.get(
            'no_registrasi_akta'
        )

        siswa.tempat_lahir = request.form.get(
            'tempat_lahir'
        )

        if request.form.get('tanggal_lahir'):
            siswa.tanggal_lahir = datetime.strptime(
                request.form.get('tanggal_lahir'),
                '%Y-%m-%d'
            ).date()

        siswa.jenis_kelamin = request.form.get(
            'jenis_kelamin'
        )

        siswa.agama = request.form.get(
            'agama'
        )

        siswa.kewarganegaraan = request.form.get(
            'kewarganegaraan'
        )

        siswa.kebutuhan_khusus = request.form.get(
            'kebutuhan_khusus'
        )

        siswa.status_tinggal = request.form.get(
            'status_tinggal'
        )

        siswa.moda_transportasi = request.form.get(
            'moda_transportasi'
        )

        siswa.anak_ke = request.form.get(
            'anak_ke'
        ) or None

        siswa.tinggi_badan = request.form.get(
            'tinggi_badan'
        ) or None

        siswa.berat_badan = request.form.get(
            'berat_badan'
        ) or None

        siswa.jumlah_saudara_kandung = request.form.get(
            'jumlah_saudara_kandung'
        ) or None

        # ==========================
        # DATA KONTAK
        # ==========================

        siswa.no_hp = request.form.get(
            'no_hp'
        )

        siswa.email = request.form.get(
            'email'
        )

        # ==========================
        # DATA SEKOLAH ASAL
        # ==========================

        siswa.asal_sekolah = request.form.get(
            'asal_sekolah'
        )

        siswa.tahun_lulus = request.form.get(
            'tahun_lulus'
        )

        siswa.jarak_ke_sekolah = request.form.get(
            'jarak_ke_sekolah'
        )

        siswa.waktu_tempuh = request.form.get(
            'waktu_tempuh'
        )

        # ==========================
        # DATA ALAMAT
        # ==========================

        if not siswa.alamat:
            siswa.alamat = AlamatSiswa(
                calon_siswa_id=siswa.id
            )

        alamat = siswa.alamat

        alamat.alamat_jalan = request.form.get(
            'alamat_jalan'
        )

        alamat.dusun = request.form.get(
            'dusun'
        )

        alamat.rt = request.form.get(
            'rt'
        )

        alamat.rw = request.form.get(
            'rw'
        )

        alamat.desa_kelurahan = request.form.get(
            'desa_kelurahan'
        )

        alamat.kecamatan = request.form.get(
            'kecamatan'
        )

        alamat.kabupaten = request.form.get(
            'kabupaten'
        )

        alamat.kode_pos = request.form.get(
            'kode_pos'
        )

        # ==========================
        # DATA AYAH
        # ==========================

        if not siswa.ayah:
            siswa.ayah = DataAyah(
                calon_siswa_id=siswa.id
            )

        ayah = siswa.ayah

        ayah.nama = request.form.get(
            'ayah_nama'
        )

        ayah.nik = request.form.get(
            'ayah_nik'
        )

        ayah.tempat_lahir = request.form.get(
            'ayah_tempat_lahir'
        )

        if request.form.get('ayah_tanggal_lahir'):
            ayah.tanggal_lahir = datetime.strptime(
                request.form.get('ayah_tanggal_lahir'),
                '%Y-%m-%d'
            ).date()

        ayah.pendidikan = request.form.get(
            'ayah_pendidikan'
        )

        ayah.pekerjaan = request.form.get(
            'ayah_pekerjaan'
        )

        ayah.penghasilan = request.form.get(
            'ayah_penghasilan'
        )

        ayah.kebutuhan_khusus = request.form.get(
            'ayah_kebutuhan_khusus'
        )

        ayah.no_hp = request.form.get(
            'ayah_no_hp'
        )

        # ==========================
        # DATA IBU
        # ==========================

        if not siswa.ibu:
            siswa.ibu = DataIbu(
                calon_siswa_id=siswa.id
            )

        ibu = siswa.ibu

        ibu.nama = request.form.get(
            'ibu_nama'
        )

        ibu.nik = request.form.get(
            'ibu_nik'
        )

        ibu.tempat_lahir = request.form.get(
            'ibu_tempat_lahir'
        )

        if request.form.get('ibu_tanggal_lahir'):
            ibu.tanggal_lahir = datetime.strptime(
                request.form.get('ibu_tanggal_lahir'),
                '%Y-%m-%d'
            ).date()

        ibu.pendidikan = request.form.get(
            'ibu_pendidikan'
        )

        ibu.pekerjaan = request.form.get(
            'ibu_pekerjaan'
        )

        ibu.penghasilan = request.form.get(
            'ibu_penghasilan'
        )

        ibu.kebutuhan_khusus = request.form.get(
            'ibu_kebutuhan_khusus'
        )

        ibu.no_hp = request.form.get(
            'ibu_no_hp'
        )

        # ==========================
        # DATA WALI (OPSIONAL)
        # ==========================

        wali_nama = request.form.get('wali_nama')

        if wali_nama:

            if not siswa.wali:
                siswa.wali = DataWali(
                    calon_siswa_id=siswa.id
                )

            wali = siswa.wali

            wali.nama = wali_nama

            wali.nik = request.form.get(
                'wali_nik'
            )

            wali.tempat_lahir = request.form.get(
                'wali_tempat_lahir'
            )

            if request.form.get('wali_tanggal_lahir'):
                wali.tanggal_lahir = datetime.strptime(
                    request.form.get('wali_tanggal_lahir'),
                    '%Y-%m-%d'
                ).date()

            wali.pendidikan = request.form.get(
                'wali_pendidikan'
            )

            wali.pekerjaan = request.form.get(
                'wali_pekerjaan'
            )

            wali.penghasilan = request.form.get(
                'wali_penghasilan'
            )

            wali.kebutuhan_khusus = request.form.get(
                'wali_kebutuhan_khusus'
            )

            wali.no_hp = request.form.get(
                'wali_no_hp'
            )

        # ==========================
        # RESET STATUS VERIFIKASI
        #
        # Data berubah karena diedit manual oleh
        # admin, sehingga perlu dicek ulang dari awal
        # (baik status sebelumnya Ditolak ataupun
        # Diverifikasi).
        # ==========================

        siswa.status_verifikasi = 'Belum Diverifikasi'

        siswa.catatan_verifikasi = None

        siswa.tanggal_verifikasi = None

        db.session.commit()

        flash(
            'Data siswa berhasil diperbarui',
            'success'
        )

        return redirect(
            url_for(
                'admin.detail_siswa',
                id=siswa.id
            )
        )

    return render_template(
        'admin/edit_siswa.html',
        siswa=siswa
    )


# ==================================================
# HAPUS CALON SISWA, URL :
# /admin/calon-siswa/hapus/<id>
# ==================================================
@admin.route('/calon-siswa/hapus/<int:id>')
@login_required
def hapus_siswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)

    db.session.delete(siswa)

    db.session.commit()

    flash(
        'Data siswa berhasil dihapus',
        'success'
    )

    return redirect(
        url_for(
            'admin.calon_siswa'
        )
    )


# ======================================
# Verifikasi data Calon Siswa, URL :
# /admin/calon-siswa/verifikasi/<id>
# ======================================
@admin.route('/verifikasi/<int:id>')
@login_required
def verifikasi_siswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)

    siswa.status_verifikasi = 'Diverifikasi'

    # Bersihkan catatan penolakan sebelumnya (jika ada),
    # karena pendaftaran ini sekarang diterima.
    siswa.catatan_verifikasi = None

    siswa.tanggal_verifikasi = datetime.now()

    db.session.commit()

    flash(
        'Pendaftaran berhasil diverifikasi',
        'success'
    )

    return redirect(
        url_for(
            'admin.detail_siswa',
            id=id
        )
    )


# ======================================
# Tolak data Calon Siswa, URL :
# /admin/calon-siswa/tolak/<id>
#
# Catatan:
# Mengikuti pola yang sama dengan tolak_berkas.
# Alasan penolakan wajib diisi agar siswa tahu
# apa yang harus diperbaiki.
# ======================================
@admin.route(
    '/calon-siswa/tolak/<int:id>',
    methods=['POST']
)
@login_required
def tolak_siswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)

    catatan = request.form.get(
        'catatan_verifikasi'
    )

    if not catatan:
        flash(
            'Alasan penolakan wajib diisi',
            'danger'
        )

        return redirect(
            url_for(
                'admin.detail_siswa',
                id=id
            )
        )

    siswa.status_verifikasi = 'Ditolak'

    siswa.catatan_verifikasi = catatan

    siswa.tanggal_verifikasi = datetime.now()

    db.session.commit()

    flash(
        'Pendaftaran siswa ditolak',
        'warning'
    )

    return redirect(
        url_for(
            'admin.detail_siswa',
            id=id
        )
    )


# ==================================================
# MENAMPILKAN SELURUH DATA BERKAS SISWA / READ
# URL : /admin/berkas
# ==================================================
@admin.route('/berkas')
@login_required
def data_berkas():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    data_berkas = Berkas.query.all()

    return render_template(
        'admin/data_berkas.html',
        data_berkas=data_berkas
    )


# ==================================================
# DETAIL DATA BERKAS SISWA / READ DETAIL
# URL : /admin/berkas/<id>
# ==================================================
@admin.route('/berkas/<int:id>')
@login_required
def detail_berkas(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    berkas = Berkas.query.get_or_404(id)

    return render_template(
        'admin/detail_berkas.html',
        berkas=berkas
    )


# ==================================================
# VERIFIKASI BERKAS SISWA / diterima dan ditolak
# URL : /admin/verifikasi-berkas/<id>
# ==================================================
@admin.route('/verifikasi-berkas/<int:id>')
@login_required
def verifikasi_berkas(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    berkas = Berkas.query.get_or_404(id)
    berkas.status_verifikasi = Berkas.STATUS_DITERIMA
    berkas.field_bermasalah = None
    berkas.tanggal_verifikasi = datetime.now()

    db.session.commit()
    flash('Berkas diterima (diverifikasi)', 'success')
    return redirect(url_for('admin.data_berkas'))


# ==================================================
# TOLAK BERKAS SISWA
# URL : /admin/tolak-berkas/<id>
# ==================================================
@admin.route('/tolak-berkas/<int:id>', methods=['POST'])
@login_required
def tolak_berkas(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    berkas = Berkas.query.get_or_404(id)

    catatan = request.form.get('catatan_verifikasi')
    field_bermasalah = request.form.getlist('field_bermasalah')  # checkbox multiple

    if not catatan:
        flash('Alasan penolakan wajib diisi', 'danger')
        return redirect(url_for('admin.detail_berkas', id=id))

    if not field_bermasalah:
        flash('Pilih minimal satu dokumen yang bermasalah', 'danger')
        return redirect(url_for('admin.detail_berkas', id=id))

    berkas.status_verifikasi = Berkas.STATUS_DITOLAK
    berkas.catatan_verifikasi = catatan
    berkas.field_bermasalah = ','.join(field_bermasalah)
    berkas.tanggal_verifikasi = datetime.now()

    db.session.commit()
    flash('Berkas berhasil ditolak', 'warning')
    return redirect(url_for('admin.data_berkas'))


# ==================================================
# HAPUS DATA BERKAS / DELETE
# URL : /admin/hapus-berkas/<id>
#
# Fungsi :
# - Menghapus data berkas dari database
# - Tidak menghapus file fisik upload
#   (jika ingin menghapus file fisik perlu
#   ditambahkan os.remove())
# ==================================================
@admin.route('/hapus-berkas/<int:id>')
@login_required
def hapus_berkas(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    berkas = Berkas.query.get_or_404(id)

    db.session.delete(berkas)

    db.session.commit()

    flash(
        'Data berkas berhasil dihapus',
        'success'
    )

    return redirect(
        url_for('admin.data_berkas')
    )


# ==================================================
# MENAMPILKAN FILE UPLOAD BERKAS SISWA
# URL : /admin/uploads/<filename>
# ==================================================
@admin.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    return send_from_directory(
        Config.UPLOAD_FOLDER,
        filename
    )
