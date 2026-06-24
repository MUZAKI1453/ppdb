from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user

from extensions_db import db
from models.user import User


# ==================================================
# Blueprint Authentication
# ==================================================
auth = Blueprint(
    'auth',
    __name__
)


# ==================================================
# HOME
# URL    : /
# METHOD : GET
#
# Fungsi:
# - Halaman utama website PPDB
# ==================================================
@auth.route('/')
def home():

    return render_template('index.html')


# ==================================================
# REGISTER
# URL    : /register
# METHOD : GET, POST
#
# Fungsi:
# - Registrasi akun calon siswa
# ==================================================
@auth.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cek_user = User.query.filter_by(
            username=username
        ).first()

        if cek_user:
            flash('Username sudah digunakan')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            role='siswa'
        )

        db.session.add(user)
        db.session.commit()

        flash('Registrasi berhasil')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ==================================================
# LOGIN
# URL    : /login
# METHOD : GET, POST
#
# Fungsi:
# - Login user
# - Redirect sesuai role
# ==================================================
@auth.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        print("================================")
        print("USERNAME :", username)
        print("USER :", user)

        if user:
            print("ROLE :", user.role)
            print(
                "PASSWORD VALID :",
                check_password_hash(
                    user.password,
                    password
                )
            )

        if user and check_password_hash(
            user.password,
            password
        ):

            print("LOGIN BERHASIL")

            login_user(user)

            if user.role == 'admin':
                return redirect('/admin/dashboard')

            return redirect('/siswa/dashboard')

        flash('Username atau Password salah')

    return render_template('auth/login.html')


# ==================================================
# LOGOUT
# URL    : /logout
# METHOD : GET
#
# Fungsi:
# - Menghapus session login
# ==================================================
@auth.route('/logout')
def logout():

    logout_user()

    return redirect(url_for('auth.login'))