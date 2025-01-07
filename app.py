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

DATABASE_FILE = "tickets.json"

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
    ticket_id = str(uuid.uuid4())
    output_file = f"qr_codes/{ticket_id}.png"
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

    return jsonify({"ticket_id": ticket_id, "qr_code": output_file})

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
    for obj in decoded_objects:
        return jsonify({"ticket_id": obj.data.decode("utf-8")})
    return jsonify({"error": "QR-код не найден!"})

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    os.makedirs("qr_codes", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
