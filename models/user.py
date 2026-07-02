from extensions_db import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    calon_siswa = db.relationship(
        'CalonSiswa',
        backref='user',
        uselist=False
    )