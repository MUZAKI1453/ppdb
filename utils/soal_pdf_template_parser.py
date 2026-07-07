"""Parser import soal PDF SPMB.

Mengikuti pola parser CBT Sekolah, lalu disesuaikan untuk template SPMB:

1. Pertanyaan PG 4 pilihan.
A. Opsi A
B. Opsi B
C. Opsi C
D. Opsi D
Jawaban: A

2. Pertanyaan PG 5 pilihan.
A. Opsi A
B. Opsi B
C. Opsi C
D. Opsi D
E. Opsi E
Jawaban: C

3. Pertanyaan esai.
Bobot: 20

Parser dibuat toleran terhadap hasil ekstraksi PDF yang sering menggabungkan
beberapa baris menjadi satu baris panjang.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Iterable, List, Tuple

import pdfplumber

NOMOR_SOAL_RE = re.compile(r"^\s*(\d{1,3})[.)]\s*(.*)$")
PILIHAN_RE = re.compile(r"^\s*([A-Ea-e])[.)]\s*(.*)$")
JAWABAN_LINE_RE = re.compile(r"^\s*(?:JAWABAN|KUNCI)\s*[:=]\s*([A-Ea-e])\s*$", re.IGNORECASE)
BOBOT_LINE_RE = re.compile(r"^\s*(?:BOBOT|POIN)\s*[:=]\s*(\d+)\s*$", re.IGNORECASE)
JAWABAN_INLINE_RE = re.compile(r"\(?\s*(?:JAWABAN|KUNCI)\s*[:=]\s*([A-Ea-e])\s*\)?", re.IGNORECASE)
BOBOT_INLINE_RE = re.compile(r"\(?\s*(?:BOBOT|POIN)\s*[:=]\s*(\d+)\s*\)?", re.IGNORECASE)
HEADER_RE = re.compile(r"^\s*TEMPLATE\s+IMPORT\s+SOAL\s+SPMB\s*$", re.IGNORECASE)
SKIP_PREFIX_RE = re.compile(r"^\s*(?:Petunjuk|Catatan)\b", re.IGNORECASE)


def extract_text_from_pdf(file_stream_or_path) -> str:
    teks_semua: List[str] = []
    with pdfplumber.open(file_stream_or_path) as pdf:
        for page in pdf.pages:
            teks_semua.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
    return "\n".join(teks_semua)


def _normalisasi_marker(teks: str) -> str:
    """Pisahkan marker nomor, opsi, Jawaban, dan Bobot ke baris sendiri."""
    teks = (teks or "").replace("\r\n", "\n").replace("\r", "\n")
    teks = re.sub(r"[\t\u00a0]+", " ", teks)

    # Jika header template dan soal pertama tersambung di satu baris.
    teks = re.sub(
        r"(TEMPLATE\s+IMPORT\s+SOAL\s+SPMB)\s+(?=\d{1,3}[.)]\s+)",
        r"\1\n",
        teks,
        flags=re.IGNORECASE,
    )

    # Metadata format CBT lama sering ditempel sebagai (Jawaban: A) / (Poin: 20).
    # Dinormalisasi dulu agar huruf A) di dalam metadata tidak dianggap opsi.
    teks = re.sub(
        r"\(\s*(Jawaban|Kunci)\s*[:=]\s*([A-Ea-e])\s*\)",
        lambda m: f"\n{m.group(1)}: {m.group(2).upper()}\n",
        teks,
        flags=re.IGNORECASE,
    )
    teks = re.sub(
        r"\(\s*(Bobot|Poin)\s*[:=]\s*(\d+)\s*\)",
        lambda m: f"\nBobot: {m.group(2)}\n",
        teks,
        flags=re.IGNORECASE,
    )

    # Nomor soal: 1. / 1)
    teks = re.sub(r"(?<!\n)(?<!\d)\s+(?=\d{1,3}[.)]\s+)", "\n", teks)
    # Pilihan A-E: A. / A)
    teks = re.sub(r"(?<!\n)\s+(?=[A-Ea-e][.)]\s+)", "\n", teks)
    # Jawaban/Kunci/Bobot/Poin.
    teks = re.sub(
        r"(?<!\n)\s+(?=(?:Jawaban|Kunci|Bobot|Poin)\s*[:=])",
        "\n",
        teks,
        flags=re.IGNORECASE,
    )
    return teks


def _bersihkan_baris(teks: str) -> List[str]:
    hasil: List[str] = []
    for raw in _normalisasi_marker(teks).split("\n"):
        line = raw.strip()
        if not line:
            continue
        if HEADER_RE.match(line) or SKIP_PREFIX_RE.match(line):
            continue
        if line.startswith("-"):
            continue
        hasil.append(line)
    return hasil


def _pecah_blok_soal(baris: Iterable[str]) -> List[Tuple[int, List[str]]]:
    blok: List[Tuple[int, List[str]]] = []
    nomor = None
    isi: List[str] = []

    for line in baris:
        match_nomor = NOMOR_SOAL_RE.match(line)
        if match_nomor:
            if nomor is not None and isi:
                blok.append((nomor, isi))
            nomor = int(match_nomor.group(1))
            sisa = match_nomor.group(2).strip()
            isi = [sisa] if sisa else []
            continue

        if nomor is not None:
            isi.append(line)

    if nomor is not None and isi:
        blok.append((nomor, isi))
    return blok


def _ambil_meta_dari_line(line: str) -> Tuple[str, str | None, int | None]:
    """Ambil Jawaban/Bobot dari baris, termasuk format inline CBT lama."""
    jawaban = None
    bobot = None

    match_jawaban = JAWABAN_INLINE_RE.search(line)
    if match_jawaban:
        jawaban = match_jawaban.group(1).upper()
        line = JAWABAN_INLINE_RE.sub("", line).strip()

    match_bobot = BOBOT_INLINE_RE.search(line)
    if match_bobot:
        bobot = int(match_bobot.group(1))
        line = BOBOT_INLINE_RE.sub("", line).strip()

    return line.strip(), jawaban, bobot


def _parse_blok(nomor: int, lines: List[str]) -> Tuple[Dict[str, Any] | None, str | None]:
    pertanyaan_lines: List[str] = []
    pilihan: Dict[str, str] = {}
    jawaban = ""
    bobot = 0
    last_state = "soal"
    opsi_terakhir = ""

    for raw_line in lines:
        line, inline_jawaban, inline_bobot = _ambil_meta_dari_line(raw_line)

        if inline_jawaban:
            jawaban = inline_jawaban
        if inline_bobot is not None:
            bobot = inline_bobot

        if not line:
            last_state = "meta" if (inline_jawaban or inline_bobot is not None) else last_state
            continue

        match_jawaban = JAWABAN_LINE_RE.match(line)
        if match_jawaban:
            jawaban = match_jawaban.group(1).upper()
            last_state = "meta"
            opsi_terakhir = ""
            continue

        match_bobot = BOBOT_LINE_RE.match(line)
        if match_bobot:
            bobot = int(match_bobot.group(1))
            last_state = "meta"
            opsi_terakhir = ""
            continue

        match_opsi = PILIHAN_RE.match(line)
        if match_opsi:
            opsi_terakhir = match_opsi.group(1).upper()
            pilihan[opsi_terakhir] = match_opsi.group(2).strip()
            last_state = opsi_terakhir
            continue

        if opsi_terakhir and last_state in ["A", "B", "C", "D", "E"]:
            pilihan[opsi_terakhir] = (pilihan.get(opsi_terakhir, "") + " " + line).strip()
        else:
            pertanyaan_lines.append(line)
            last_state = "soal"

    pertanyaan = " ".join(pertanyaan_lines).strip()
    if not pertanyaan:
        return None, f"Soal nomor {nomor}: pertanyaan kosong"

    punya_opsi = any((pilihan.get(h) or "").strip() for h in ["A", "B", "C", "D", "E"])

    if jawaban:
        jumlah_pilihan = 5 if pilihan.get("E") else 4
        wajib = ["A", "B", "C", "D"] + (["E"] if jumlah_pilihan == 5 else [])
        kurang = [h for h in wajib if not (pilihan.get(h) or "").strip()]
        if kurang:
            return None, f"Soal nomor {nomor}: pilihan {', '.join(kurang)} tidak ditemukan"
        if jawaban not in wajib:
            return None, f"Soal nomor {nomor}: jawaban {jawaban} tidak sesuai jumlah pilihan"

        return {
            "id": str(uuid.uuid4()),
            "nomor": nomor,
            "tipe_soal": "pg",
            "jumlah_pilihan": jumlah_pilihan,
            "pertanyaan": pertanyaan,
            "pilihan_a": pilihan.get("A", ""),
            "pilihan_b": pilihan.get("B", ""),
            "pilihan_c": pilihan.get("C", ""),
            "pilihan_d": pilihan.get("D", ""),
            "pilihan_e": pilihan.get("E", ""),
            "jawaban_benar": jawaban,
            "bobot": 0,
        }, None

    if bobot > 0:
        if punya_opsi:
            return None, f"Soal nomor {nomor}: pilihan ditemukan tetapi Jawaban belum diisi"

        return {
            "id": str(uuid.uuid4()),
            "nomor": nomor,
            "tipe_soal": "esai",
            "jumlah_pilihan": 0,
            "pertanyaan": pertanyaan,
            "pilihan_a": "",
            "pilihan_b": "",
            "pilihan_c": "",
            "pilihan_d": "",
            "pilihan_e": "",
            "jawaban_benar": "",
            "bobot": bobot,
        }, None

    return None, f"Soal nomor {nomor}: tambahkan Jawaban untuk PG atau Bobot untuk esai"


def parse_soal_text(teks: str):
    daftar_soal: List[Dict[str, Any]] = []
    errors: List[str] = []

    for nomor, lines in _pecah_blok_soal(_bersihkan_baris(teks or "")):
        soal, error = _parse_blok(nomor, lines)
        if soal:
            daftar_soal.append(soal)
        elif error:
            errors.append(error)

    if not daftar_soal and not errors:
        errors.append("Tidak ada soal yang terdeteksi. Pastikan nomor soal memakai format 1., 2., dan seterusnya.")

    return daftar_soal, errors


def parse_soal_pdf(file_stream_or_path):
    return parse_soal_text(extract_text_from_pdf(file_stream_or_path))
