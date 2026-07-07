# ==================================================
# PARSER SOAL DARI FILE PDF
#
# Format PDF yang harus diikuti (per soal):
#
#   1. Ini adalah pertanyaan soal, boleh lebih
#      dari satu baris.
#   A. Pilihan jawaban A
#   B. Pilihan jawaban B
#   C. Pilihan jawaban C
#   D. Pilihan jawaban D
#   KUNCI: A
#   KATEGORI: Matematika        <- opsional
#
# Aturan:
# - Nomor soal harus berupa "1." "2." dst di awal baris
#   (menandai mulainya soal baru).
# - Pilihan harus diawali "A." "B." "C." "D." (boleh juga
#   "A)" "B)" dst) di awal baris.
# - Baris KUNCI: <huruf> wajib ada, menentukan jawaban benar.
# - Baris KATEGORI: <teks> opsional, kalau tidak ada maka
#   kategori memakai nilai default yang dipilih admin saat
#   upload (mis. "Matematika" untuk seluruh file).
# ==================================================

import re
import pdfplumber

NOMOR_SOAL_RE = re.compile(r'^\s*(\d+)[.)]\s*(.*)$')
PILIHAN_RE = re.compile(r'^\s*([A-Ea-e])[.)]\s*(.*)$')
KUNCI_RE = re.compile(r'^\s*(?:KUNCI|JAWABAN)\s*[:=]\s*([A-Ea-e])\s*$', re.IGNORECASE)
KATEGORI_RE = re.compile(r'^\s*KATEGORI\s*[:=]\s*(.+)$', re.IGNORECASE)


def extract_text_from_pdf(file_stream_or_path):
    """Ambil seluruh teks dari file PDF, urut per halaman."""
    teks_semua = []

    with pdfplumber.open(file_stream_or_path) as pdf:
        for page in pdf.pages:
            teks_halaman = page.extract_text() or ''
            teks_semua.append(teks_halaman)

    return '\n'.join(teks_semua)


def _tutup_blok(blok_lines, nomor, hasil, errors):
    """Parse satu blok baris (1 nomor soal) jadi dict soal."""
    if not blok_lines:
        return

    pertanyaan_lines = []
    pilihan = {}
    kunci = None
    kategori = None

    mode = 'pertanyaan'

    for line in blok_lines:
        m_pilihan = PILIHAN_RE.match(line)
        m_kunci = KUNCI_RE.match(line)
        m_kategori = KATEGORI_RE.match(line)

        if m_kunci:
            kunci = m_kunci.group(1).upper()
            mode = 'lain'
            continue

        if m_kategori:
            kategori = m_kategori.group(1).strip()
            mode = 'lain'
            continue

        if m_pilihan:
            huruf = m_pilihan.group(1).upper()
            isi = m_pilihan.group(2).strip()
            pilihan[huruf] = isi
            mode = 'pilihan'
            continue

        if line.strip() == '':
            continue

        # Baris lanjutan: nyambung ke pertanyaan atau ke
        # pilihan terakhir yang sedang diisi (soal/pilihan
        # yang teksnya lebih dari satu baris).
        if mode == 'pertanyaan':
            pertanyaan_lines.append(line.strip())
        elif mode == 'pilihan' and pilihan:
            huruf_terakhir = list(pilihan.keys())[-1]
            pilihan[huruf_terakhir] += ' ' + line.strip()

    pertanyaan = ' '.join(pertanyaan_lines).strip()

    masalah = []
    if not pertanyaan:
        masalah.append('pertanyaan kosong')
    for huruf in ['A', 'B', 'C', 'D']:
        if huruf not in pilihan or not pilihan[huruf].strip():
            masalah.append(f'pilihan {huruf} tidak ditemukan')
    if not kunci or kunci not in ['A', 'B', 'C', 'D', 'E']:
        masalah.append('baris KUNCI tidak valid/tidak ditemukan')
    elif kunci == 'E' and not pilihan.get('E'):
        masalah.append('kunci E dipilih tetapi pilihan E tidak ditemukan')

    if masalah:
        errors.append(f'Soal nomor {nomor}: {", ".join(masalah)}')
        return

    hasil.append({
        'nomor': nomor,
        'pertanyaan': pertanyaan,
        'pilihan_a': pilihan['A'],
        'pilihan_b': pilihan['B'],
        'pilihan_c': pilihan['C'],
        'pilihan_d': pilihan['D'],
        'pilihan_e': pilihan.get('E', ''),
        'jumlah_pilihan': 5 if pilihan.get('E') else 4,
        'jawaban_benar': kunci,
        'kategori': kategori,
    })


def parse_soal_text(teks):
    """
    Pecah teks hasil ekstraksi PDF menjadi daftar dict soal.
    Mengembalikan (daftar_soal, daftar_error).
    """
    baris_list = teks.split('\n')

    daftar_soal = []
    daftar_error = []

    blok_saat_ini = []
    nomor_saat_ini = None

    for line in baris_list:
        m_nomor = NOMOR_SOAL_RE.match(line)

        # Baris "N. ..." dianggap nomor soal baru HANYA jika
        # anka di awal <= 500 (menghindari salah tangkap poin
        # desimal / penomoran lain yang tidak relevan) dan
        # dulu blok sebelumnya sudah ada isinya.
        if m_nomor and int(m_nomor.group(1)) <= 500:
            if blok_saat_ini:
                _tutup_blok(blok_saat_ini, nomor_saat_ini, daftar_soal, daftar_error)

            nomor_saat_ini = int(m_nomor.group(1))
            sisa_teks = m_nomor.group(2)
            blok_saat_ini = [sisa_teks] if sisa_teks.strip() else []
            continue

        blok_saat_ini.append(line)

    if blok_saat_ini:
        _tutup_blok(blok_saat_ini, nomor_saat_ini, daftar_soal, daftar_error)

    return daftar_soal, daftar_error


def parse_soal_pdf(file_stream_or_path):
    """Entry point: dari file PDF -> (daftar_soal, daftar_error)."""
    teks = extract_text_from_pdf(file_stream_or_path)
    return parse_soal_text(teks)