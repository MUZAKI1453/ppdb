# SPMB BTS

Sistem **SPMB BTS** adalah aplikasi web berbasis Flask untuk mengelola proses penerimaan calon siswa, mulai dari pendaftaran, pengisian formulir, upload berkas, verifikasi admin, ujian CBT, koreksi esai, sampai pengumuman hasil seleksi.

Project ini memiliki dua role utama:

- **Admin**: mengelola data calon siswa, verifikasi berkas, bank soal, jadwal ujian, hasil ujian, koreksi esai, dan hasil seleksi.
- **Calon Siswa**: registrasi akun, melengkapi data pendaftaran, upload berkas, mengikuti ujian SPMB, dan melihat pengumuman.

---

## Teknologi

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- SQLite
- Bootstrap Icons
- HTML, CSS, JavaScript
- pdfplumber untuk parsing/import soal dari PDF

---

## Struktur Folder

```text
.
├── app.py
├── config.py
├── extensions_db.py
├── requirements.txt
├── models/
│   ├── user.py
│   ├── calon_siswa.py
│   ├── berkas.py
│   ├── ujian_sesi.py
│   ├── soal.py
│   ├── hasil_ujian.py
│   ├── jawaban_ujian.py
│   └── pengaturan_ujian.py
├── routes/
│   ├── auth.py
│   ├── admin.py
│   └── siswa.py
├── static/
│   └── css/
├── templates/
│   ├── admin/
│   ├── auth/
│   ├── layouts/
│   ├── partials/
│   └── siswa/
└── utils/
    ├── soal_pdf_parser.py
    ├── soal_pdf_template_parser.py
    └── upload_helper.py
```

---

## Instalasi Lokal

### 1. Clone repository

```bash
git clone <url-repository>
cd <nama-folder-project>
```

### 2. Buat virtual environment

```bash
python -m venv venv
```

Aktifkan virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

### 4. Buat file `.env`

Buat file `.env` di root project:

```env
SECRET_KEY=secret-key
FLASK_DEBUG=false
DATABASE_URL=sqlite:///spmb.db
UPLOAD_FOLDER=instance/uploads
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ad123min
PER_FILE_UPLOAD_LIMIT=5242880
MAX_REQUEST_CONTENT_LENGTH=83886080
```

### 5. Jalankan aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di:

```text
http://localhost:5000
```

Saat aplikasi pertama kali dijalankan, tabel database akan dibuat otomatis. Jika `ADMIN_USERNAME` dan `ADMIN_PASSWORD` diisi pada `.env`, akun admin default juga akan dibuat otomatis.

---

## Alur Penggunaan

### Alur Admin

1. Login menggunakan akun admin.
2. Cek dashboard pendaftaran.
3. Kelola data calon siswa.
4. Verifikasi berkas pendaftaran.
5. Masuk ke menu **Bank Soal**.
6. Buat sesi ujian.
7. Tambahkan soal pilihan ganda dan/atau esai.
8. Atur jadwal global ujian SPMB.
9. Pantau hasil ujian per sesi.
10. Koreksi jawaban esai jika ada.
11. Tentukan hasil seleksi calon siswa.

### Alur Siswa

1. Registrasi akun siswa.
2. Login.
3. Lengkapi formulir pendaftaran.
4. Upload berkas persyaratan.
5. Menunggu verifikasi admin.
6. Buka halaman ujian SPMB.
7. Melihat jadwal ujian dan daftar sesi ujian.
8. Klik **Mulai Ujian** saat jadwal sudah terbuka.
9. Mengerjakan sesi ujian secara berurutan.
10. Setelah semua sesi selesai, siswa menunggu pengumuman hasil seleksi.