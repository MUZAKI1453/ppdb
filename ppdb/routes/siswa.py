from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import uuid, os
from datetime import datetime
from models.calon_siswa import CalonSiswa
from extensions_db import db
from models.berkas import Berkas
from werkzeug.utils import secure_filename
from flask_login import (
    login_required,
    current_user
)

siswa = Blueprint(
    'siswa',
    __name__,
    url_prefix='/siswa'
)


# ==================================================
# Dashboard Siswa
# URL : /siswa/dashboard
# ==================================================
@siswa.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = CalonSiswa.query.filter_by(
        user_id=current_user.id
    ).first()

    berkas = None

    progress = 25

    status_data = "Belum Mengisi"

    status_berkas = "Belum Upload"

    if calon_siswa:

        progress = 50

        status_data = "Menunggu Verifikasi"

        if calon_siswa.status_verifikasi == "Diverifikasi":
            status_data = "Diverifikasi"

        berkas = Berkas.query.filter_by(
            calon_siswa_id=calon_siswa.id
        ).first()

        if berkas:

            progress = 75

            status_berkas = "Menunggu Verifikasi"

            if berkas.status_verifikasi == Berkas.STATUS_DITOLAK:

                status_berkas = "Ditolak"

            elif berkas.status_verifikasi == "Diverifikasi":

                progress = 100

                status_berkas = "Diverifikasi"

    return render_template(
        'siswa/dashboard.html',
        progress=progress,
        status_data=status_data,
        status_berkas=status_berkas,
        berkas=berkas
    )


# ==================================================
# Formulir PPDB
# URL : /siswa/formulir
# ==================================================
@siswa.route(
    '/formulir',
    methods=['GET', 'POST']
)
@login_required
def formulir():
    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = CalonSiswa.query.filter_by(
        user_id=current_user.id
    ).first()

    # ===================================
    # SIMPAN DATA
    # ===================================

    if request.method == 'POST':

        if not calon_siswa:
            calon_siswa = CalonSiswa(
                user_id=current_user.id
            )

            db.session.add(calon_siswa)

        calon_siswa.nama_lengkap = request.form.get(
            'nama_lengkap'
        )

        calon_siswa.nisn = request.form.get(
            'nisn'
        )

        calon_siswa.nik = request.form.get(
            'nik'
        )

        calon_siswa.jenis_kelamin = request.form.get(
            'jenis_kelamin'
        )

        calon_siswa.alamat = request.form.get(
            'alamat'
        )

        calon_siswa.no_hp = request.form.get(
            'no_hp'
        )

        calon_siswa.email = request.form.get(
            'email'
        )

        calon_siswa.nama_ayah = request.form.get(
            'nama_ayah'
        )

        calon_siswa.nama_ibu = request.form.get(
            'nama_ibu'
        )

        calon_siswa.asal_sekolah = request.form.get(
            'asal_sekolah'
        )

        calon_siswa.tahun_lulus = request.form.get(
            'tahun_lulus'
        )

        calon_siswa.tempat_lahir = request.form.get(
            'tempat_lahir'
        )

        if request.form.get('tanggal_lahir'):
            calon_siswa.tanggal_lahir = datetime.strptime(
                request.form.get('tanggal_lahir'),
                '%Y-%m-%d'
            ).date()

        calon_siswa.agama = request.form.get(
            'agama'
        )

        calon_siswa.pekerjaan_ayah = request.form.get(
            'pekerjaan_ayah'
        )

        calon_siswa.pekerjaan_ibu = request.form.get(
            'pekerjaan_ibu'
        )

        calon_siswa.no_hp_ortu = request.form.get(
            'no_hp_ortu'
        )

        db.session.commit()

        flash(
            'Data berhasil disimpan',
            'success'
        )

        return redirect(
            url_for('siswa.formulir')
        )

    return render_template(
        'siswa/formulir.html',
        calon_siswa=calon_siswa
    )


# ==================================================
# Upload Berkas
# URL : /siswa/upload-berkas
# ==================================================
@siswa.route(
    '/upload-berkas',
    methods=['GET', 'POST']
)
@login_required
def upload_berkas():

    if current_user.role != 'siswa':
        return "Akses Ditolak", 403

    calon_siswa = current_user.calon_siswa

    if not calon_siswa:

        flash(
            'Isi formulir PPDB terlebih dahulu',
            'danger'
        )

        return redirect(
            url_for('siswa.formulir')
        )

    berkas = Berkas.query.filter_by(
        calon_siswa_id=calon_siswa.id
    ).first()

    if request.method == 'POST':

        ada_perubahan = False

        upload_folder = current_app.config[
            'UPLOAD_FOLDER'
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        pas_foto = request.files.get(
            'pas_foto'
        )

        kartu_keluarga = request.files.get(
            'kartu_keluarga'
        )

        akta_lahir = request.files.get(
            'akta_lahir'
        )

        ijazah = request.files.get(
            'ijazah'
        )

        # ==================================
        # Buat record jika belum ada
        # ==================================
        if not berkas:

            berkas = Berkas(
                calon_siswa_id=calon_siswa.id
            )

        # ==================================
        # PAS FOTO
        # ==================================
        if pas_foto and pas_foto.filename:

            ext = os.path.splitext(
                secure_filename(
                    pas_foto.filename
                )
            )[1]

            filename = (
                f"pasfoto_"
                f"{calon_siswa.id}_"
                f"{uuid.uuid4().hex}"
                f"{ext}"
            )

            pas_foto.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            berkas.pas_foto = filename

            ada_perubahan = True

        # ==================================
        # KARTU KELUARGA
        # ==================================
        if kartu_keluarga and kartu_keluarga.filename:

            ext = os.path.splitext(
                secure_filename(
                    kartu_keluarga.filename
                )
            )[1]

            filename = (
                f"kk_"
                f"{calon_siswa.id}_"
                f"{uuid.uuid4().hex}"
                f"{ext}"
            )

            kartu_keluarga.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            berkas.kartu_keluarga = filename

            ada_perubahan = True

        # ==================================
        # AKTA LAHIR
        # ==================================
        if akta_lahir and akta_lahir.filename:

            ext = os.path.splitext(
                secure_filename(
                    akta_lahir.filename
                )
            )[1]

            filename = (
                f"akta_"
                f"{calon_siswa.id}_"
                f"{uuid.uuid4().hex}"
                f"{ext}"
            )

            akta_lahir.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            berkas.akta_lahir = filename

            ada_perubahan = True

        # ==================================
        # IJAZAH
        # ==================================
        if ijazah and ijazah.filename:

            ext = os.path.splitext(
                secure_filename(
                    ijazah.filename
                )
            )[1]

            filename = (
                f"ijazah_"
                f"{calon_siswa.id}_"
                f"{uuid.uuid4().hex}"
                f"{ext}"
            )

            ijazah.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            berkas.ijazah = filename

            ada_perubahan = True

        # ==================================
        # SIMPAN JIKA ADA PERUBAHAN
        # ==================================
        if ada_perubahan:

            berkas.status_verifikasi = (
                Berkas.STATUS_BELUM
            )

            berkas.catatan_verifikasi = None

            berkas.tanggal_verifikasi = None

            berkas.tanggal_upload = (
                datetime.utcnow()
            )

            db.session.add(berkas)

            db.session.commit()

            flash(
                'Berkas berhasil diupload',
                'success'
            )

        else:

            flash(
                'Tidak ada file yang dipilih',
                'warning'
            )

        return redirect(
            url_for('siswa.upload_berkas')
        )

    return render_template(
        'siswa/upload_berkas.html',
        berkas=berkas
    )