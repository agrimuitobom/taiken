"""
ADC0834 (4ch, 8bit ADC) をRPi.GPIOでビットバンギング読み取りするモジュール。
MCP3008と違い標準SPIではないため、CS/CLK/DI/DOを手動で制御する。

配線例（GPIO番号は自由に変更可。実機のADC0834のピン配置は
データシートで CS / CLK / DI / DO / CH0-CH3 / VCC(+VREF) / GND を確認して接続すること）:
  CS  -> GPIO25
  CLK -> GPIO18
  DI  -> GPIO24
  DO  -> GPIO23
  CH0 -> 土壌水分センサーのAOUTをここに接続
"""

import RPi.GPIO as GPIO

CLK = 18
DI = 24
DO = 23
CS = 25


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK, GPIO.OUT)
    GPIO.setup(DI, GPIO.OUT)
    GPIO.setup(DO, GPIO.IN)
    GPIO.setup(CS, GPIO.OUT)
    GPIO.output(CS, GPIO.HIGH)


def read_channel(channel):
    """channel: 0-3 (シングルエンド読み取り)。戻り値は0-255の生値。"""
    if channel < 0 or channel > 3:
        raise ValueError("channel must be 0-3")

    GPIO.setup(DI, GPIO.OUT)
    GPIO.output(CS, GPIO.LOW)
    GPIO.output(CLK, GPIO.LOW)

    # スタートビット
    GPIO.output(DI, GPIO.HIGH)
    GPIO.output(CLK, GPIO.HIGH)
    GPIO.output(CLK, GPIO.LOW)

    # SGL/DIF = 1 (シングルエンドモード)
    GPIO.output(DI, GPIO.HIGH)
    GPIO.output(CLK, GPIO.HIGH)
    GPIO.output(CLK, GPIO.LOW)

    # ODD/SIGN ビット（チャンネル選択の上位ビット）
    GPIO.output(DI, GPIO.HIGH if (channel & 0x02) else GPIO.LOW)
    GPIO.output(CLK, GPIO.HIGH)
    GPIO.output(CLK, GPIO.LOW)

    # SELECT ビット（チャンネル選択の下位ビット）
    GPIO.output(DI, GPIO.HIGH if (channel & 0x01) else GPIO.LOW)
    GPIO.output(CLK, GPIO.HIGH)
    GPIO.output(CLK, GPIO.LOW)

    # ここからDOを読む。MSBファーストで8ビット分クロックを出す
    GPIO.setup(DI, GPIO.IN)
    value = 0
    for _ in range(8):
        GPIO.output(CLK, GPIO.HIGH)
        GPIO.output(CLK, GPIO.LOW)
        value <<= 1
        if GPIO.input(DO):
            value |= 1

    GPIO.output(CS, GPIO.HIGH)
    return value  # 0-255


def read_average(channel, samples=5):
    """ノイズ対策で複数回読んで平均を取る"""
    total = sum(read_channel(channel) for _ in range(samples))
    return total / samples
