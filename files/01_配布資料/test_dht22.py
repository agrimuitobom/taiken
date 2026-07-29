"""
DHT22 単体テスト。
配線が合っていれば、気温・湿度が数秒おきにターミナルに表示され続ける。
先にこれが安定して動くことを確認してから、土壌水分センサーに進む。
"""

import time
import board
import adafruit_dht

DHT_PIN = board.D4  # DHT22のDATA線を挿したGPIO番号（配線に合わせて変更）

dht = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)

print("DHT22 テスト開始（Ctrl+Cで終了）")

while True:
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        if temperature is not None and humidity is not None:
            print(f"気温: {temperature:.1f}C  湿度: {humidity:.1f}%")
        else:
            print("読み取り値がNoneでした。配線を確認してください。")
    except RuntimeError as e:
        # DHT22はよくある一時的な読み取り失敗。配線が合っていれば数回に1回は成功する
        print(f"読み取り失敗（よくあるエラー）: {e}")
    except Exception as e:
        print(f"想定外のエラー: {e}")
        raise

    time.sleep(2)
