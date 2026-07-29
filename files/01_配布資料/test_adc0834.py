"""
ADC0834 単体テスト（土壌水分センサーはCH0に接続している前提）。
指で触れる／土に挿す／水に浸す、などしながら実行して、
raw値（0-255）がちゃんと反応して変化するか確認する。
"""

import time
import adc0834

adc0834.setup()

print("ADC0834 テスト開始（Ctrl+Cで終了）")
print("CH0の値を1秒おきに表示します。センサーに触れたり土に挿したりして変化を確認してください。")

while True:
    raw = adc0834.read_average(0, samples=5)
    print(f"CH0 raw = {raw:.1f}  (0-255の範囲。乾燥側/湿潤側で数値がどう動くか見てください)")
    time.sleep(1)
