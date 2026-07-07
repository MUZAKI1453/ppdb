from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

from extensions_db import db
from models.user import User
from models.calon_siswa import CalonSiswa


auth = Blueprint('auth', __name__)


@auth.route('/')
def home():
    return render_template('index.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nisn = (request.form.get('nisn') or '').strip()
        nama_lengkap = (request.form.get('nama_lengkap') or '').strip()
        password = request.form.get('password') or ''

        if not nisn or not nama_lengkap or not password:
            flash('NISN, nama lengkap, dan password wajib diisi.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if User.query.filter_by(username=nisn).first() or CalonSiswa.query.filter_by(nisn=nisn).first():
            flash('NISN sudah terdaftar. Silakan login atau hubungi admin.', 'warning')
            return render_template('auth/register.html', form_data=request.form)

        user = User(
            username=nisn,
            password=generate_password_hash(password),
            role='siswa'
        )
        db.session.add(user)
        db.session.flush()

        calon_siswa = CalonSiswa(
            user_id=user.id,
            nisn=nisn,
            nama_lengkap=nama_lengkap
        )
        db.session.add(calon_siswa)
        db.session.commit()

        flash('Registrasi berhasil. Silakan login menggunakan NISN.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = (request.form.get('login_id') or request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        user = User.query.filter_by(username=login_id).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

            return redirect(url_for('siswa.dashboard'))

        flash('NISN/Username atau password salah.', 'danger')

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
