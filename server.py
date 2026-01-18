# server/server.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Используем PostgreSQL на Render, SQLite локально
if os.getenv("RENDER"):
    # На Render.com
    DATABASE_URL = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    # Локально
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///licenses.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class LicenseKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    duration_days = db.Column(db.Float, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(100), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)

_initialized = False

@app.before_request
def initialize_db():
    global _initialized
    if not _initialized:
        db.create_all()
        # Проверяем, есть ли уже ключи
        if LicenseKey.query.count() == 0:
            keys = [
                ("W1K7-9FqR-2mN-pL8s", 7),
                ("X3Y9-KpT4-8vB-nM2d", 7),
                ("Z5A2-LwE6-4cX-qR9f", 7),
                ("B7C4-MnU8-1zY-tV3g", 7),
                ("D9E6-PoI2-5aS-hJ7k", 7),
                ("M1N3-ThG5-9bV-cX4r", 30),
                ("H1R5-JkL9-3mQ-wE8t", 0.0417),
                ("K2S7-VbN4-6pZ-xC1y", 0.0417),
                ("L3T9-WcM5-7qA-yD2u", 0.0417)
            ]
            for key, days in keys:
                db.session.add(LicenseKey(key=key, duration_days=days))
            db.session.commit()
            print("✅ База данных создана. Добавлено 9 ключей.")
        _initialized = True

@app.route('/api/activate', methods=['POST'])
def activate():
    data = request.get_json()
    key = data.get('key')
    device_id = data.get('device_id')

    if not key or not device_id:
        return jsonify({"error": "Неверный запрос"}), 400

    license_key = LicenseKey.query.filter_by(key=key).first()
    if not license_key:
        return jsonify({"error": "Ключ не существует"}), 404

    if license_key.used:
        return jsonify({"error": "Ключ уже использован"}), 403

    # Удаляем ключ
    db.session.delete(license_key)
    db.session.commit()

    return jsonify({
        "duration_days": license_key.duration_days
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
