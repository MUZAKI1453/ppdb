import os
import uuid

from werkzeug.utils import secure_filename


IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
PDF_EXTENSIONS = {'pdf'}


def get_extension(filename):
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename, allowed_extensions):
    return get_extension(filename) in set(allowed_extensions or [])


def format_file_size(size_bytes):
    if not size_bytes:
        return '0 MB'
    mb = size_bytes / (1024 * 1024)
    if mb >= 1:
        return f'{mb:.0f} MB' if mb.is_integer() else f'{mb:.1f} MB'
    kb = size_bytes / 1024
    return f'{kb:.0f} KB'


def get_upload_size(file_storage):
    stream = getattr(file_storage, 'stream', None)
    if stream is None:
        return getattr(file_storage, 'content_length', 0) or 0

    try:
        current_position = stream.tell()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(current_position)
        return size
    except (AttributeError, OSError):
        return getattr(file_storage, 'content_length', 0) or 0


def is_image(filename):
    return get_extension(filename) in IMAGE_EXTENSIONS


def is_pdf(filename):
    return get_extension(filename) in PDF_EXTENSIONS


def save_secure_upload(file_storage, upload_folder, prefix, allowed_extensions, max_size_bytes=None):
    """Validasi dan simpan upload ke folder non-static.

    Ukuran divalidasi per file agar beberapa dokumen bisa dikirim sekaligus
    tanpa memakai batas total request sebagai aturan utama.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError('File belum dipilih.')

    original_name = secure_filename(file_storage.filename)
    ext = get_extension(original_name)

    if not ext or not allowed_file(original_name, allowed_extensions):
        daftar = ', '.join(sorted(allowed_extensions or []))
        raise ValueError(f'Format file tidak diizinkan. Gunakan: {daftar}.')

    if max_size_bytes:
        file_size = get_upload_size(file_storage)
        if file_size > max_size_bytes:
            raise ValueError(
                f'Ukuran file {original_name} terlalu besar. Maksimal {format_file_size(max_size_bytes)} per file.'
            )

    safe_prefix = secure_filename(prefix or 'upload') or 'upload'
    filename = f'{safe_prefix}_{uuid.uuid4().hex}.{ext}'

    os.makedirs(upload_folder, exist_ok=True)
    file_storage.save(os.path.join(upload_folder, filename))
    return filename


def delete_uploaded_file(upload_folder, filename):
    if not filename:
        return False

    safe_name = os.path.basename(filename)
    path = os.path.join(upload_folder, safe_name)

    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError:
        return False

    return False
