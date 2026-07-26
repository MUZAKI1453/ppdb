"""Generator PDF formulir PPDB berbasis overlay ReportLab.

PDF kosong resmi dipakai sebagai background. ReportLab hanya menuliskan data
ke posisi kotak yang sudah ada, lalu pypdf menggabungkan overlay dengan template.
Dengan begitu layout tidak bergantung pada HTML/CSS atau pagination otomatis.
"""
from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0
FONT_NAME = "Times-Roman"
FONT_SIZE = 8.2
EXTENSION_TARGET_COUNT = 24
EXTENSION_LINE_WIDTH = 0.65
EXTENSION_TOP_OFFSET = 0.25

AGAMA_KODE = {
    "islam": "01",
    "kristen": "02",
    "protestan": "02",
    "kristen protestan": "02",
    "katolik": "03",
    "katholik": "03",
    "hindu": "04",
    "budha": "05",
    "buddha": "05",
    "khonghucu": "06",
    "konghucu": "06",
    "khong hu chu": "06",
}
STATUS_TINGGAL_KODE = {
    "bersama orang tua": "1",
    "orang tua": "1",
    "wali": "2",
    "kos": "3",
    "asrama": "4",
    "panti asuhan": "5",
    "pesantren": "6",
    "lainnya": "9",
    "lain-lain": "9",
}
MODA_KODE = {
    "jalan kaki": "01",
    "kendaraan umum": "02",
    "angkutan umum": "02",
    "kendaraan pribadi": "03",
}
PENDIDIKAN_KODE = {
    "sd": "01",
    "sd/sederajat": "01",
    "smp": "02",
    "smp/sederajat": "02",
    "sma": "03",
    "sma/sederajat": "03",
    "d1": "04",
    "d2": "05",
    "d3": "06",
    "s1": "07",
    "s2": "08",
    "s3": "09",
}

# Format tuple: (x kiri, top dari halaman, jumlah kotak, lebar kotak, tinggi kotak)
BoxRow = tuple[float, float, int, float, float]


def _value(obj: Any, attr: str, default: Any = "") -> Any:
    if obj is None:
        return default
    result = getattr(obj, attr, default)
    return default if result is None else result


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    # Font standar ReportLab memakai WinAnsi. Karakter yang tidak tersedia
    # diganti agar proses unduh PDF tidak gagal karena input pengguna.
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", _clean_text(value))


def _kode(mapping: dict[str, str], value: Any) -> str:
    normalized = _clean_text(value).lower()
    if not normalized:
        return ""
    if normalized in mapping:
        return mapping[normalized]
    for label, code in mapping.items():
        if label in normalized:
            return code
    return ""


def _angka(value: Any) -> str:
    match = re.search(r"\d+", _clean_text(value))
    return match.group() if match else ""


def _extract_waktu(value: Any) -> tuple[str, str]:
    text = _clean_text(value)
    if not text:
        return "", ""

    jam_match = re.search(r"(\d+)\s*(?:jam|j)\b", text, re.IGNORECASE)
    menit_match = re.search(r"(\d+)\s*(?:menit|mnt|min)\b", text, re.IGNORECASE)

    jam = jam_match.group(1) if jam_match else ""
    menit = menit_match.group(1) if menit_match else ""

    # Nilai tunggal pada formulir lama dianggap menit.
    if not jam and not menit:
        digit = re.search(r"\d+", text)
        if digit:
            menit = digit.group()

    return jam, menit


def _date_parts(value: Any) -> tuple[str, str, str]:
    if not value:
        return "", "", ""
    return f"{value.day:02d}", f"{value.month:02d}", f"{value.year:04d}"


def _penghasilan_kode(value: Any) -> str:
    text = _clean_text(value).lower()
    if not text:
        return ""

    compact = re.sub(r"\s+", " ", text)
    if "tidak" in compact and "penghasilan" in compact:
        return "7"
    if compact.startswith("<") or "kurang" in compact:
        return "1"
    if compact.startswith(">") or "lebih dari 20" in compact or "di atas 20" in compact:
        return "6"
    if "500" in compact and "999" in compact:
        return "2"
    if ("1 juta" in compact or "1jt" in compact) and ("1.999" in compact or "1999" in compact):
        return "3"
    if ("2 juta" in compact or "2jt" in compact) and ("4.999" in compact or "4999" in compact):
        return "4"
    if ("5 juta" in compact or "5jt" in compact) and "20" in compact:
        return "5"

    # Dukungan input nominal tunggal, misalnya Rp 3.000.000.
    number_text = re.sub(r"[^0-9]", "", compact)
    if number_text:
        amount = int(number_text)
        if amount < 500_000:
            return "1"
        if amount < 1_000_000:
            return "2"
        if amount < 2_000_000:
            return "3"
        if amount < 5_000_000:
            return "4"
        if amount <= 20_000_000:
            return "5"
        return "6"
    return ""


def _baseline(top: float, height: float, font_name: str, font_size: float) -> float:
    center_y = PAGE_HEIGHT - top - (height / 2)
    ascent = pdfmetrics.getAscent(font_name, font_size)
    descent = pdfmetrics.getDescent(font_name, font_size)
    return center_y - ((ascent + descent) / 2)


def _draw_box_chars(
    canvas: Canvas,
    value: Any,
    rows: Sequence[BoxRow],
    *,
    font_size: float = FONT_SIZE,
) -> None:
    text = _clean_text(value)
    offset = 0
    canvas.setFont(FONT_NAME, font_size)

    for x, top, count, cell_width, cell_height in rows:
        baseline = _baseline(top, cell_height, FONT_NAME, font_size)
        for index in range(count):
            text_index = offset + index
            if text_index >= len(text):
                return
            center_x = x + (index + 0.5) * cell_width
            canvas.drawCentredString(center_x, baseline, text[text_index])
        offset += count


def _draw_box_extensions(
    canvas: Canvas,
    rows: Sequence[BoxRow],
    *,
    target_counts: Sequence[int],
) -> None:
    """Lanjutkan kotak template hanya saat isi melebihi kapasitas aslinya."""
    canvas.saveState()
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(EXTENSION_LINE_WIDTH)
    canvas.setLineCap(0)
    canvas.setLineJoin(0)

    for row, target_count in zip(rows, target_counts):
        x, top, count, cell_width, cell_height = row
        additional = target_count - count
        if additional <= 0:
            continue

        left = x + (count * cell_width)
        right = left + (additional * cell_width)
        adjusted_top = top + EXTENSION_TOP_OFFSET
        bottom = PAGE_HEIGHT - adjusted_top - cell_height
        top_y = bottom + cell_height

        canvas.line(left, bottom, right, bottom)
        canvas.line(left, top_y, right, top_y)

        # Sisi kiri memakai garis kanan kotak asli, jadi tidak digambar ulang.
        for divider in range(1, additional + 1):
            divider_x = left + (divider * cell_width)
            canvas.line(divider_x, bottom, divider_x, top_y)

    canvas.restoreState()


def _draw_extended_box_chars(
    canvas: Canvas,
    value: Any,
    rows: Sequence[BoxRow],
    *,
    max_count: int = EXTENSION_TARGET_COUNT,
    font_size: float = FONT_SIZE,
) -> None:
    text = _clean_text(value)
    remaining = len(text)
    target_counts: list[int] = []

    for _x, _top, original_count, _cell_width, _cell_height in rows:
        # Baris hanya diperpanjang bila sisa karakter tidak muat di kotak asli.
        target_count = min(max(original_count, remaining), max_count)
        target_counts.append(target_count)
        remaining = max(0, remaining - target_count)

    _draw_box_extensions(canvas, rows, target_counts=target_counts)

    dynamic_rows = [
        (x, top, target_count, cell_width, cell_height)
        for (x, top, _count, cell_width, cell_height), target_count
        in zip(rows, target_counts)
    ]
    _draw_box_chars(canvas, text, dynamic_rows, font_size=font_size)


def _draw_image_contain(
    canvas: Canvas,
    image_path: Path,
    *,
    x: float,
    y: float,
    max_width: float,
    max_height: float,
) -> None:
    """Gambar logo di dalam area tanpa mengubah rasio aslinya."""
    if not image_path.is_file():
        return

    image = ImageReader(str(image_path))
    image_width, image_height = image.getSize()
    scale = min(max_width / image_width, max_height / image_height)
    width = image_width * scale
    height = image_height * scale

    canvas.drawImage(
        image,
        x + ((max_width - width) / 2),
        y + ((max_height - height) / 2),
        width=width,
        height=height,
        preserveAspectRatio=True,
        mask="auto",
    )


def _draw_smp_letterhead(canvas: Canvas, static_dir: Path) -> None:
    """Tutup KOP lama dan gambar KOP SMP memakai logo dari folder static."""
    canvas.saveState()

    # Area ini berhenti sebelum banner kuning FORMULIR PESERTA DIDIK.
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setStrokeColorRGB(1, 1, 1)
    canvas.rect(18.0, 696.0, PAGE_WIDTH - 36.0, 90.0, stroke=0, fill=1)

    _draw_image_contain(
        canvas,
        static_dir / "img" / "logo.png",
        x=62.0,
        y=700.0,
        max_width=46.0,
        max_height=50.0,
    )
    _draw_image_contain(
        canvas,
        static_dir / "img" / "logo_yayasan.png",
        x=503.0,
        y=700.0,
        max_width=48.0,
        max_height=52.0,
    )

    center_x = PAGE_WIDTH / 2
    canvas.setFillColorRGB(0, 0, 0)
    canvas.setFont("Times-Bold", 11.0)
    canvas.drawCentredString(
        center_x,
        733.0,
        "YAYASAN PENDIDIKAN ISLAM BAITUSSALAM",
    )
    canvas.setFont("Times-Bold", 15.0)
    canvas.drawCentredString(
        center_x,
        715.0,
        "SMP ISLAM PLUS BAITUSSALAM KUNINGAN",
    )
    canvas.setFont("Times-Roman", 6.8)
    canvas.drawCentredString(
        center_x,
        703.0,
        (
            "Jl. Ir. Soekarno (Jalan Baru), Blok Cikedung Rt.02 Rw.01 "
            "Kel. Cirendang Kec. Kuningan - Kuningan"
        ),
    )
    canvas.restoreState()


def _draw_x(canvas: Canvas, x: float, top: float, width: float, height: float) -> None:
    font_size = 9.0
    canvas.setFont(FONT_NAME, font_size)
    canvas.drawCentredString(
        x + width / 2,
        _baseline(top, height, FONT_NAME, font_size),
        "X",
    )


def _draw_date(
    canvas: Canvas,
    value: Any,
    day_row: BoxRow,
    month_row: BoxRow,
    year_row: BoxRow,
) -> None:
    day, month, year = _date_parts(value)
    _draw_box_chars(canvas, day, [day_row])
    _draw_box_chars(canvas, month, [month_row])
    _draw_box_chars(canvas, year, [year_row])


def _draw_page_one(
    canvas: Canvas,
    siswa: Any,
    printed_on: date,
    static_dir: Path,
) -> None:
    _draw_smp_letterhead(canvas, static_dir)
    alamat = _value(siswa, "alamat", None)

    # Tanggal cetak di bagian paling atas.
    _draw_date(
        canvas,
        printed_on,
        (106.32, 123.60, 2, 14.88, 12.96),
        (150.96, 123.60, 2, 14.88, 12.96),
        (195.60, 123.60, 4, 14.88, 12.96),
    )

    _draw_box_chars(
        canvas,
        _value(siswa, "nama_lengkap"),
        [
            (195.60, 158.52, 22, 14.88, 12.96),
            (195.60, 171.48, 20, 14.88, 12.96),
        ],
    )

    gender = _clean_text(_value(siswa, "jenis_kelamin")).lower()
    if "laki" in gender or gender in {"l", "male"}:
        _draw_x(canvas, 195.60, 197.40, 14.88, 12.96)
    elif "perempuan" in gender or gender in {"p", "female"}:
        _draw_x(canvas, 255.12, 197.40, 14.88, 12.96)

    _draw_box_chars(canvas, _digits(_value(siswa, "nisn")), [(195.60, 214.68, 11, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(siswa, "nik")), [(195.60, 236.28, 16, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(siswa, "tempat_lahir"), [(195.60, 258.24, 13, 14.88, 12.96)])
    _draw_date(
        canvas,
        _value(siswa, "tanggal_lahir", None),
        (195.60, 277.20, 2, 14.88, 12.96),
        (240.24, 277.20, 2, 14.88, 12.96),
        (284.88, 277.20, 4, 14.88, 12.96),
    )
    _draw_box_chars(canvas, _value(siswa, "no_registrasi_akta"), [(195.60, 295.68, 13, 14.88, 12.96)])
    _draw_box_chars(canvas, _kode(AGAMA_KODE, _value(siswa, "agama")), [(195.60, 318.48, 2, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(siswa, "kewarganegaraan"), [(195.60, 337.92, 13, 14.88, 12.96)])
    _draw_box_chars(
        canvas,
        _value(siswa, "kebutuhan_khusus"),
        [
            (195.60, 355.56, 19, 14.88, 12.96),
            (195.60, 368.52, 19, 14.88, 12.96),
        ],
    )
    _draw_extended_box_chars(canvas, _value(alamat, "alamat_jalan"), [(195.60, 386.64, 19, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(alamat, "dusun"), [(195.60, 403.44, 19, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(alamat, "rt")), [(195.60, 422.40, 3, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(alamat, "rw")), [(195.60, 441.36, 3, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(alamat, "desa_kelurahan"), [(195.60, 461.64, 19, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(alamat, "kecamatan"), [(195.60, 479.28, 19, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(alamat, "kabupaten"), [(195.60, 496.56, 19, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(alamat, "kode_pos")), [(195.60, 515.52, 6, 14.88, 12.96)])
    _draw_box_chars(canvas, _kode(STATUS_TINGGAL_KODE, _value(siswa, "status_tinggal")), [(195.60, 533.64, 1, 14.88, 12.96)])
    _draw_box_chars(canvas, _kode(MODA_KODE, _value(siswa, "moda_transportasi")), [(195.60, 552.12, 2, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(siswa, "anak_ke")), [(195.60, 569.76, 2, 14.88, 12.96)])
    _draw_extended_box_chars(canvas, _value(siswa, "asal_sekolah"), [(195.60, 587.04, 19, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(siswa, "tinggi_badan")), [(195.60, 606.00, 3, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(siswa, "berat_badan")), [(195.60, 624.12, 3, 14.88, 12.96)])
    _draw_box_chars(canvas, _angka(_value(siswa, "jarak_ke_sekolah")), [(195.60, 642.60, 3, 14.88, 12.96)])

    jam, menit = _extract_waktu(_value(siswa, "waktu_tempuh"))
    _draw_box_chars(canvas, jam, [(195.60, 661.56, 2, 14.88, 12.96)])
    _draw_box_chars(canvas, menit, [(255.12, 661.56, 2, 14.88, 12.96)])
    _draw_box_chars(canvas, _digits(_value(siswa, "jumlah_saudara_kandung")), [(195.60, 680.52, 2, 14.88, 12.96)])


def _draw_parent_section(canvas: Canvas, person: Any, rows: dict[str, Any]) -> None:
    _draw_box_chars(canvas, _value(person, "nama"), [rows["nama"]])
    _draw_box_chars(canvas, _digits(_value(person, "nik")), [rows["nik"]])
    _draw_box_chars(canvas, _value(person, "tempat_lahir"), [rows["tempat_lahir"]])
    _draw_date(canvas, _value(person, "tanggal_lahir", None), *rows["tanggal"])
    _draw_box_chars(canvas, _kode(PENDIDIKAN_KODE, _value(person, "pendidikan")), [rows["pendidikan"]])
    _draw_box_chars(canvas, _value(person, "pekerjaan"), [rows["pekerjaan"]])
    _draw_box_chars(canvas, _penghasilan_kode(_value(person, "penghasilan")), [rows["penghasilan"]])
    _draw_box_chars(canvas, _value(person, "kebutuhan_khusus"), rows["kebutuhan_khusus"])
    _draw_box_chars(canvas, _digits(_value(person, "no_hp")), [rows["no_hp"]])


def _parent_rows(section: str) -> dict[str, Any]:
    coordinates = {
        "ayah": {
            "nama": 149.76,
            "nik": 169.80,
            "tempat_lahir": 192.12,
            "pendidikan": 213.48,
            "pekerjaan": 240.84,
            "penghasilan": 264.96,
            "kebutuhan_1": 289.56,
            "kebutuhan_2": 303.24,
            "no_hp": 325.08,
        },
        "ibu": {
            "nama": 374.76,
            "nik": 394.80,
            "tempat_lahir": 416.16,
            "pendidikan": 438.00,
            "pekerjaan": 458.88,
            "penghasilan": 479.76,
            "kebutuhan_1": 500.28,
            "kebutuhan_2": 513.96,
            "no_hp": 533.04,
        },
        "wali": {
            "nama": 581.28,
            "nik": 601.80,
            "tempat_lahir": 623.16,
            "pendidikan": 644.04,
            "pekerjaan": 666.36,
            "penghasilan": 688.68,
            "kebutuhan_1": 709.56,
            "kebutuhan_2": 723.24,
            "no_hp": 745.08,
        },
    }
    top = coordinates[section]
    return {
        "nama": (190.80, top["nama"], 24, 15.36, 13.68),
        "nik": (190.80, top["nik"], 16, 15.36, 13.68),
        "tempat_lahir": (190.80, top["tempat_lahir"], 12, 15.36, 13.68),
        "tanggal": (
            (390.48, top["tempat_lahir"], 2, 15.36, 13.68),
            (436.56, top["tempat_lahir"], 2, 15.36, 13.68),
            (482.64, top["tempat_lahir"], 4, 15.36, 13.68),
        ),
        "pendidikan": (190.80, top["pendidikan"], 2, 15.36, 13.68),
        "pekerjaan": (190.80, top["pekerjaan"], 24, 15.36, 13.68),
        "penghasilan": (190.80, top["penghasilan"], 1, 15.36, 13.68),
        "kebutuhan_khusus": [
            (190.80, top["kebutuhan_1"], 24, 15.36, 13.68),
            (190.80, top["kebutuhan_2"], 24, 15.36, 13.68),
        ],
        "no_hp": (190.80, top["no_hp"], 12, 15.36, 13.68),
    }


def _draw_page_two(canvas: Canvas, siswa: Any) -> None:
    _draw_parent_section(canvas, _value(siswa, "ayah", None), _parent_rows("ayah"))
    _draw_parent_section(canvas, _value(siswa, "ibu", None), _parent_rows("ibu"))
    _draw_parent_section(canvas, _value(siswa, "wali", None), _parent_rows("wali"))


def _build_overlay(siswa: Any, printed_on: date, static_dir: Path) -> bytes:
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pageCompression=1)
    _draw_page_one(canvas, siswa, printed_on, static_dir)
    canvas.showPage()
    _draw_page_two(canvas, siswa)
    canvas.save()
    return buffer.getvalue()


def build_formulir_pdf(
    siswa: Any,
    template_path: str | Path,
    *,
    printed_on: date | None = None,
) -> bytes:
    """Gabungkan data siswa dengan PDF kosong resmi dan kembalikan bytes PDF."""
    template_path = Path(template_path)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template formulir tidak ditemukan: {template_path}")

    template = PdfReader(str(template_path))
    if len(template.pages) != 2:
        raise ValueError("Template formulir harus terdiri dari tepat 2 halaman")

    for page in template.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - PAGE_WIDTH) > 0.1 or abs(height - PAGE_HEIGHT) > 0.1:
            raise ValueError(
                f"Ukuran template harus {PAGE_WIDTH:g}x{PAGE_HEIGHT:g} pt, "
                f"ditemukan {width:g}x{height:g} pt"
            )

    static_dir = template_path.parent.parent
    overlay = PdfReader(
        io.BytesIO(
            _build_overlay(
                siswa,
                printed_on or date.today(),
                static_dir,
            )
        )
    )
    writer = PdfWriter()

    for template_page, overlay_page in zip(template.pages, overlay.pages):
        template_page.merge_page(overlay_page, over=True)
        writer.add_page(template_page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
