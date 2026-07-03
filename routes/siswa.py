from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import uuid, os
from datetime import datetime
from models.calon_siswa import CalonSiswa
from extensions_db import db
from models.berkas import Berkas
from werkzeug.utils import secure_filename
from models.alamat_siswa import AlamatSiswa
from models.data_ayah import DataAyah
from models.data_ibu import DataIbu
from models.data_wali import DataWali
from models.soal import Soal
from models.hasil_ujian import HasilUjian
from models.jawaban_ujian import JawabanUjian
from flask_login import login_required, current_user

siswa = Blueprint('siswa', __name__, url_prefix='/siswa')

# Daftar field wajib formulir PPDB (nama_field, label_error). Data wali tidak wajib.
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


def validasi_formulir(form):
    # Cek semua FIELD_WAJIB terisi, kembalikan list label yang kosong
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


def isi_data_dari_form(calon_siswa, form):
    # Isi seluruh field CalonSiswa + relasi (alamat/ayah/ibu/wali) dari form, belum commit

    # Data Pribadi Siswa
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

    # Data Alamat
    alamat = calon_siswa.alamat
    alamat.alamat_jalan = form.get('alamat_jalan')
    alamat.dusun = form.get('dusun')
    alamat.rt = form.get('rt')
    alamat.rw = form.get('rw')
    alamat.desa_kelurahan = form.get('desa_kelurahan')
    alamat.kecamatan = form.get('kecamatan')
    alamat.kabupaten = form.get('kabupaten')
    alamat.kode_pos = form.get('kode_pos')

    # Data Ayah
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

    # Data Ibu
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

    # Data Wali (opsional, hanya diisi jika wali_nama ada)
    wali_nama = form.get('wali_nama')
    if wali_nama and calon_siswa.wali:
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


# Dashboard Siswa -> /siswa/dashboard
@siswa.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = CalonSiswa.query.filter_by(user_id=current_user.id).first()
    berkas = None
    progress = 25
    status_data = "Belum Mengisi"
    status_berkas = "Belum Upload"
    status_seleksi = "Menunggu"
    boleh_ujian = False
    hasil_ujian = None
    status_ujian = {
        jenis: {'hasil': None, 'label': label}
        for jenis, label in Soal.JENIS_PILIHAN
    }

    if calon_siswa:
        progress = 50
        status_data = "Menunggu Verifikasi"

        if calon_siswa.status_verifikasi == "Diverifikasi":
            status_data = "Diverifikasi"
        elif calon_siswa.status_verifikasi == "Ditolak":
            status_data = "Ditolak"

        berkas = Berkas.query.filter_by(calon_siswa_id=calon_siswa.id).first()

        if berkas:
            progress = 75
            status_berkas = "Menunggu Verifikasi"

            if berkas.status_verifikasi == Berkas.STATUS_DITOLAK:
                status_berkas = "Ditolak"
            elif berkas.status_verifikasi == "Diverifikasi":
                progress = 100
                status_berkas = "Diverifikasi"

        boleh_ujian = calon_siswa.sudah_lolos_administrasi()

        for jenis in status_ujian:
            status_ujian[jenis]['hasil'] = calon_siswa.get_hasil_ujian(jenis)

        semua_selesai = calon_siswa.sudah_selesai_semua_ujian()
        ada_yang_selesai = any(
            v['hasil'] and v['hasil'].is_selesai()
            for v in status_ujian.values()
        )

        if semua_selesai:
            nilai_akhir = calon_siswa.nilai_akhir_ujian()
            status_seleksi = f"Nilai {nilai_akhir:g}"
        elif ada_yang_selesai:
            status_seleksi = "Sebagian Ujian Selesai"
        elif boleh_ujian:
            status_seleksi = "Siap Ujian"

        # hasil_ujian dipertahankan untuk kompatibilitas
        # lama pada template (dipakai untuk pewarnaan kartu),
        # dianggap "selesai" hanya jika kedua ujian selesai.
        hasil_ujian = status_ujian[Soal.JENIS_AKADEMIK]['hasil'] if semua_selesai else None

    return render_template(
        'siswa/dashboard.html',
        progress=progress,
        status_data=status_data,
        status_berkas=status_berkas,
        status_seleksi=status_seleksi,
        boleh_ujian=boleh_ujian,
        hasil_ujian=hasil_ujian,
        status_ujian=status_ujian,
        berkas=berkas,
        calon_siswa=calon_siswa
    )


# Detail Formulir Siswa -> /siswa/formulir
@siswa.route('/formulir', methods=['GET', 'POST'])
@login_required
def formulir():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = CalonSiswa.query.filter_by(user_id=current_user.id).first()
    is_locked = bool(calon_siswa and calon_siswa.status_verifikasi == 'Diverifikasi')

    # Siswa baru (belum punya data) otomatis dapat mode edit, tanpa perlu klik tombol dulu
    is_new = calon_siswa is None
    edit_mode = (is_new or request.args.get('edit') == 'true') and not is_locked

    if is_locked and request.method == 'POST':
        flash('Data sudah diverifikasi, tidak dapat diubah.', 'danger')
        return redirect(url_for('siswa.formulir'))

    if request.method == 'POST' and edit_mode:
        try:
            field_kosong = validasi_formulir(request.form)
            if field_kosong:
                flash('Mohon lengkapi: ' + ', '.join(field_kosong), 'danger')
                return render_template(
                    'siswa/formulir.html',
                    calon_siswa=calon_siswa,
                    is_locked=is_locked,
                    edit_mode=True,
                    form_data=request.form
                )

            if not calon_siswa:
                calon_siswa = CalonSiswa(user_id=current_user.id)
                db.session.add(calon_siswa)
                db.session.flush()

            # Pastikan relasi wajib sudah ada
            if not calon_siswa.alamat:
                calon_siswa.alamat = AlamatSiswa(calon_siswa_id=calon_siswa.id)
            if not calon_siswa.ayah:
                calon_siswa.ayah = DataAyah(calon_siswa_id=calon_siswa.id)
            if not calon_siswa.ibu:
                calon_siswa.ibu = DataIbu(calon_siswa_id=calon_siswa.id)

            # Wali dibuat/dihapus tergantung input
            if request.form.get('wali_nama'):
                if not calon_siswa.wali:
                    calon_siswa.wali = DataWali(calon_siswa_id=calon_siswa.id)
            elif calon_siswa.wali:
                db.session.delete(calon_siswa.wali)
                calon_siswa.wali = None

            isi_data_dari_form(calon_siswa, request.form)

            # Reset status verifikasi setiap kali data disimpan/diubah
            calon_siswa.status_verifikasi = 'Belum Diverifikasi'
            calon_siswa.catatan_verifikasi = None
            calon_siswa.tanggal_verifikasi = None

            db.session.commit()
            flash('Data berhasil disimpan', 'success')
            return redirect(url_for('siswa.formulir'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template(
        'siswa/formulir.html',
        calon_siswa=calon_siswa,
        is_locked=is_locked,
        edit_mode=edit_mode
    )


# Upload Berkas -> /siswa/upload-berkas
FIELD_BERKAS = ['pas_foto', 'kartu_keluarga', 'akta_lahir', 'ijazah', 'ktp_orang_tua']


@siswa.route('/upload-berkas', methods=['GET', 'POST'])
@login_required
def upload_berkas():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = current_user.calon_siswa
    if not calon_siswa:
        flash('Isi formulir PPDB terlebih dahulu', 'danger')
        return redirect(url_for('siswa.formulir'))

    berkas = Berkas.query.filter_by(calon_siswa_id=calon_siswa.id).first()

    # Tentukan mode akses upload
    if not berkas:
        upload_mode = 'baru'  # belum pernah upload -> semua field boleh
        field_boleh_upload = FIELD_BERKAS
    elif berkas.status_verifikasi == Berkas.STATUS_DITOLAK:
        upload_mode = 'revisi'  # hanya field yg ditandai admin
        field_boleh_upload = berkas.list_field_bermasalah
    else:
        # Belum Diverifikasi (menunggu) ATAU sudah Diverifikasi -> keduanya dikunci
        upload_mode = 'locked'
        field_boleh_upload = []

    if request.method == 'POST':

        if upload_mode == 'locked':
            flash('Berkas sedang menunggu/telah diverifikasi, tidak dapat diubah.', 'warning')
            return redirect(url_for('siswa.upload_berkas'))

        ada_perubahan = False
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        if not berkas:
            berkas = Berkas(calon_siswa_id=calon_siswa.id)

        file_map = {
            'pas_foto': ('pasfoto', 'pas_foto'),
            'kartu_keluarga': ('kk', 'kartu_keluarga'),
            'akta_lahir': ('akta', 'akta_lahir'),
            'ijazah': ('ijazah', 'ijazah'),
            'ktp_orang_tua': ('ktp', 'ktp_orang_tua'),
        }

        for field_name, (prefix, attr) in file_map.items():
            if field_name not in field_boleh_upload:
                continue  # skip dokumen yang tidak diizinkan diubah saat revisi

            f = request.files.get(field_name)
            if f and f.filename:
                ext = os.path.splitext(secure_filename(f.filename))[1]
                filename = f"{prefix}_{calon_siswa.id}_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_folder, filename))
                setattr(berkas, attr, filename)
                ada_perubahan = True

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
        field_boleh_upload=field_boleh_upload
    )


JENIS_UJIAN_VALID = [Soal.JENIS_AKADEMIK, Soal.JENIS_PSIKOTES]
LABEL_JENIS_UJIAN = dict(Soal.JENIS_PILIHAN)


# ==================================================
# Ujian Seleksi -> /siswa/ujian/<jenis>
#
# jenis: 'akademik' atau 'psikotes'. Keduanya adalah
# dua sesi ujian terpisah, masing-masing hanya bisa
# dikerjakan satu kali.
#
# Syarat mengerjakan:
# - Data pribadi & berkas sudah sama-sama Diverifikasi
# - Belum pernah menyelesaikan ujian jenis ini
# ==================================================
@siswa.route('/ujian/<jenis>', methods=['GET', 'POST'])
@login_required
def ujian(jenis):
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    if jenis not in JENIS_UJIAN_VALID:
        return "Jenis ujian tidak dikenal", 404

    calon_siswa = current_user.calon_siswa

    if not calon_siswa or not calon_siswa.sudah_lolos_administrasi():
        flash('Ujian hanya bisa diakses setelah data dan berkas Anda diverifikasi admin.', 'warning')
        return redirect(url_for('siswa.dashboard'))

    hasil = calon_siswa.get_hasil_ujian(jenis)

    if hasil and hasil.is_selesai():
        return redirect(url_for('siswa.hasil_ujian', jenis=jenis))

    daftar_soal = Soal.query.filter_by(jenis_ujian=jenis).order_by(Soal.id).all()

    if not daftar_soal:
        flash(f'Belum ada soal ujian {LABEL_JENIS_UJIAN[jenis]} yang tersedia. Silakan hubungi pihak sekolah.', 'warning')
        return render_template('siswa/ujian.html', daftar_soal=[], jenis=jenis, label_jenis=LABEL_JENIS_UJIAN[jenis])

    if request.method == 'POST':
        if not hasil:
            hasil = HasilUjian(
                calon_siswa_id=calon_siswa.id,
                jenis_ujian=jenis,
                waktu_mulai=datetime.utcnow()
            )
            db.session.add(hasil)
            db.session.flush()

        jumlah_benar = 0

        for soal in daftar_soal:
            jawaban_dipilih = request.form.get(f'soal_{soal.id}')
            benar = bool(jawaban_dipilih) and jawaban_dipilih == soal.jawaban_benar

            if benar:
                jumlah_benar += 1

            db.session.add(
                JawabanUjian(
                    hasil_ujian_id=hasil.id,
                    soal_id=soal.id,
                    jawaban_dipilih=jawaban_dipilih,
                    benar=benar
                )
            )

        hasil.jumlah_soal = len(daftar_soal)
        hasil.jumlah_benar = jumlah_benar
        hasil.nilai = round((jumlah_benar / len(daftar_soal)) * 100, 2)
        hasil.status = HasilUjian.STATUS_SELESAI
        hasil.waktu_selesai = datetime.utcnow()

        db.session.commit()

        flash(f'Ujian {LABEL_JENIS_UJIAN[jenis]} berhasil dikumpulkan.', 'success')
        return redirect(url_for('siswa.hasil_ujian', jenis=jenis))

    return render_template(
        'siswa/ujian.html',
        daftar_soal=daftar_soal,
        jenis=jenis,
        label_jenis=LABEL_JENIS_UJIAN[jenis]
    )


# ==================================================
# Hasil Ujian -> /siswa/hasil-ujian/<jenis>
# ==================================================
@siswa.route('/hasil-ujian/<jenis>')
@login_required
def hasil_ujian(jenis):
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    if jenis not in JENIS_UJIAN_VALID:
        return "Jenis ujian tidak dikenal", 404

    calon_siswa = current_user.calon_siswa
    hasil = calon_siswa.get_hasil_ujian(jenis) if calon_siswa else None

    return render_template(
        'siswa/hasil_ujian.html',
        hasil=hasil,
        jenis=jenis,
        label_jenis=LABEL_JENIS_UJIAN[jenis]
    )


# ==================================================
# Pengumuman Kelulusan -> /siswa/pengumuman
# ==================================================
@siswa.route('/pengumuman')
@login_required
def pengumuman():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = current_user.calon_siswa

    return render_template(
        'siswa/pengumuman.html',
        calon_siswa=calon_siswa
    )
