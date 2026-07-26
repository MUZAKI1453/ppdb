"""
Route unduh formulir PPDB — DISESUAIKAN dengan models asli repo MUZAKI1453/ppdb
(models/calon_siswa.py, alamat_siswa.py, data_ayah.py, data_ibu.py, data_wali.py,
berkas.py, user.py).

- /formulir/<id>/download          -> siswa & admin: 1 PDF formulir (Formulir A + B)
- /admin/formulir/bulk-download    -> admin: pilih beberapa id -> 1 file ZIP
- /admin/formulir/export-excel     -> admin: rekap SEMUA (atau id terpilih) -> 1 Excel

id di sini = CalonSiswa.id (bukan User.id).
"""
import io
import zipfile
from pathlib import Path
from datetime import datetime

import pandas as pd
from flask import Blueprint, send_file, request, abort, flash, redirect, url_for, current_app
from flask_login import login_required, current_user

from models.calon_siswa import CalonSiswa
from utils.formulir_reportlab import build_formulir_pdf

formulir_bp = Blueprint("formulir", __name__)

FORMULIR_TEMPLATE = "static/pdf/formulir_ppdb_template.pdf"


def _build_pdf_bytes(siswa: CalonSiswa) -> bytes:
    """Isi PDF formulir resmi memakai overlay ReportLab."""
    template_path = Path(current_app.root_path) / FORMULIR_TEMPLATE
    return build_formulir_pdf(siswa, template_path)


# ---------- 1) SISWA & ADMIN: unduh 1 formulir ----------
@formulir_bp.route("/formulir/<int:id>/download")
@login_required
def download_single(id):
    siswa = CalonSiswa.query.get_or_404(id)

    if current_user.role == "siswa" and siswa.user_id != current_user.id:
        abort(403)

    pdf_bytes = _build_pdf_bytes(siswa)
    filename = f"Formulir_{siswa.nama_lengkap.replace(' ', '_')}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


# ---------- 2) ADMIN: unduh banyak (checkbox) -> 1 ZIP ----------
@formulir_bp.route("/admin/formulir/bulk-download", methods=["POST"])
@login_required
def bulk_download():
    if current_user.role != "admin":
        abort(403)

    ids = request.form.getlist("siswa_ids")
    if not ids:
        flash("Tidak ada siswa yang dipilih!", "warning")
        return redirect(request.referrer or url_for('admin.calon_siswa'))

    siswa_list = CalonSiswa.query.filter(CalonSiswa.id.in_(ids)).all()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for siswa in siswa_list:
            pdf_bytes = _build_pdf_bytes(siswa)
            identitas = siswa.nisn or siswa.id
            fname = f"{identitas}_{siswa.nama_lengkap.replace(' ', '_')}.pdf"
            zf.writestr(fname, pdf_bytes)
    zip_buffer.seek(0)

    tanggal = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"Formulir_Terpilih_{tanggal}.zip",
    )


# ---------- 3) ADMIN: export rekap ke Excel ----------
@formulir_bp.route("/admin/formulir/export-excel", methods=["GET", "POST"])
@login_required
def export_excel():
    if current_user.role != "admin":
        abort(403)

    ids = request.form.getlist("siswa_ids") if request.method == "POST" else None
    query = CalonSiswa.query
    if ids:
        query = query.filter(CalonSiswa.id.in_(ids))
    siswa_list = query.all()

    rows = []
    for s in siswa_list:
        alamat = getattr(s, 'alamat', None)
        berkas = getattr(s, 'berkas', None)
        rows.append({
            "Nama Lengkap": s.nama_lengkap,
            "Jenis Kelamin": s.jenis_kelamin,
            "NISN": s.nisn,
            "NIK": s.nik,
            "Tempat, Tanggal Lahir": f"{s.tempat_lahir}, {s.tanggal_lahir}" if s.tanggal_lahir else s.tempat_lahir,
            "Agama": s.agama,
            "Alamat Jalan": alamat.alamat_jalan if alamat else "",
            "Desa/Kelurahan": alamat.desa_kelurahan if alamat else "",
            "Kecamatan": alamat.kecamatan if alamat else "",
            "Kabupaten": alamat.kabupaten if alamat else "",
            "Asal Sekolah": s.asal_sekolah,
            "No HP": s.no_hp,
            "Status Verifikasi Data": getattr(s, 'status_verifikasi', '-'),
            "Status Kelulusan": getattr(s, 'status_kelulusan', '-'),
            "Status Verifikasi Berkas": berkas.status_verifikasi if berkas else "-",
        })

    df = pd.DataFrame(rows)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Rekap Pendaftar")
    excel_buffer.seek(0)

    tanggal = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Rekap_Pendaftar_{tanggal}.xlsx",
    )