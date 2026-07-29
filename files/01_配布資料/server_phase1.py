"""
畑のステータス表示 - フェーズ2（DHT22 + ADC0834土壌水分センサー）
気温・湿度はDHT22、土壌水分はADC0834経由の実測値を返す。
このサーバー自身がHTML（status_mockup.html）も配信するので、
ブラウザで http://<ラズパイのIP>:5000/ を開くだけで見られる。
"""

import threading
import time
from pathlib import Path

import board
import adafruit_dht
from flask import Flask, jsonify, send_from_directory

import adc0834

DHT_PIN = board.D4
SOIL_ADC_CHANNEL = 0
READ_INTERVAL_SEC = 2

# 実測した較正値（乾燥 220 / 水中 127）
SOIL_RAW_DRY = 220
SOIL_RAW_WET = 127

# status_mockup.html をこのapp.pyと同じフォルダに置いておくこと
HTML_DIR = Path(__file__).parent

app = Flask(__name__)
dht = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)
adc0834.setup()

latest = {
    "soil": 50,
    "soil_live": True,
    "humidity": 55,
    "temperature": 24.0,
    "ok": False,
    "updated_at": None,
}
lock = threading.Lock()


def soil_raw_to_percent(raw):
    """rawのADC値(0-255)を 0-100%（湿っているほど大きい値）に変換する"""
    pct = (SOIL_RAW_DRY - raw) / (SOIL_RAW_DRY - SOIL_RAW_WET) * 100
    return max(0, min(100, round(pct)))


def sensor_loop():
    while True:
        try:
            temperature = dht.temperature
            humidity = dht.humidity
            soil_raw = adc0834.read_average(SOIL_ADC_CHANNEL)
            soil_pct = soil_raw_to_percent(soil_raw)

            if temperature is not None and humidity is not None:
                with lock:
                    latest["humidity"] = round(humidity)
                    latest["temperature"] = round(temperature, 1)
                    latest["soil"] = soil_pct
                    latest["ok"] = True
                    latest["updated_at"] = time.time()
                print(f"[OK] hum={humidity:.1f} temp={temperature:.1f} soil_raw={soil_raw:.1f} soil%={soil_pct}")
            else:
                print("[WARN] DHT22 read returned None")
        except RuntimeError as e:
            print(f"[WARN] DHT22 read error: {e}")
        except Exception as e:
            print(f"[ERROR] unexpected sensor error: {e}")

        time.sleep(READ_INTERVAL_SEC)


@app.route("/api/status")
def status():
    with lock:
        return jsonify(dict(latest))


@app.route("/")
def index():
    return send_from_directory(HTML_DIR, "status_mockup.html")


if __name__ == "__main__":
    t = threading.Thread(target=sensor_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)



@app.route("/api/status")
def status():
    with lock:
        return jsonify(dict(latest))


@app.route("/")
def index():
    return send_from_directory(HTML_DIR, "status_mockup.html")


if __name__ == "__main__":
    t = threading.Thread(target=sensor_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
