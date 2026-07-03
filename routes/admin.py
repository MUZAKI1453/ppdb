from flask import Blueprint, render_template, request, flash, url_for, redirect, send_from_directory
from flask_login import login_required, current_user
from models.calon_siswa import CalonSiswa
from models.alamat_siswa import AlamatSiswa
from models.data_ayah import DataAyah
from models.data_ibu import DataIbu
from models.data_wali import DataWali
from extensions_db import db
from models.berkas import Berkas
from models.soal import Soal
from models.hasil_ujian import HasilUjian
from config import Config
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.soal_pdf_parser import parse_soal_pdf
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

    periode_ppdb = "2026 / 2027"

    return render_template(
        'admin/dashboard.html',
        total_pendaftar=total_pendaftar,
        data_diverifikasi=data_diverifikasi,
        berkas_diverifikasi=berkas_diverifikasi,
        berkas_ditolak=berkas_ditolak,
        menunggu_verifikasi=menunggu_verifikasi,
        total_berkas_masuk=total_berkas_masuk,
        total_diterima=total_diterima,
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


# ==================================================
# BANK SOAL - MENAMPILKAN SELURUH SOAL / READ
# URL : /admin/bank-soal
# ==================================================
@admin.route('/bank-soal')
@login_required
def bank_soal():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    # Tab aktif: 'akademik' atau 'psikotes' lewat ?jenis=...
    jenis_aktif = request.args.get('jenis', Soal.JENIS_AKADEMIK)
    if jenis_aktif not in [j for j, _ in Soal.JENIS_PILIHAN]:
        jenis_aktif = Soal.JENIS_AKADEMIK

    daftar_soal = Soal.query.filter_by(
        jenis_ujian=jenis_aktif
    ).order_by(Soal.id).all()

    jumlah_per_jenis = {
        jenis: Soal.query.filter_by(jenis_ujian=jenis).count()
        for jenis, _ in Soal.JENIS_PILIHAN
    }

    return render_template(
        'admin/bank_soal.html',
        daftar_soal=daftar_soal,
        jenis_aktif=jenis_aktif,
        jenis_pilihan=Soal.JENIS_PILIHAN,
        jumlah_per_jenis=jumlah_per_jenis
    )


# ==================================================
# BANK SOAL - TAMBAH SOAL / CREATE
# URL : /admin/bank-soal/tambah
# ==================================================
@admin.route('/bank-soal/tambah', methods=['GET', 'POST'])
@login_required
def tambah_soal():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    if request.method == 'POST':
        pertanyaan = request.form.get('pertanyaan')
        pilihan_a = request.form.get('pilihan_a')
        pilihan_b = request.form.get('pilihan_b')
        pilihan_c = request.form.get('pilihan_c')
        pilihan_d = request.form.get('pilihan_d')
        jawaban_benar = request.form.get('jawaban_benar')
        jenis_ujian = request.form.get('jenis_ujian', Soal.JENIS_AKADEMIK)

        if jenis_ujian not in [j for j, _ in Soal.JENIS_PILIHAN]:
            jenis_ujian = Soal.JENIS_AKADEMIK

        if not all([pertanyaan, pilihan_a, pilihan_b, pilihan_c, pilihan_d, jawaban_benar]):
            flash('Semua field wajib diisi', 'danger')
            return render_template('admin/form_soal.html', soal=None, form_data=request.form, jenis_pilihan=Soal.JENIS_PILIHAN)

        soal = Soal(
            pertanyaan=pertanyaan,
            pilihan_a=pilihan_a,
            pilihan_b=pilihan_b,
            pilihan_c=pilihan_c,
            pilihan_d=pilihan_d,
            jawaban_benar=jawaban_benar,
            kategori=request.form.get('kategori'),
            jenis_ujian=jenis_ujian
        )

        db.session.add(soal)
        db.session.commit()

        flash('Soal berhasil ditambahkan', 'success')
        return redirect(url_for('admin.bank_soal', jenis=jenis_ujian))

    jenis_default = request.args.get('jenis', Soal.JENIS_AKADEMIK)
    if jenis_default not in [j for j, _ in Soal.JENIS_PILIHAN]:
        jenis_default = Soal.JENIS_AKADEMIK

    return render_template(
        'admin/form_soal.html',
        soal=None,
        jenis_pilihan=Soal.JENIS_PILIHAN,
        jenis_default=jenis_default
    )


# ==================================================
# BANK SOAL - EDIT SOAL / UPDATE
# URL : /admin/bank-soal/edit/<id>
# ==================================================
@admin.route('/bank-soal/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_soal(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    soal = Soal.query.get_or_404(id)

    if request.method == 'POST':
        pertanyaan = request.form.get('pertanyaan')
        pilihan_a = request.form.get('pilihan_a')
        pilihan_b = request.form.get('pilihan_b')
        pilihan_c = request.form.get('pilihan_c')
        pilihan_d = request.form.get('pilihan_d')
        jawaban_benar = request.form.get('jawaban_benar')
        jenis_ujian = request.form.get('jenis_ujian', Soal.JENIS_AKADEMIK)

        if jenis_ujian not in [j for j, _ in Soal.JENIS_PILIHAN]:
            jenis_ujian = Soal.JENIS_AKADEMIK

        if not all([pertanyaan, pilihan_a, pilihan_b, pilihan_c, pilihan_d, jawaban_benar]):
            flash('Semua field wajib diisi', 'danger')
            return render_template('admin/form_soal.html', soal=soal, jenis_pilihan=Soal.JENIS_PILIHAN)

        soal.pertanyaan = pertanyaan
        soal.pilihan_a = pilihan_a
        soal.pilihan_b = pilihan_b
        soal.pilihan_c = pilihan_c
        soal.pilihan_d = pilihan_d
        soal.jawaban_benar = jawaban_benar
        soal.kategori = request.form.get('kategori')
        soal.jenis_ujian = jenis_ujian

        db.session.commit()

        flash('Soal berhasil diperbarui', 'success')
        return redirect(url_for('admin.bank_soal', jenis=jenis_ujian))

    return render_template('admin/form_soal.html', soal=soal, jenis_pilihan=Soal.JENIS_PILIHAN)


# ==================================================
# BANK SOAL - HAPUS SOAL / DELETE
# URL : /admin/bank-soal/hapus/<id>
# ==================================================
@admin.route('/bank-soal/hapus/<int:id>')
@login_required
def hapus_soal(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    soal = Soal.query.get_or_404(id)
    jenis_ujian = soal.jenis_ujian

    db.session.delete(soal)
    db.session.commit()

    flash('Soal berhasil dihapus', 'success')
    return redirect(url_for('admin.bank_soal', jenis=jenis_ujian))


# ==================================================
# BANK SOAL - TAMBAH SOAL VIA UPLOAD PDF
# URL : /admin/bank-soal/upload
#
# Format PDF yang harus diikuti ada di
# utils/soal_pdf_parser.py. Ringkasnya per soal:
#
#   1. Pertanyaan...
#   A. Pilihan A
#   B. Pilihan B
#   C. Pilihan C
#   D. Pilihan D
#   KUNCI: A
#   KATEGORI: Matematika   (opsional)
# ==================================================
@admin.route('/bank-soal/upload', methods=['GET', 'POST'])
@login_required
def upload_soal_pdf():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    if request.method == 'POST':
        file = request.files.get('file_pdf')
        jenis_ujian = request.form.get('jenis_ujian', Soal.JENIS_AKADEMIK)
        kategori_default = request.form.get('kategori_default') or None

        if jenis_ujian not in [j for j, _ in Soal.JENIS_PILIHAN]:
            jenis_ujian = Soal.JENIS_AKADEMIK

        if not file or file.filename == '':
            flash('Pilih file PDF terlebih dahulu.', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))

        if not file.filename.lower().endswith('.pdf'):
            flash('File harus berformat PDF.', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))

        # Simpan sementara supaya bisa dibuka pdfplumber,
        # lalu langsung dihapus lagi setelah selesai diparse.
        nama_file_sementara = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        path_sementara = os.path.join(Config.UPLOAD_FOLDER, nama_file_sementara)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(path_sementara)

        try:
            daftar_soal_parsed, errors = parse_soal_pdf(path_sementara)
        except Exception as e:
            flash(f'Gagal membaca PDF: {e}', 'danger')
            return redirect(url_for('admin.upload_soal_pdf'))
        finally:
            if os.path.exists(path_sementara):
                os.remove(path_sementara)

        jumlah_masuk = 0

        for item in daftar_soal_parsed:
            soal = Soal(
                pertanyaan=item['pertanyaan'],
                pilihan_a=item['pilihan_a'],
                pilihan_b=item['pilihan_b'],
                pilihan_c=item['pilihan_c'],
                pilihan_d=item['pilihan_d'],
                jawaban_benar=item['jawaban_benar'],
                kategori=item['kategori'] or kategori_default,
                jenis_ujian=jenis_ujian
            )
            db.session.add(soal)
            jumlah_masuk += 1

        if jumlah_masuk:
            db.session.commit()

        if jumlah_masuk:
            flash(f'{jumlah_masuk} soal berhasil diimpor dari PDF.', 'success')
        if errors:
            pesan_error = 'Sebagian soal dilewati karena tidak sesuai format: ' + '; '.join(errors[:10])
            if len(errors) > 10:
                pesan_error += f' (dan {len(errors) - 10} lainnya)'
            flash(pesan_error, 'warning')

        if not jumlah_masuk and not errors:
            flash('Tidak ada soal yang terdeteksi di PDF. Pastikan formatnya sesuai contoh.', 'warning')

        return redirect(url_for('admin.bank_soal', jenis=jenis_ujian))

    return render_template(
        'admin/upload_soal.html',
        jenis_pilihan=Soal.JENIS_PILIHAN
    )


# ==================================================
# HASIL UJIAN - MENAMPILKAN SELURUH HASIL / READ
# URL : /admin/hasil-ujian
# ==================================================
@admin.route('/hasil-ujian')
@login_required
def hasil_ujian():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    jenis_aktif = request.args.get('jenis', Soal.JENIS_AKADEMIK)
    if jenis_aktif not in [j for j, _ in Soal.JENIS_PILIHAN]:
        jenis_aktif = Soal.JENIS_AKADEMIK

    data_hasil = HasilUjian.query.filter_by(
        status=HasilUjian.STATUS_SELESAI,
        jenis_ujian=jenis_aktif
    ).order_by(HasilUjian.nilai.desc()).all()

    total_soal = Soal.query.filter_by(jenis_ujian=jenis_aktif).count()

    return render_template(
        'admin/hasil_ujian.html',
        data_hasil=data_hasil,
        total_soal=total_soal,
        jenis_aktif=jenis_aktif,
        jenis_pilihan=Soal.JENIS_PILIHAN
    )


# ==================================================
# HASIL UJIAN - DETAIL JAWABAN SISWA
# URL : /admin/hasil-ujian/<id>
# ==================================================
@admin.route('/hasil-ujian/<int:id>')
@login_required
def detail_hasil_ujian(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    hasil = HasilUjian.query.get_or_404(id)

    return render_template(
        'admin/detail_hasil_ujian.html',
        hasil=hasil
    )


# ==================================================
# HASIL SELEKSI - MENAMPILKAN SISWA YANG SUDAH LOLOS
# ADMINISTRASI UNTUK DITETAPKAN KELULUSANNYA
# URL : /admin/hasil-seleksi
# ==================================================
@admin.route('/hasil-seleksi')
@login_required
def hasil_seleksi():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    data_siswa = [
        cs for cs in CalonSiswa.query.all()
        if cs.sudah_lolos_administrasi()
    ]

    # Urutkan dari nilai akhir tertinggi (rata-rata nilai
    # ujian Akademik & Psikotes yang sudah selesai). Siswa
    # yang belum mengerjakan ujian sama sekali ditempatkan
    # paling bawah.
    data_siswa.sort(
        key=lambda cs: (
            nilai if (nilai := cs.nilai_akhir_ujian()) is not None else -1
        ),
        reverse=True
    )

    total_diterima = CalonSiswa.query.filter_by(
        status_kelulusan='Diterima'
    ).count()

    total_tidak_diterima = CalonSiswa.query.filter_by(
        status_kelulusan='Tidak Diterima'
    ).count()

    return render_template(
        'admin/hasil_seleksi.html',
        data_siswa=data_siswa,
        total_diterima=total_diterima,
        total_tidak_diterima=total_tidak_diterima
    )


# ==================================================
# HASIL SELEKSI - TETAPKAN DITERIMA
# URL : /admin/hasil-seleksi/terima/<id>
# ==================================================
@admin.route('/hasil-seleksi/terima/<int:id>')
@login_required
def terima_seleksi(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Diterima'
    db.session.commit()

    flash(f'{siswa.nama_lengkap} dinyatakan Diterima', 'success')
    return redirect(url_for('admin.hasil_seleksi'))


# ==================================================
# HASIL SELEKSI - TETAPKAN TIDAK DITERIMA
# URL : /admin/hasil-seleksi/tolak/<id>
# ==================================================
@admin.route('/hasil-seleksi/tolak/<int:id>')
@login_required
def tolak_seleksi(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Tidak Diterima'
    db.session.commit()

    flash(f'{siswa.nama_lengkap} dinyatakan Tidak Diterima', 'warning')
    return redirect(url_for('admin.hasil_seleksi'))


# ==================================================
# HASIL SELEKSI - RESET KE MENUNGGU
# URL : /admin/hasil-seleksi/reset/<id>
# ==================================================
@admin.route('/hasil-seleksi/reset/<int:id>')
@login_required
def reset_seleksi(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403

    siswa = CalonSiswa.query.get_or_404(id)
    siswa.status_kelulusan = 'Menunggu'
    db.session.commit()

    flash(f'Status kelulusan {siswa.nama_lengkap} direset ke Menunggu', 'success')
    return redirect(url_for('admin.hasil_seleksi'))