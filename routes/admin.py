from flask import Blueprint, render_template, request, flash, url_for, redirect, send_from_directory, current_app, session, make_response
from flask_login import login_required, current_user
from models.calon_siswa import CalonSiswa
from models.alamat_siswa import AlamatSiswa
from models.data_ayah import DataAyah
from models.data_ibu import DataIbu
from models.data_wali import DataWali
from extensions_db import db
from models.berkas import Berkas
from models.soal import Soal
from models.ujian_sesi import UjianSesi
from models.pengaturan_ujian import PengaturanUjian
from models.hasil_ujian import HasilUjian
from models.user import User
from datetime import datetime
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename
from utils.soal_pdf_template_parser import parse_soal_pdf
from utils.upload_helper import IMAGE_EXTENSIONS, is_image, is_pdf, delete_uploaded_file, save_secure_upload
import os
import uuid

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

    total_diterima = CalonSiswa.query.filter_by(
        status_kelulusan='Diterima'
    ).count()

    periode_spmb = "2026 / 2027"

    return render_template(
        'admin/dashboard.html',
        total_pendaftar=total_pendaftar,
        data_diverifikasi=data_diverifikasi,
        berkas_diverifikasi=berkas_diverifikasi,
        berkas_ditolak=berkas_ditolak,
        menunggu_verifikasi=menunggu_verifikasi,
        total_berkas_masuk=total_berkas_masuk,
        total_diterima=total_diterima,
        periode_spmb=periode_spmb
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

        elif siswa.wali:
            db.session.delete(siswa.wali)
            siswa.wali = None

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

        if siswa.user and siswa.nisn:
            existing_user = User.query.filter(
                User.username == siswa.nisn,
                User.id != siswa.user.id
            ).first()
            if existing_user:
                flash('NISN sudah dipakai akun lain. Perubahan dibatalkan.', 'danger')
                db.session.rollback()
                return redirect(url_for('admin.edit_siswa', id=siswa.id))
            siswa.user.username = siswa.nisn

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
@admin.route('/calon-siswa/hapus/<int:id>', methods=['POST'])
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
@admin.route('/verifikasi/<int:id>', methods=['POST'])
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
        berkas=berkas,
        is_image=is_image,
        is_pdf=is_pdf
    )


# ==================================================
# VERIFIKASI BERKAS SISWA / diterima dan ditolak
# URL : /admin/verifikasi-berkas/<id>
# ==================================================
@admin.route('/verifikasi-berkas/<int:id>', methods=['POST'])
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
@admin.route('/hapus-berkas/<int:id>', methods=['POST'])
@login_required
def hapus_berkas(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    berkas = Berkas.query.get_or_404(id)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    for filename in [
        berkas.pas_foto,
        berkas.kartu_keluarga,
        berkas.akta_lahir,
        berkas.ijazah,
        berkas.ktp_orang_tua,
    ]:
        delete_uploaded_file(upload_folder, filename)

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
        current_app.config['UPLOAD_FOLDER'],
        filename
    )



# ==================================================
# BANK SOAL / SESI UJIAN DINAMIS
# ==================================================
def _require_admin():
    if current_user.role != 'admin':
        return False
    return True


def _get_sesi_aktif_dari_request():
    sesi_id = request.args.get('sesi_id', type=int)
    sesi_list = UjianSesi.query.order_by(UjianSesi.urutan, UjianSesi.id).all()
    sesi_aktif = None

    if sesi_id:
        sesi_aktif = UjianSesi.query.get(sesi_id)

    if not sesi_aktif and sesi_list:
        sesi_aktif = sesi_list[0]

    return sesi_list, sesi_aktif



def _ambil_durasi_menit(form, default=60):
    try:
        durasi = int(form.get('durasi_menit') or default)
    except (TypeError, ValueError):
        durasi = default

    if durasi < 1:
        durasi = default
    return min(durasi, 480)


def _ambil_datetime_local(form, field_name):
    raw = (form.get(field_name) or '').strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%dT%H:%M')
    except ValueError:
        return None


def _format_datetime_local(value):
    return value.strftime('%Y-%m-%dT%H:%M') if value else ''


@admin.route('/bank-soal/template-soal')
@login_required
def unduh_template_soal():
    if not _require_admin():
        return "Akses Ditolak", 403

    isi_template = """TEMPLATE IMPORT SOAL SPMB

1. Contoh pertanyaan pilihan ganda dengan empat pilihan.
A. Pilihan jawaban A
B. Pilihan jawaban B
C. Pilihan jawaban C
D. Pilihan jawaban D
Jawaban: A

2. Contoh pertanyaan pilihan ganda dengan lima pilihan.
A. Pilihan jawaban A
B. Pilihan jawaban B
C. Pilihan jawaban C
D. Pilihan jawaban D
E. Pilihan jawaban E
Jawaban: C

3. Contoh pertanyaan essay.
Bobot: 20
"""
    response = make_response(isi_template)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=template_import_soal_spmb.txt'
    return response

@admin.route('/bank-soal')
@login_required
def bank_soal():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_list, sesi_aktif = _get_sesi_aktif_dari_request()
    pengaturan_ujian = PengaturanUjian.get_or_create()
    daftar_soal = []
    if sesi_aktif:
        daftar_soal = Soal.query.filter_by(
            sesi_id=sesi_aktif.id
        ).order_by(Soal.urutan, Soal.id).all()

    return render_template(
        'admin/bank_soal.html',
        sesi_list=sesi_list,
        sesi_aktif=sesi_aktif,
        daftar_soal=daftar_soal,
        pengaturan_ujian=pengaturan_ujian,
        edit_id=request.args.get('edit_id', type=int),
        opsi_huruf=['A', 'B', 'C', 'D', 'E'],
        format_datetime_local=_format_datetime_local,
        now=datetime.utcnow(),
    )


@admin.route('/bank-soal/uploads/soal/<path:filename>')
@login_required
def uploaded_soal_file(filename):
    if not _require_admin():
        return "Akses Ditolak", 403

    soal_terkait = Soal.query.filter(or_(
        Soal.gambar_pertanyaan == filename,
        Soal.gambar_pilihan_a == filename,
        Soal.gambar_pilihan_b == filename,
        Soal.gambar_pilihan_c == filename,
        Soal.gambar_pilihan_d == filename,
        Soal.gambar_pilihan_e == filename,
    )).first()

    if not soal_terkait:
        return 'File tidak ditemukan', 404

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@admin.route('/bank-soal/sesi/<int:sesi_id>/preview')
@login_required
def preview_soal_sesi(sesi_id):
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi = UjianSesi.query.get_or_404(sesi_id)
    daftar_soal = Soal.query.filter_by(
        sesi_id=sesi.id
    ).order_by(Soal.urutan, Soal.id).all()

    return redirect(url_for('admin.bank_soal', sesi_id=sesi.id, edit_id=request.args.get('edit_id', type=int)))


@admin.route('/bank-soal/jadwal/update', methods=['POST'])
@login_required
def update_jadwal_ujian_global():
    if not _require_admin():
        return "Akses Ditolak", 403

    pengaturan = PengaturanUjian.get_or_create()
    sesi_id = request.form.get('sesi_id', type=int)
    redirect_target = url_for('admin.bank_soal', sesi_id=sesi_id) if sesi_id else url_for('admin.bank_soal')
    jadwal_mulai = _ambil_datetime_local(request.form, 'jadwal_mulai')
    jadwal_selesai = _ambil_datetime_local(request.form, 'jadwal_selesai')
    if not jadwal_mulai or not jadwal_selesai:
        flash('Jadwal mulai dan selesai ujian wajib diisi.', 'danger')
        return redirect(redirect_target)

    if jadwal_selesai <= jadwal_mulai:
        flash('Jadwal selesai harus lebih besar dari jadwal mulai.', 'danger')
        return redirect(redirect_target)

    pengaturan.jadwal_mulai = jadwal_mulai
    pengaturan.jadwal_selesai = jadwal_selesai
    db.session.commit()

    flash('Jadwal global ujian SPMB berhasil disimpan.', 'success')
    return redirect(redirect_target)


@admin.route('/bank-soal/sesi/tambah', methods=['POST'])
@login_required
def tambah_sesi_ujian():
    if not _require_admin():
        return "Akses Ditolak", 403

    judul = (request.form.get('judul') or '').strip()
    deskripsi = (request.form.get('deskripsi') or '').strip() or None
    durasi_menit = _ambil_durasi_menit(request.form)

    if not judul:
        flash('Judul sesi ujian wajib diisi.', 'danger')
        return redirect(url_for('admin.bank_soal'))

    max_urutan = db.session.query(func.max(UjianSesi.urutan)).scalar() or 0
    sesi = UjianSesi(
        judul=judul,
        deskripsi=deskripsi,
        durasi_menit=durasi_menit,
        urutan=max_urutan + 1,
        aktif=True,
    )
    db.session.add(sesi)
    db.session.commit()

    file = request.files.get('file_pdf')
    if file and file.filename:
        if not file.filename.lower().endswith('.pdf'):
            flash('Sesi berhasil dibuat, tetapi file import harus berformat PDF.', 'warning')
            return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

        temp_folder = os.path.join(current_app.instance_path, 'tmp')
        os.makedirs(temp_folder, exist_ok=True)
        nama_file_sementara = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        path_sementara = os.path.join(temp_folder, nama_file_sementara)
        file.save(path_sementara)

        try:
            daftar_soal_parsed, errors = parse_soal_pdf(path_sementara)
        except Exception as e:
            flash(f'Sesi berhasil dibuat, tetapi PDF gagal dibaca: {e}', 'warning')
            return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))
        finally:
            if os.path.exists(path_sementara):
                os.remove(path_sementara)

        if errors:
            pesan_error = 'Sebagian soal dilewati karena tidak sesuai format: ' + '; '.join(errors[:10])
            if len(errors) > 10:
                pesan_error += f' (dan {len(errors) - 10} lainnya)'
            flash(pesan_error, 'warning')

        if not daftar_soal_parsed:
            flash('Sesi berhasil dibuat, tetapi tidak ada soal yang terdeteksi di PDF.', 'warning')
            return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

        tersimpan, gagal = _simpan_soal_pdf_ke_sesi(sesi, daftar_soal_parsed)
        if gagal:
            pesan_gagal = 'Sebagian soal belum tersimpan: ' + '; '.join(gagal[:10])
            if len(gagal) > 10:
                pesan_gagal += f' (dan {len(gagal) - 10} lainnya)'
            flash(pesan_gagal, 'warning')

        if tersimpan:
            flash(f'Sesi berhasil dibuat. {tersimpan} soal berhasil masuk ke bank soal.', 'success')
        else:
            flash('Sesi berhasil dibuat, tetapi belum ada soal PDF yang valid untuk disimpan.', 'warning')
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    flash('Sesi ujian berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))


@admin.route('/bank-soal/sesi/<int:id>/update', methods=['POST'])
@login_required
def update_sesi_ujian(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi = UjianSesi.query.get_or_404(id)
    judul = (request.form.get('judul') or '').strip()
    deskripsi = (request.form.get('deskripsi') or '').strip() or None

    if not judul:
        flash('Judul sesi ujian wajib diisi.', 'danger')
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    sesi.judul = judul
    sesi.deskripsi = deskripsi
    sesi.durasi_menit = _ambil_durasi_menit(request.form, default=sesi.durasi_menit or 60)
    db.session.commit()

    flash('Pengaturan sesi ujian berhasil disimpan.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))


@admin.route('/bank-soal/sesi/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_sesi_ujian(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi = UjianSesi.query.get_or_404(id)
    sesi.aktif = not sesi.aktif
    db.session.commit()
    flash('Status sesi ujian berhasil diperbarui.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))


@admin.route('/bank-soal/sesi/<int:id>/hapus', methods=['POST'])
@login_required
def hapus_sesi_ujian(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi = UjianSesi.query.get_or_404(id)
    if sesi.hasil_ujian:
        flash('Sesi tidak dapat dihapus karena sudah memiliki hasil ujian calon siswa.', 'danger')
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    db.session.delete(sesi)
    db.session.commit()
    flash('Sesi ujian berhasil dihapus.', 'success')
    return redirect(url_for('admin.bank_soal'))


def _pilihan_form_name(huruf):
    return f'pilihan_{huruf.lower()}'


def _gambar_pilihan_attr(huruf):
    return f'gambar_pilihan_{huruf.lower()}'


def _save_optional_soal_image(field_name, prefix, old_filename=None, enabled=False):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_storage = request.files.get(field_name)

    if not enabled:
        if old_filename:
            delete_uploaded_file(upload_folder, old_filename)
        return None

    if file_storage and file_storage.filename:
        if old_filename:
            delete_uploaded_file(upload_folder, old_filename)
        return save_secure_upload(
            file_storage,
            upload_folder,
            prefix,
            IMAGE_EXTENSIONS,
            current_app.config.get('PER_FILE_UPLOAD_LIMIT')
        )

    return old_filename


def _ambil_data_soal_dari_form(form, soal_lama=None):
    tipe_soal = (form.get('tipe_soal') or Soal.TIPE_PG).strip().lower()
    if tipe_soal not in [Soal.TIPE_PG, Soal.TIPE_ESAI]:
        tipe_soal = Soal.TIPE_PG

    try:
        jumlah_pilihan = int(form.get('jumlah_pilihan') or 4)
    except (TypeError, ValueError):
        jumlah_pilihan = 4
    jumlah_pilihan = 5 if jumlah_pilihan == 5 else 4

    data = {
        'tipe_soal': tipe_soal,
        'jumlah_pilihan': jumlah_pilihan,
        'pertanyaan': (form.get('pertanyaan') or '').strip(),
        'jawaban_benar': (form.get('jawaban_benar') or '').strip().upper(),
        'bobot': int(form.get('bobot') or 0),
    }

    for huruf in ['A', 'B', 'C', 'D', 'E']:
        data[_pilihan_form_name(huruf)] = (form.get(_pilihan_form_name(huruf)) or '').strip()

    if tipe_soal == Soal.TIPE_ESAI:
        data['jumlah_pilihan'] = 0
        data['jawaban_benar'] = ''
        for huruf in ['A', 'B', 'C', 'D', 'E']:
            data[_pilihan_form_name(huruf)] = ''

    try:
        data['gambar_pertanyaan'] = _save_optional_soal_image(
            'gambar_pertanyaan',
            'soal_pertanyaan',
            getattr(soal_lama, 'gambar_pertanyaan', None) if soal_lama else None,
            enabled=form.get('gunakan_gambar_pertanyaan') == '1',
        )
        for huruf in ['A', 'B', 'C', 'D', 'E']:
            attr = _gambar_pilihan_attr(huruf)
            data[attr] = _save_optional_soal_image(
                attr,
                f'soal_opsi_{huruf.lower()}',
                getattr(soal_lama, attr, None) if soal_lama else None,
                enabled=form.get(f'gunakan_{attr}') == '1',
            )
    except ValueError as exc:
        data['_upload_error'] = str(exc)

    return data


def _validasi_data_soal(data):
    if data.get('_upload_error'):
        return data['_upload_error']

    if not data['pertanyaan']:
        return 'Pertanyaan soal wajib diisi.'

    if data['tipe_soal'] == Soal.TIPE_ESAI:
        if data.get('bobot', 0) < 0:
            return 'Bobot esai tidak valid.'
        return None

    wajib = ['A', 'B', 'C', 'D']
    if data.get('jumlah_pilihan') == 5:
        wajib.append('E')

    for huruf in wajib:
        teks = data.get(_pilihan_form_name(huruf))
        gambar = data.get(_gambar_pilihan_attr(huruf))
        if not teks and not gambar:
            return f'Pilihan {huruf} wajib diisi dengan teks atau gambar.'

    if data['jawaban_benar'] not in wajib:
        return 'Kunci jawaban harus sesuai jumlah pilihan yang aktif.'

    return None


def _isi_soal_dari_data(soal, data):
    for field in [
        'tipe_soal', 'jumlah_pilihan', 'pertanyaan', 'gambar_pertanyaan',
        'pilihan_a', 'pilihan_b', 'pilihan_c', 'pilihan_d', 'pilihan_e',
        'gambar_pilihan_a', 'gambar_pilihan_b', 'gambar_pilihan_c', 'gambar_pilihan_d', 'gambar_pilihan_e',
        'jawaban_benar', 'bobot'
    ]:
        setattr(soal, field, data.get(field))


def _normalisasi_soal_parsed_pdf(item):
    tipe_soal = (item.get('tipe_soal') or '').lower()
    punya_jawaban = bool((item.get('jawaban_benar') or '').strip())
    punya_opsi = any((item.get(f'pilihan_{h}') or '').strip() for h in ['a', 'b', 'c', 'd', 'e'])

    if tipe_soal not in [Soal.TIPE_PG, Soal.TIPE_ESAI]:
        tipe_soal = Soal.TIPE_PG if (punya_jawaban or punya_opsi) else Soal.TIPE_ESAI

    jumlah_pilihan = int(item.get('jumlah_pilihan') or (5 if item.get('pilihan_e') else 4))
    if jumlah_pilihan not in [4, 5]:
        jumlah_pilihan = 5 if item.get('pilihan_e') else 4

    try:
        bobot = int(item.get('bobot') or 0)
    except (TypeError, ValueError):
        bobot = 0

    data = {
        'tipe_soal': tipe_soal,
        'jumlah_pilihan': jumlah_pilihan if tipe_soal == Soal.TIPE_PG else 0,
        'pertanyaan': (item.get('pertanyaan') or '').strip(),
        'pilihan_a': (item.get('pilihan_a') or '').strip(),
        'pilihan_b': (item.get('pilihan_b') or '').strip(),
        'pilihan_c': (item.get('pilihan_c') or '').strip(),
        'pilihan_d': (item.get('pilihan_d') or '').strip(),
        'pilihan_e': (item.get('pilihan_e') or '').strip(),
        'jawaban_benar': (item.get('jawaban_benar') or '').strip().upper(),
        'bobot': bobot,
        'gambar_pertanyaan': None,
        'gambar_pilihan_a': None,
        'gambar_pilihan_b': None,
        'gambar_pilihan_c': None,
        'gambar_pilihan_d': None,
        'gambar_pilihan_e': None,
    }

    if data['tipe_soal'] == Soal.TIPE_ESAI:
        data['jumlah_pilihan'] = 0
        data['jawaban_benar'] = ''
        for huruf in ['a', 'b', 'c', 'd', 'e']:
            data[f'pilihan_{huruf}'] = ''

    return data


def _simpan_soal_pdf_ke_sesi(sesi, daftar_soal_parsed):
    tersimpan = 0
    gagal = []
    max_urutan = db.session.query(func.max(Soal.urutan)).filter_by(sesi_id=sesi.id).scalar() or 0

    for index, item in enumerate(daftar_soal_parsed, start=1):
        data = _normalisasi_soal_parsed_pdf(item)
        error = _validasi_data_soal(data)
        if error:
            gagal.append(f'Soal {index}: {error}')
            continue

        max_urutan += 1
        soal = Soal(sesi_id=sesi.id, urutan=max_urutan)
        _isi_soal_dari_data(soal, data)
        db.session.add(soal)
        tersimpan += 1

    db.session.commit()
    return tersimpan, gagal


@admin.route('/bank-soal/sesi/<int:sesi_id>/soal/tambah', methods=['POST'])
@login_required
def tambah_soal_sesi(sesi_id):
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi = UjianSesi.query.get_or_404(sesi_id)
    data = _ambil_data_soal_dari_form(request.form)
    error = _validasi_data_soal(data)
    if error:
        flash(error, 'danger')
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    max_urutan = db.session.query(func.max(Soal.urutan)).filter_by(sesi_id=sesi.id).scalar() or 0
    soal = Soal(sesi_id=sesi.id, urutan=max_urutan + 1)
    _isi_soal_dari_data(soal, data)
    db.session.add(soal)
    db.session.commit()

    flash('Soal berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))


@admin.route('/bank-soal/soal/<int:id>/update', methods=['POST'])
@login_required
def update_soal_inline(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    soal = Soal.query.get_or_404(id)
    data = _ambil_data_soal_dari_form(request.form, soal_lama=soal)
    error = _validasi_data_soal(data)
    if error:
        flash(error, 'danger')
        return redirect(url_for('admin.bank_soal', sesi_id=soal.sesi_id, edit_id=soal.id))

    _isi_soal_dari_data(soal, data)
    try:
        soal.urutan = int(request.form.get('urutan') or soal.urutan or 0)
    except (TypeError, ValueError):
        pass
    db.session.commit()

    flash('Soal berhasil disimpan.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=soal.sesi_id))


@admin.route('/bank-soal/soal/<int:id>/hapus', methods=['POST'])
@login_required
def hapus_soal(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    soal = Soal.query.get_or_404(id)
    sesi_id = soal.sesi_id
    upload_folder = current_app.config['UPLOAD_FOLDER']
    for filename in [
        soal.gambar_pertanyaan,
        soal.gambar_pilihan_a,
        soal.gambar_pilihan_b,
        soal.gambar_pilihan_c,
        soal.gambar_pilihan_d,
        soal.gambar_pilihan_e,
    ]:
        delete_uploaded_file(upload_folder, filename)

    db.session.delete(soal)
    db.session.commit()

    flash('Soal berhasil dihapus.', 'success')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi_id))


@admin.route('/bank-soal/tambah', methods=['GET', 'POST'])
@login_required
def tambah_soal():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_list, sesi_aktif = _get_sesi_aktif_dari_request()
    if request.method == 'POST':
        sesi_id = request.form.get('sesi_id', type=int) or (sesi_aktif.id if sesi_aktif else None)
        if not sesi_id:
            flash('Buat sesi ujian terlebih dahulu.', 'warning')
            return redirect(url_for('admin.bank_soal'))
        return tambah_soal_sesi(sesi_id)

    return redirect(url_for('admin.bank_soal', sesi_id=sesi_aktif.id) if sesi_aktif else url_for('admin.bank_soal'))


@admin.route('/bank-soal/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_soal(id):
    soal = Soal.query.get_or_404(id)
    return redirect(url_for('admin.bank_soal', sesi_id=soal.sesi_id, edit_id=soal.id))


@admin.route('/bank-soal/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_soal_legacy(id):
    return hapus_soal(id)


@admin.route('/bank-soal/upload', methods=['GET', 'POST'])
@login_required
def upload_soal_pdf():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_list = UjianSesi.query.order_by(UjianSesi.urutan, UjianSesi.id).all()
    if request.method == 'POST':
        file = request.files.get('file_pdf')
        sesi_id = request.form.get('sesi_id', type=int)

        sesi = UjianSesi.query.get(sesi_id) if sesi_id else None
        if not sesi:
            flash('Pilih sesi ujian terlebih dahulu.', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))

        if not file or file.filename == '':
            flash('Pilih file PDF terlebih dahulu.', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))

        if not file.filename.lower().endswith('.pdf'):
            flash('File harus berformat PDF.', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))

        temp_folder = os.path.join(current_app.instance_path, 'tmp')
        os.makedirs(temp_folder, exist_ok=True)
        nama_file_sementara = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        path_sementara = os.path.join(temp_folder, nama_file_sementara)
        file.save(path_sementara)

        try:
            daftar_soal_parsed, errors = parse_soal_pdf(path_sementara)
        except Exception as e:
            flash(f'Gagal membaca PDF: {e}', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))
        finally:
            if os.path.exists(path_sementara):
                os.remove(path_sementara)

        if errors:
            pesan_error = 'Sebagian soal dilewati karena tidak sesuai format: ' + '; '.join(errors[:10])
            if len(errors) > 10:
                pesan_error += f' (dan {len(errors) - 10} lainnya)'
            flash(pesan_error, 'warning')

        if not daftar_soal_parsed:
            flash('Tidak ada soal yang terdeteksi di PDF.', 'warning')
            return redirect(url_for('admin.upload_soal_pdf'))

        tersimpan, gagal = _simpan_soal_pdf_ke_sesi(sesi, daftar_soal_parsed)
        if gagal:
            pesan_gagal = 'Sebagian soal belum tersimpan: ' + '; '.join(gagal[:10])
            if len(gagal) > 10:
                pesan_gagal += f' (dan {len(gagal) - 10} lainnya)'
            flash(pesan_gagal, 'warning')

        if tersimpan:
            flash(f'{tersimpan} soal berhasil masuk ke bank soal.', 'success')
        else:
            flash('Belum ada soal PDF yang valid untuk disimpan.', 'warning')
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    return render_template('admin/upload_soal.html', sesi_list=sesi_list)


@admin.route('/bank-soal/upload/preview')
@login_required
def preview_upload_soal_pdf():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_id = session.get('preview_soal_sesi_id')
    session.pop('preview_soal_pdf', None)
    session.pop('preview_soal_sesi_id', None)
    return redirect(url_for('admin.bank_soal', sesi_id=sesi_id) if sesi_id else url_for('admin.bank_soal'))


@admin.route('/bank-soal/upload/preview/simpan/<int:index>', methods=['POST'])
@login_required
def simpan_preview_soal_pdf(index):
    if not _require_admin():
        return "Akses Ditolak", 403

    daftar_soal = session.get('preview_soal_pdf') or []
    sesi_id = session.get('preview_soal_sesi_id')
    sesi = UjianSesi.query.get(sesi_id) if sesi_id else None

    if not sesi or index < 0 or index >= len(daftar_soal):
        flash('Soal preview tidak ditemukan.', 'danger')
        return redirect(url_for('admin.preview_upload_soal_pdf'))

    item = daftar_soal[index]
    data = {
        'tipe_soal': (request.form.get('tipe_soal') or item.get('tipe_soal') or Soal.TIPE_PG).lower(),
        'jumlah_pilihan': int(request.form.get('jumlah_pilihan') or item.get('jumlah_pilihan') or 4),
        'pertanyaan': request.form.get('pertanyaan') or item.get('pertanyaan'),
        'pilihan_a': request.form.get('pilihan_a') or item.get('pilihan_a') or '',
        'pilihan_b': request.form.get('pilihan_b') or item.get('pilihan_b') or '',
        'pilihan_c': request.form.get('pilihan_c') or item.get('pilihan_c') or '',
        'pilihan_d': request.form.get('pilihan_d') or item.get('pilihan_d') or '',
        'pilihan_e': request.form.get('pilihan_e') or item.get('pilihan_e') or '',
        'jawaban_benar': (request.form.get('jawaban_benar') or item.get('jawaban_benar') or '').upper(),
        'bobot': int(request.form.get('bobot') or item.get('bobot') or 0),
        'gambar_pertanyaan': None,
        'gambar_pilihan_a': None,
        'gambar_pilihan_b': None,
        'gambar_pilihan_c': None,
        'gambar_pilihan_d': None,
        'gambar_pilihan_e': None,
    }
    if data['tipe_soal'] == Soal.TIPE_ESAI:
        data['jumlah_pilihan'] = 0
        data['jawaban_benar'] = ''
        for huruf in ['a', 'b', 'c', 'd', 'e']:
            data[f'pilihan_{huruf}'] = ''

    error = _validasi_data_soal(data)
    if error:
        flash(error, 'danger')
        return redirect(url_for('admin.preview_upload_soal_pdf'))

    max_urutan = db.session.query(func.max(Soal.urutan)).filter_by(sesi_id=sesi.id).scalar() or 0
    soal = Soal(sesi_id=sesi.id, urutan=max_urutan + 1)
    _isi_soal_dari_data(soal, data)
    db.session.add(soal)

    daftar_soal.pop(index)
    session['preview_soal_pdf'] = daftar_soal
    session.modified = True
    db.session.commit()

    flash('Satu soal berhasil disimpan.', 'success')
    if not daftar_soal:
        session.pop('preview_soal_pdf', None)
        session.pop('preview_soal_sesi_id', None)
        return redirect(url_for('admin.bank_soal', sesi_id=sesi.id))

    return redirect(url_for('admin.preview_upload_soal_pdf'))


@admin.route('/bank-soal/upload/preview/batal', methods=['POST'])
@login_required
def batal_preview_soal_pdf():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_id = session.get('preview_soal_sesi_id')
    session.pop('preview_soal_pdf', None)
    session.pop('preview_soal_sesi_id', None)
    flash('Preview soal dibatalkan.', 'info')
    return redirect(url_for('admin.bank_soal', sesi_id=sesi_id) if sesi_id else url_for('admin.bank_soal'))


@admin.route('/hasil-ujian')
@login_required
def hasil_ujian():
    if not _require_admin():
        return "Akses Ditolak", 403

    sesi_list = UjianSesi.query.order_by(UjianSesi.urutan, UjianSesi.id).all()
    sesi_id = request.args.get('sesi_id', type=int)
    sesi_aktif = UjianSesi.query.get(sesi_id) if sesi_id else (sesi_list[0] if sesi_list else None)

    query = HasilUjian.query.filter_by(status=HasilUjian.STATUS_SELESAI)
    if sesi_aktif:
        query = query.filter_by(sesi_id=sesi_aktif.id)

    data_hasil = query.order_by(HasilUjian.nilai.desc()).all()
    total_soal = Soal.query.filter_by(sesi_id=sesi_aktif.id).count() if sesi_aktif else 0

    return render_template(
        'admin/hasil_ujian.html',
        data_hasil=data_hasil,
        total_soal=total_soal,
        sesi_list=sesi_list,
        sesi_aktif=sesi_aktif
    )

@admin.route('/hasil-ujian/<int:id>/koreksi-esai', methods=['GET', 'POST'])
@login_required
def koreksi_esai(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    hasil = HasilUjian.query.get_or_404(id)
    jawaban = sorted(hasil.jawaban, key=lambda item: ((item.soal.urutan or 0) if item.soal else 0, item.soal_id))
    jawaban_pg = [item for item in jawaban if item.soal and item.soal.is_pilihan_ganda()]
    jawaban_esai = [item for item in jawaban if item.soal and item.soal.is_esai()]

    if request.method == 'POST':
        total_esai = 0
        for item in jawaban_esai:
            maksimal = item.soal.bobot or 0
            try:
                skor = float(request.form.get(f'skor_{item.id}') or 0)
            except (TypeError, ValueError):
                skor = 0
            if skor < 0:
                skor = 0
            if maksimal and skor > maksimal:
                skor = maksimal
            item.skor_esai = round(skor, 2)
            total_esai += item.skor_esai

        jumlah_benar = 0
        for item in jawaban_pg:
            item.benar = bool(item.jawaban_dipilih) and item.jawaban_dipilih == item.soal.jawaban_benar
            if item.benar:
                jumlah_benar += 1

        total_bobot_esai = sum((item.soal.bobot or 0) for item in jawaban_esai)
        max_nilai_pg = max(0, 100 - total_bobot_esai)
        nilai_pg = round((jumlah_benar / len(jawaban_pg)) * max_nilai_pg, 2) if jawaban_pg else 0

        hasil.jumlah_soal = len(jawaban)
        hasil.jumlah_benar = jumlah_benar
        hasil.nilai_pg = nilai_pg
        hasil.nilai_esai = round(total_esai, 2)
        hasil.nilai = round(nilai_pg + total_esai, 2)
        hasil.esai_dikoreksi = True
        db.session.commit()

        flash('Nilai esai berhasil disimpan.', 'success')
        return redirect(url_for('admin.hasil_ujian', sesi_id=hasil.sesi_id))

    return render_template(
        'admin/koreksi_esai.html',
        hasil=hasil,
        jawaban_pg=jawaban_pg,
        jawaban_esai=jawaban_esai,
    )


@admin.route('/hasil-ujian/<int:id>/reset', methods=['POST'])
@login_required
def reset_ujian_siswa(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    hasil = HasilUjian.query.get_or_404(id)
    nama_siswa = hasil.calon_siswa.nama_lengkap if hasil.calon_siswa else 'Calon siswa'
    label_sesi = hasil.label_sesi()
    sesi_id = hasil.sesi_id

    db.session.delete(hasil)
    db.session.commit()

    flash(f'Ujian {label_sesi} untuk {nama_siswa} berhasil direset. Siswa dapat mengerjakan ulang sesi tersebut.', 'success')
    return redirect(url_for('admin.hasil_ujian', sesi_id=sesi_id))


@admin.route('/hasil-seleksi')
@login_required
def hasil_seleksi():
    if not _require_admin():
        return "Akses Ditolak", 403

    data_siswa = [
        cs for cs in CalonSiswa.query.all()
        if cs.sudah_lolos_administrasi()
    ]

    data_siswa.sort(
        key=lambda cs: (nilai if (nilai := cs.nilai_akhir_ujian()) is not None else -1),
        reverse=True
    )

    total_diterima = CalonSiswa.query.filter_by(status_kelulusan='Diterima').count()
    total_tidak_diterima = CalonSiswa.query.filter_by(status_kelulusan='Tidak Diterima').count()

    return render_template(
        'admin/hasil_seleksi.html',
        data_siswa=data_siswa,
        total_diterima=total_diterima,
        total_tidak_diterima=total_tidak_diterima
    )


@admin.route('/hasil-seleksi/terima/<int:id>', methods=['POST'])
@login_required
def terima_seleksi(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Diterima'
    db.session.commit()
    flash(f'{siswa.nama_lengkap} dinyatakan Diterima', 'success')
    return redirect(url_for('admin.hasil_seleksi'))


@admin.route('/hasil-seleksi/tolak/<int:id>', methods=['POST'])
@login_required
def tolak_seleksi(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Tidak Diterima'
    db.session.commit()
    flash(f'{siswa.nama_lengkap} dinyatakan Tidak Diterima', 'warning')
    return redirect(url_for('admin.hasil_seleksi'))


@admin.route('/hasil-seleksi/reset/<int:id>', methods=['POST'])
@login_required
def reset_seleksi(id):
    if not _require_admin():
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Menunggu'
    db.session.commit()
    flash(f'Status kelulusan {siswa.nama_lengkap} direset ke Menunggu', 'success')
    return redirect(url_for('admin.hasil_seleksi'))
