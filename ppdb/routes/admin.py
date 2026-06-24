from flask import Blueprint, render_template, request, flash, url_for, redirect, send_from_directory
from flask_login import login_required, current_user
from models.calon_siswa import CalonSiswa
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
        # DATA PRIBADI
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

        siswa.jenis_kelamin = request.form.get(
            'jenis_kelamin'
        )

        siswa.tempat_lahir = request.form.get(
            'tempat_lahir'
        )

        siswa.agama = request.form.get(
            'agama'
        )

        if request.form.get('tanggal_lahir'):
            siswa.tanggal_lahir = datetime.strptime(
                request.form.get(
                    'tanggal_lahir'
                ),
                '%Y-%m-%d'
            ).date()

        # ==========================
        # DATA KONTAK
        # ==========================
        siswa.alamat = request.form.get(
            'alamat'
        )

        siswa.no_hp = request.form.get(
            'no_hp'
        )

        siswa.email = request.form.get(
            'email'
        )

        # ==========================
        # DATA ORANG TUA
        # ==========================
        siswa.nama_ayah = request.form.get(
            'nama_ayah'
        )

        siswa.nama_ibu = request.form.get(
            'nama_ibu'
        )

        siswa.pekerjaan_ayah = request.form.get(
            'pekerjaan_ayah'
        )

        siswa.pekerjaan_ibu = request.form.get(
            'pekerjaan_ibu'
        )

        siswa.no_hp_ortu = request.form.get(
            'no_hp_ortu'
        )

        # ==========================
        # DATA SEKOLAH
        # ==========================
        siswa.asal_sekolah = request.form.get(
            'asal_sekolah'
        )

        siswa.tahun_lulus = request.form.get(
            'tahun_lulus'
        )

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
                'admin.detail_berkas',
                id=id
            )
        )

    berkas.status_verifikasi = Berkas.STATUS_DITOLAK

    berkas.catatan_verifikasi = catatan

    berkas.tanggal_verifikasi = datetime.now()

    db.session.commit()

    flash(
        'Berkas berhasil ditolak',
        'warning'
    )

    return redirect(
        url_for(
            'admin.data_berkas'
        )
    )


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
