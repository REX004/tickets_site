from flask import Flask, jsonify, request, send_file, render_template
from flask_cors import CORS
import qrcode
import uuid
import json
from pyzbar.pyzbar import decode
from PIL import Image
import os

app = Flask(__name__)
CORS(app)

# Путь к файлу базы данных
DATABASE_FILE = "tickets.json"

# Создание папки для QR-кодов
QR_CODES_FOLDER = "qr_codes"
os.makedirs(QR_CODES_FOLDER, exist_ok=True)

# Загрузка базы данных
def load_tickets():
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение базы данных
def save_tickets(tickets):
    with open(DATABASE_FILE, "w") as f:
        json.dump(tickets, f)

# Генерация QR-кода
@app.route("/generate", methods=["POST"])
def generate_qr():
    ticket_id = str(uuid.uuid4())  # Уникальный идентификатор билета
    output_file = os.path.join(QR_CODES_FOLDER, f"{ticket_id}.png")

    # Генерация QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_file)

    # Сохраняем билет в базе
    tickets = load_tickets()
    tickets[ticket_id] = {"used": False}
    save_tickets(tickets)

    return jsonify({"ticket_id": ticket_id, "qr_code_url": f"/download/{ticket_id}"})

# Скачивание QR-кода
@app.route("/download/<ticket_id>", methods=["GET"])
def download_qr(ticket_id):
    file_path = os.path.join(QR_CODES_FOLDER, f"{ticket_id}.png")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="image/png")
    return jsonify({"error": "QR-код не найден"}), 404

# Проверка билета
@app.route("/check", methods=["POST"])
def check_ticket():
    ticket_id = request.json.get("ticket_id")
    tickets = load_tickets()
    if ticket_id in tickets:
        if not tickets[ticket_id]["used"]:
            tickets[ticket_id]["used"] = True
            save_tickets(tickets)
            return jsonify({"status": "valid", "message": "Билет подтверждён!"})
        else:
            return jsonify({"status": "used", "message": "Билет уже был использован."})
    return jsonify({"status": "invalid", "message": "Билет не найден."})

# Сканирование QR-кода
@app.route("/scan", methods=["POST"])
def scan_qr():

    file = request.files["file"]
    img = Image.open(file)
    decoded_objects = decode(img)
    try:
        img = Image.open(file)
    except Exception as e:
        return jsonify({"error": "Ошибка при обработке изображения!"}), 400

    for obj in decoded_objects:
        return jsonify({"ticket_id": obj.data.decode("utf-8")})
    return jsonify({"error": "QR-код не найден!"})

# Главная страница
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
