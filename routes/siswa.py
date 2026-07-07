import os
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from extensions_db import db
from models.user import User
from models.calon_siswa import CalonSiswa
from models.alamat_siswa import AlamatSiswa
from models.data_ayah import DataAyah
from models.data_ibu import DataIbu
from models.data_wali import DataWali
from models.berkas import Berkas
from models.ujian_sesi import UjianSesi
from models.soal import Soal
from models.hasil_ujian import HasilUjian
from models.jawaban_ujian import JawabanUjian
from utils.upload_helper import save_secure_upload, delete_uploaded_file, is_image, is_pdf


siswa = Blueprint('siswa', __name__, url_prefix='/siswa')

FIELD_WAJIB = [
    ('nama_lengkap', 'Nama Lengkap'),
    ('nisn', 'NISN'),
    ('nik', 'NIK'),
    ('no_registrasi_akta', 'Nomor Registrasi Akta'),
    ('tempat_lahir', 'Tempat Lahir'),
    ('tanggal_lahir', 'Tanggal Lahir'),
    ('jenis_kelamin', 'Jenis Kelamin'),
    ('agama', 'Agama'),
    ('kewarganegaraan', 'Kewarganegaraan'),
    ('kebutuhan_khusus', 'Berkebutuhan Khusus'),
    ('status_tinggal', 'Status Tinggal'),
    ('moda_transportasi', 'Moda Transportasi'),
    ('anak_ke', 'Anak Ke'),
    ('tinggi_badan', 'Tinggi Badan'),
    ('berat_badan', 'Berat Badan'),
    ('jumlah_saudara_kandung', 'Jumlah Saudara Kandung'),
    ('no_hp', 'Nomor HP'),
    ('email', 'Email'),
    ('alamat_jalan', 'Alamat Jalan'),
    ('dusun', 'Dusun/Blok'),
    ('rt', 'RT'),
    ('rw', 'RW'),
    ('desa_kelurahan', 'Desa/Kelurahan'),
    ('kecamatan', 'Kecamatan'),
    ('kabupaten', 'Kabupaten/Kota'),
    ('kode_pos', 'Kode Pos'),
    ('asal_sekolah', 'Asal Sekolah'),
    ('tahun_lulus', 'Tahun Lulus'),
    ('jarak_ke_sekolah', 'Jarak Tempat Tinggal ke Sekolah'),
    ('waktu_tempuh', 'Waktu Tempuh ke Sekolah'),
    ('ayah_nama', 'Nama Ayah'),
    ('ayah_nik', 'NIK Ayah'),
    ('ayah_tempat_lahir', 'Tempat Lahir Ayah'),
    ('ayah_tanggal_lahir', 'Tanggal Lahir Ayah'),
    ('ayah_pendidikan', 'Pendidikan Ayah'),
    ('ayah_pekerjaan', 'Pekerjaan Ayah'),
    ('ayah_penghasilan', 'Penghasilan Ayah'),
    ('ayah_kebutuhan_khusus', 'Berkebutuhan Khusus Ayah'),
    ('ayah_no_hp', 'Nomor HP Ayah'),
    ('ibu_nama', 'Nama Ibu'),
    ('ibu_nik', 'NIK Ibu'),
    ('ibu_tempat_lahir', 'Tempat Lahir Ibu'),
    ('ibu_tanggal_lahir', 'Tanggal Lahir Ibu'),
    ('ibu_pendidikan', 'Pendidikan Ibu'),
    ('ibu_pekerjaan', 'Pekerjaan Ibu'),
    ('ibu_penghasilan', 'Penghasilan Ibu'),
    ('ibu_kebutuhan_khusus', 'Berkebutuhan Khusus Ibu'),
    ('ibu_no_hp', 'Nomor HP Ibu'),
]

FIELD_BERKAS = ['pas_foto', 'kartu_keluarga', 'akta_lahir', 'ijazah', 'ktp_orang_tua']


def validasi_formulir(form):
    field_kosong = []
    for nama_field, label in FIELD_WAJIB:
        nilai = (form.get(nama_field) or '').strip()
        if not nilai:
            field_kosong.append(label)
    return field_kosong


def _parse_tanggal(form, nama_field):
    nilai = form.get(nama_field)
    if not nilai:
        return None
    return datetime.strptime(nilai, '%Y-%m-%d').date()


def _ensure_relasi(calon_siswa):
    if not calon_siswa.alamat:
        calon_siswa.alamat = AlamatSiswa(calon_siswa_id=calon_siswa.id)
    if not calon_siswa.ayah:
        calon_siswa.ayah = DataAyah(calon_siswa_id=calon_siswa.id)
    if not calon_siswa.ibu:
        calon_siswa.ibu = DataIbu(calon_siswa_id=calon_siswa.id)


def isi_data_dari_form(calon_siswa, form):
    calon_siswa.nama_lengkap = form.get('nama_lengkap')
    calon_siswa.nisn = form.get('nisn')
    calon_siswa.nik = form.get('nik')
    calon_siswa.no_registrasi_akta = form.get('no_registrasi_akta')
    calon_siswa.tempat_lahir = form.get('tempat_lahir')
    calon_siswa.tanggal_lahir = _parse_tanggal(form, 'tanggal_lahir')
    calon_siswa.jenis_kelamin = form.get('jenis_kelamin')
    calon_siswa.agama = form.get('agama')
    calon_siswa.kewarganegaraan = form.get('kewarganegaraan')
    calon_siswa.kebutuhan_khusus = form.get('kebutuhan_khusus')
    calon_siswa.status_tinggal = form.get('status_tinggal')
    calon_siswa.moda_transportasi = form.get('moda_transportasi')
    calon_siswa.anak_ke = form.get('anak_ke') or None
    calon_siswa.tinggi_badan = form.get('tinggi_badan') or None
    calon_siswa.berat_badan = form.get('berat_badan') or None
    calon_siswa.jarak_ke_sekolah = form.get('jarak_ke_sekolah')
    calon_siswa.waktu_tempuh = form.get('waktu_tempuh')
    calon_siswa.jumlah_saudara_kandung = form.get('jumlah_saudara_kandung') or None
    calon_siswa.no_hp = form.get('no_hp')
    calon_siswa.email = form.get('email')
    calon_siswa.asal_sekolah = form.get('asal_sekolah')
    calon_siswa.tahun_lulus = form.get('tahun_lulus')

    alamat = calon_siswa.alamat
    alamat.alamat_jalan = form.get('alamat_jalan')
    alamat.dusun = form.get('dusun')
    alamat.rt = form.get('rt')
    alamat.rw = form.get('rw')
    alamat.desa_kelurahan = form.get('desa_kelurahan')
    alamat.kecamatan = form.get('kecamatan')
    alamat.kabupaten = form.get('kabupaten')
    alamat.kode_pos = form.get('kode_pos')

    ayah = calon_siswa.ayah
    ayah.nama = form.get('ayah_nama')
    ayah.nik = form.get('ayah_nik')
    ayah.tempat_lahir = form.get('ayah_tempat_lahir')
    ayah.tanggal_lahir = _parse_tanggal(form, 'ayah_tanggal_lahir')
    ayah.pendidikan = form.get('ayah_pendidikan')
    ayah.pekerjaan = form.get('ayah_pekerjaan')
    ayah.penghasilan = form.get('ayah_penghasilan')
    ayah.kebutuhan_khusus = form.get('ayah_kebutuhan_khusus')
    ayah.no_hp = form.get('ayah_no_hp')

    ibu = calon_siswa.ibu
    ibu.nama = form.get('ibu_nama')
    ibu.nik = form.get('ibu_nik')
    ibu.tempat_lahir = form.get('ibu_tempat_lahir')
    ibu.tanggal_lahir = _parse_tanggal(form, 'ibu_tanggal_lahir')
    ibu.pendidikan = form.get('ibu_pendidikan')
    ibu.pekerjaan = form.get('ibu_pekerjaan')
    ibu.penghasilan = form.get('ibu_penghasilan')
    ibu.kebutuhan_khusus = form.get('ibu_kebutuhan_khusus')
    ibu.no_hp = form.get('ibu_no_hp')

    wali_nama = form.get('wali_nama')
    if wali_nama:
        if not calon_siswa.wali:
            calon_siswa.wali = DataWali(calon_siswa_id=calon_siswa.id)
        wali = calon_siswa.wali
        wali.nama = wali_nama
        wali.nik = form.get('wali_nik')
        wali.tempat_lahir = form.get('wali_tempat_lahir')
        wali.tanggal_lahir = _parse_tanggal(form, 'wali_tanggal_lahir')
        wali.pendidikan = form.get('wali_pendidikan')
        wali.pekerjaan = form.get('wali_pekerjaan')
        wali.penghasilan = form.get('wali_penghasilan')
        wali.kebutuhan_khusus = form.get('wali_kebutuhan_khusus')
        wali.no_hp = form.get('wali_no_hp')
    elif calon_siswa.wali:
        db.session.delete(calon_siswa.wali)
        calon_siswa.wali = None


def _preview_formulir_object(calon_siswa, form):
    preview = calon_siswa or CalonSiswa(user_id=current_user.id)
    _ensure_relasi(preview)
    if form.get('wali_nama') and not preview.wali:
        preview.wali = DataWali(calon_siswa_id=preview.id)
    isi_data_dari_form(preview, form)
    return preview


def _cek_nisn_unik(nisn, calon_siswa_id=None, user_id=None):
    query_calon = CalonSiswa.query.filter(CalonSiswa.nisn == nisn)
    if calon_siswa_id:
        query_calon = query_calon.filter(CalonSiswa.id != calon_siswa_id)
    if query_calon.first():
        return False

    query_user = User.query.filter(User.username == nisn)
    if user_id:
        query_user = query_user.filter(User.id != user_id)
    return query_user.first() is None


def _sesi_aktif_dengan_soal():
    return [
        sesi for sesi in UjianSesi.query.filter_by(aktif=True).order_by(UjianSesi.urutan, UjianSesi.id).all()
        if sesi.jumlah_soal > 0
    ]


def _next_sesi(calon_siswa):
    for sesi in _sesi_aktif_dengan_soal():
        hasil = calon_siswa.get_hasil_ujian(sesi.id)
        if not hasil or not hasil.is_selesai():
            return sesi
    return None


def _panduan_tahapan_dashboard(calon_siswa, berkas, boleh_ujian, sesi_berikutnya, status_ujian):
    """Buat teks panduan singkat yang dinamis sesuai posisi calon siswa."""
    if not calon_siswa or not calon_siswa.nik:
        return {
            'label': 'Tahap 1 dari 5',
            'judul': 'Lengkapi Formulir SPMB',
            'deskripsi': 'Mulai dengan mengisi identitas, alamat, asal sekolah, dan data orang tua/wali. Pastikan data sesuai dokumen resmi.',
            'aksi_url': url_for('siswa.formulir', edit='true'),
            'aksi_teks': 'Isi Formulir',
            'ikon': 'bi-file-earmark-person-fill',
        }

    if calon_siswa.status_verifikasi == 'Ditolak':
        return {
            'label': 'Tahap Perbaikan Data',
            'judul': 'Perbaiki Formulir SPMB',
            'deskripsi': calon_siswa.catatan_verifikasi or 'Data formulir perlu diperbaiki. Buka formulir, cek kembali isian, lalu kirim ulang untuk diverifikasi.',
            'aksi_url': url_for('siswa.formulir', edit='true'),
            'aksi_teks': 'Perbaiki Formulir',
            'ikon': 'bi-exclamation-triangle-fill',
        }

    if calon_siswa.status_verifikasi != 'Diverifikasi':
        return {
            'label': 'Tahap 2 dari 5',
            'judul': 'Menunggu Verifikasi Formulir',
            'deskripsi': 'Formulir sudah tersimpan. Panitia akan memeriksa data Anda. Siapkan berkas pendukung agar proses berikutnya lebih cepat.',
            'aksi_url': url_for('siswa.formulir'),
            'aksi_teks': 'Lihat Formulir',
            'ikon': 'bi-hourglass-split',
        }

    if not berkas:
        return {
            'label': 'Tahap 3 dari 5',
            'judul': 'Upload Berkas Persyaratan',
            'deskripsi': 'Unggah pas foto dan dokumen persyaratan. Gunakan file yang jelas, terbaca, dan sesuai format yang diizinkan.',
            'aksi_url': url_for('siswa.upload_berkas'),
            'aksi_teks': 'Upload Berkas',
            'ikon': 'bi-cloud-upload-fill',
        }

    if berkas.status_verifikasi == Berkas.STATUS_DITOLAK:
        return {
            'label': 'Tahap Revisi Berkas',
            'judul': 'Perbaiki Berkas Persyaratan',
            'deskripsi': berkas.catatan_verifikasi or 'Ada berkas yang perlu diperbaiki. Upload ulang hanya dokumen yang ditandai bermasalah.',
            'aksi_url': url_for('siswa.upload_berkas'),
            'aksi_teks': 'Revisi Berkas',
            'ikon': 'bi-file-earmark-x-fill',
        }

    if berkas.status_verifikasi != Berkas.STATUS_DITERIMA:
        return {
            'label': 'Tahap 4 dari 5',
            'judul': 'Menunggu Verifikasi Berkas',
            'deskripsi': 'Berkas sudah diunggah dan sedang menunggu pemeriksaan panitia. Cek dashboard ini secara berkala untuk melihat status terbaru.',
            'aksi_url': url_for('siswa.upload_berkas'),
            'aksi_teks': 'Lihat Berkas',
            'ikon': 'bi-file-earmark-check-fill',
        }

    if boleh_ujian and sesi_berikutnya:
        return {
            'label': 'Tahap 5 dari 5',
            'judul': f'Kerjakan {sesi_berikutnya.judul}',
            'deskripsi': 'Administrasi Anda sudah lolos. Kerjakan sesi ujian secara berurutan. Setelah satu sesi selesai, sesi berikutnya akan muncul otomatis.',
            'aksi_url': url_for('siswa.ujian', sesi_id=sesi_berikutnya.id),
            'aksi_teks': f'Mulai {sesi_berikutnya.judul}',
            'ikon': 'bi-play-circle-fill',
        }

    if status_ujian and all(item['hasil'] and item['hasil'].is_selesai() for item in status_ujian):
        if calon_siswa.status_kelulusan and calon_siswa.status_kelulusan != 'Menunggu':
            return {
                'label': 'Pengumuman Tersedia',
                'judul': 'Lihat Hasil SPMB',
                'deskripsi': 'Seluruh tahapan SPMB sudah selesai dan hasil seleksi sudah tersedia. Buka menu pengumuman untuk melihat status akhir Anda.',
                'aksi_url': url_for('siswa.pengumuman'),
                'aksi_teks': 'Lihat Pengumuman',
                'ikon': 'bi-megaphone-fill',
            }
        return {
            'label': 'Menunggu Pengumuman',
            'judul': 'Semua Sesi Ujian Selesai',
            'deskripsi': 'Jawaban ujian sudah tersimpan. Tunggu panitia menetapkan hasil seleksi dan pantau menu pengumuman secara berkala.',
            'aksi_url': url_for('siswa.hasil_ujian'),
            'aksi_teks': 'Lihat Hasil Ujian',
            'ikon': 'bi-award-fill',
        }

    return {
        'label': 'Tahapan SPMB',
        'judul': 'Pantau Proses SPMB Anda',
        'deskripsi': 'Ikuti tahapan dari formulir, upload berkas, verifikasi administrasi, ujian, sampai pengumuman.',
        'aksi_url': url_for('siswa.dashboard'),
        'aksi_teks': 'Muat Ulang Dashboard',
        'ikon': 'bi-grid-fill',
    }


@siswa.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = CalonSiswa.query.filter_by(user_id=current_user.id).first()
    berkas = None
    progress = 25
    status_data = 'Belum Mengisi'
    status_berkas = 'Belum Upload'
    status_seleksi = 'Menunggu'
    boleh_ujian = False
    status_ujian = []
    sesi_berikutnya = None

    if calon_siswa:
        progress = 50
        status_data = 'Menunggu Verifikasi'
        if calon_siswa.status_verifikasi == 'Diverifikasi':
            status_data = 'Diverifikasi'
        elif calon_siswa.status_verifikasi == 'Ditolak':
            status_data = 'Ditolak'

        berkas = calon_siswa.berkas
        if berkas:
            progress = 75
            status_berkas = 'Menunggu Verifikasi'
            if berkas.status_verifikasi == Berkas.STATUS_DITOLAK:
                status_berkas = 'Ditolak'
            elif berkas.status_verifikasi == Berkas.STATUS_DITERIMA:
                progress = 100
                status_berkas = 'Diverifikasi'

        boleh_ujian = calon_siswa.sudah_lolos_administrasi()
        sesi_berikutnya = _next_sesi(calon_siswa) if boleh_ujian else None

        for sesi in _sesi_aktif_dengan_soal():
            status_ujian.append({
                'sesi': sesi,
                'hasil': calon_siswa.get_hasil_ujian(sesi.id)
            })

        if calon_siswa.sudah_selesai_semua_ujian():
            nilai_akhir = calon_siswa.nilai_akhir_ujian()
            status_seleksi = f'Nilai {nilai_akhir:g}' if nilai_akhir is not None else 'Selesai'
        elif any(item['hasil'] and item['hasil'].is_selesai() for item in status_ujian):
            status_seleksi = 'Lanjut Sesi Berikutnya'
        elif boleh_ujian:
            status_seleksi = 'Siap Ujian'

    panduan_tahapan = _panduan_tahapan_dashboard(
        calon_siswa,
        berkas,
        boleh_ujian,
        sesi_berikutnya,
        status_ujian
    )

    return render_template(
        'siswa/dashboard.html',
        progress=progress,
        status_data=status_data,
        status_berkas=status_berkas,
        status_seleksi=status_seleksi,
        boleh_ujian=boleh_ujian,
        status_ujian=status_ujian,
        sesi_berikutnya=sesi_berikutnya,
        berkas=berkas,
        calon_siswa=calon_siswa,
        panduan_tahapan=panduan_tahapan
    )


@siswa.route('/formulir', methods=['GET', 'POST'])
@login_required
def formulir():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = CalonSiswa.query.filter_by(user_id=current_user.id).first()
    is_locked = bool(calon_siswa and calon_siswa.status_verifikasi == 'Diverifikasi')
    is_new_or_incomplete = calon_siswa is None or not calon_siswa.nik
    edit_mode = (is_new_or_incomplete or request.args.get('edit') == 'true') and not is_locked

    if is_locked and request.method == 'POST':
        flash('Data sudah diverifikasi, tidak dapat diubah.', 'danger')
        return redirect(url_for('siswa.formulir'))

    if request.method == 'POST' and edit_mode:
        try:
            nisn = (request.form.get('nisn') or '').strip()
            field_kosong = validasi_formulir(request.form)

            if nisn and not _cek_nisn_unik(nisn, calon_siswa.id if calon_siswa else None, current_user.id):
                field_kosong.append('NISN sudah digunakan')

            if field_kosong:
                flash('Mohon lengkapi/perbaiki: ' + ', '.join(field_kosong), 'danger')
                preview = _preview_formulir_object(calon_siswa, request.form)
                return render_template(
                    'siswa/formulir.html',
                    calon_siswa=preview,
                    is_locked=is_locked,
                    edit_mode=True,
                    form_data=request.form
                )

            if not calon_siswa:
                calon_siswa = CalonSiswa(user_id=current_user.id)
                db.session.add(calon_siswa)
                db.session.flush()

            _ensure_relasi(calon_siswa)
            isi_data_dari_form(calon_siswa, request.form)

            current_user.username = calon_siswa.nisn
            calon_siswa.status_verifikasi = 'Belum Diverifikasi'
            calon_siswa.catatan_verifikasi = None
            calon_siswa.tanggal_verifikasi = None

            db.session.commit()
            flash('Data berhasil disimpan', 'success')
            return redirect(url_for('siswa.formulir'))

        except (ValueError, IntegrityError) as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template(
        'siswa/formulir.html',
        calon_siswa=calon_siswa,
        is_locked=is_locked,
        edit_mode=edit_mode
    )


@siswa.route('/upload-berkas', methods=['GET', 'POST'])
@login_required
def upload_berkas():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = current_user.calon_siswa
    if not calon_siswa or not calon_siswa.nik:
        flash('Isi formulir SPMB terlebih dahulu', 'danger')
        return redirect(url_for('siswa.formulir'))

    berkas = Berkas.query.filter_by(calon_siswa_id=calon_siswa.id).first()

    if not berkas:
        upload_mode = 'baru'
        field_boleh_upload = FIELD_BERKAS
    elif berkas.status_verifikasi == Berkas.STATUS_DITOLAK:
        upload_mode = 'revisi'
        field_boleh_upload = berkas.list_field_bermasalah
    else:
        upload_mode = 'locked'
        field_boleh_upload = []

    if request.method == 'POST':
        if upload_mode == 'locked':
            flash('Berkas sedang menunggu/telah diverifikasi, tidak dapat diubah.', 'warning')
            return redirect(url_for('siswa.upload_berkas'))

        ada_perubahan = False
        upload_folder = current_app.config['UPLOAD_FOLDER']
        allowed_extensions = current_app.config['ALLOWED_UPLOAD_EXTENSIONS']

        if not berkas:
            berkas = Berkas(calon_siswa_id=calon_siswa.id)

        file_map = {
            'pas_foto': ('pasfoto', 'pas_foto'),
            'kartu_keluarga': ('kk', 'kartu_keluarga'),
            'akta_lahir': ('akta', 'akta_lahir'),
            'ijazah': ('ijazah', 'ijazah'),
            'ktp_orang_tua': ('ktp', 'ktp_orang_tua'),
        }

        try:
            for field_name, (prefix, attr) in file_map.items():
                if field_name not in field_boleh_upload:
                    continue

                file_storage = request.files.get(field_name)
                if file_storage and file_storage.filename:
                    old_filename = getattr(berkas, attr)
                    filename = save_secure_upload(
                        file_storage,
                        upload_folder,
                        f'{prefix}_{calon_siswa.id}',
                        allowed_extensions,
                        current_app.config.get('PER_FILE_UPLOAD_LIMIT')
                    )
                    delete_uploaded_file(upload_folder, old_filename)
                    setattr(berkas, attr, filename)
                    ada_perubahan = True

        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('siswa.upload_berkas'))

        if ada_perubahan:
            berkas.status_verifikasi = Berkas.STATUS_BELUM
            berkas.catatan_verifikasi = None
            berkas.field_bermasalah = None
            berkas.tanggal_verifikasi = None
            berkas.tanggal_upload = datetime.utcnow()
            db.session.add(berkas)
            db.session.commit()
            flash('Berkas berhasil diupload, menunggu verifikasi admin.', 'success')
        else:
            flash('Tidak ada file yang dipilih', 'warning')

        return redirect(url_for('siswa.upload_berkas'))

    return render_template(
        'siswa/upload_berkas.html',
        berkas=berkas,
        upload_mode=upload_mode,
        field_boleh_upload=field_boleh_upload,
        is_image=is_image,
        is_pdf=is_pdf
    )


@siswa.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = current_user.calon_siswa
    berkas = calon_siswa.berkas if calon_siswa else None
    if not berkas:
        return 'File tidak ditemukan', 404

    allowed_files = {
        berkas.pas_foto,
        berkas.kartu_keluarga,
        berkas.akta_lahir,
        berkas.ijazah,
        berkas.ktp_orang_tua,
    }
    if filename not in allowed_files:
        return 'Akses Ditolak', 403

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@siswa.route('/ujian')
@login_required
def mulai_ujian():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = current_user.calon_siswa
    if not calon_siswa or not calon_siswa.sudah_lolos_administrasi():
        flash('Ujian hanya bisa diakses setelah data dan berkas Anda diverifikasi admin.', 'warning')
        return redirect(url_for('siswa.dashboard'))

    sesi = _next_sesi(calon_siswa)
    if sesi:
        return redirect(url_for('siswa.ujian', sesi_id=sesi.id))

    flash('Semua sesi ujian yang tersedia sudah selesai.', 'success')
    return redirect(url_for('siswa.hasil_ujian'))


@siswa.route('/ujian/<int:sesi_id>', methods=['GET', 'POST'])
@login_required
def ujian(sesi_id):
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = current_user.calon_siswa
    if not calon_siswa or not calon_siswa.sudah_lolos_administrasi():
        flash('Ujian hanya bisa diakses setelah data dan berkas Anda diverifikasi admin.', 'warning')
        return redirect(url_for('siswa.dashboard'))

    sesi = UjianSesi.query.get_or_404(sesi_id)
    if not sesi.aktif:
        flash('Sesi ujian ini belum aktif.', 'warning')
        return redirect(url_for('siswa.dashboard'))

    sesi_berikutnya = _next_sesi(calon_siswa)
    hasil = calon_siswa.get_hasil_ujian(sesi.id)

    if hasil and hasil.is_selesai():
        berikut = _next_sesi(calon_siswa)
        if berikut:
            return redirect(url_for('siswa.ujian', sesi_id=berikut.id))
        return redirect(url_for('siswa.hasil_ujian'))

    if sesi_berikutnya and sesi_berikutnya.id != sesi.id:
        flash('Silakan ikuti urutan sesi ujian.', 'warning')
        return redirect(url_for('siswa.ujian', sesi_id=sesi_berikutnya.id))

    daftar_soal = Soal.query.filter_by(sesi_id=sesi.id).order_by(Soal.urutan, Soal.id).all()
    if not daftar_soal:
        flash('Belum ada soal pada sesi ini. Silakan hubungi pihak sekolah.', 'warning')
        return render_template('siswa/ujian.html', daftar_soal=[], sesi=sesi, sesi_berikutnya=None)

    if request.method == 'POST':
        if not hasil:
            hasil = HasilUjian(
                calon_siswa_id=calon_siswa.id,
                sesi_id=sesi.id,
                waktu_mulai=datetime.utcnow()
            )
            db.session.add(hasil)
            db.session.flush()
        else:
            JawabanUjian.query.filter_by(hasil_ujian_id=hasil.id).delete()

        jumlah_benar = 0
        for soal in daftar_soal:
            jawaban_dipilih = request.form.get(f'soal_{soal.id}')
            benar = bool(jawaban_dipilih) and jawaban_dipilih == soal.jawaban_benar
            if benar:
                jumlah_benar += 1
            db.session.add(JawabanUjian(
                hasil_ujian_id=hasil.id,
                soal_id=soal.id,
                jawaban_dipilih=jawaban_dipilih,
                benar=benar
            ))

        hasil.jumlah_soal = len(daftar_soal)
        hasil.jumlah_benar = jumlah_benar
        hasil.nilai = round((jumlah_benar / len(daftar_soal)) * 100, 2)
        hasil.status = HasilUjian.STATUS_SELESAI
        hasil.waktu_selesai = datetime.utcnow()
        db.session.commit()

        berikut = _next_sesi(calon_siswa)
        if berikut:
            flash(f'Sesi {sesi.judul} selesai. Silakan lanjut ke {berikut.judul}.', 'success')
            return redirect(url_for('siswa.ujian', sesi_id=berikut.id))

        flash('Seluruh sesi ujian berhasil diselesaikan.', 'success')
        return redirect(url_for('siswa.hasil_ujian'))

    return render_template('siswa/ujian.html', daftar_soal=daftar_soal, sesi=sesi, sesi_berikutnya=sesi_berikutnya)


@siswa.route('/hasil-ujian')
@login_required
def hasil_ujian():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    calon_siswa = current_user.calon_siswa
    sesi_aktif = _sesi_aktif_dengan_soal()
    hasil_map = {}
    if calon_siswa:
        hasil_map = {hasil.sesi_id: hasil for hasil in calon_siswa.hasil_ujian if hasil.sesi_id}

    return render_template(
        'siswa/hasil_ujian.html',
        calon_siswa=calon_siswa,
        sesi_aktif=sesi_aktif,
        hasil_map=hasil_map,
        sesi_berikutnya=_next_sesi(calon_siswa) if calon_siswa else None
    )


@siswa.route('/pengumuman')
@login_required
def pengumuman():
    if current_user.role != 'siswa':
        return 'Akses Ditolak', 403

    return render_template('siswa/pengumuman.html', calon_siswa=current_user.calon_siswa)
