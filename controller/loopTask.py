import datetime
import time
import RPi.GPIO as GPIO
import smbus2

from pydantic_settings import BaseSettings
from INA226 import INA226
from INA228 import INA228
import PlanFile

I2C_ADDR_INA226 = 0x40  # meter for charger i2c address
I2C_ADDR_INA228 = 0x44  # meter for battery i2c address
PIN_ACDC = 17
PIN_INV = 27

LOOP_TIME_SEC = 30

# 環境変数の読み込み
# .env ファイルの書き方と、 DATA_DIR については、README を参照

class MyEnv(BaseSettings):
    DATA_DIR: str

    class Config:
        env_file = ".env"

env = MyEnv()

# 指令用GPIOの初期設定
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_ACDC, GPIO.OUT)
GPIO.setup(PIN_INV, GPIO.OUT)

# 電流計測IC
i2c = smbus2.SMBus(1)
ina226 = INA226(i2c, I2C_ADDR_INA226)  # meter for charger
ina228 = INA228(i2c, I2C_ADDR_INA228)  # meter for battery

try:
    force_charge_start_time = 0

    while True:
        now = datetime.datetime.now()  # 現在時刻

        # =======
        # Logging
        # =======
        
        batt_voltage_V = 0

        try:
            ina226.set_calibration(current_lsb_A=0.001, shunt_ohm=0.002)
            ina228.set_calibration(max_current_A=50, shunt_ohm=0.002)

            charger_voltage_V = ina226.get_bus_voltage_V()
            charger_current_A = ina226.get_current_A()
            charger_power_W   = ina226.get_power_W()

            batt_voltage_V = ina228.get_bus_voltage_V()
            batt_current_A = ina228.get_current_A()
            batt_power_W   = ina228.get_power_W()
            batt_charge_C  = ina228.get_charge_C()

            log_text = (
                now.strftime("%Y/%m/%d %H:%M:%S") + ',' +
                str(round(charger_voltage_V, 5)) + ',' + 
                str(round(charger_current_A, 4)) + ',' + 
                str(round(charger_power_W, 4)) + ',' +
                str(round(batt_voltage_V, 10)) + ',' + 
                str(batt_current_A) + ',' + 
                str(batt_power_W) + ',' + 
                str(batt_charge_C)
            )
#             print(log_text)

            log_file_path = env.DATA_DIR + "/powerLog/" +  now.strftime("%Y%m%d") + ".csv"
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_text + "\n")
        
        except OSError:
            print("I2C communication failed")

        # =======
        # Control
        # =======

        index = int(48 * (now.hour * 60 + now.minute) / 1440)  # 1日を48コマに区切ったときの、現在のコマ
        plan_file = PlanFile.PlanFile(env.DATA_DIR + "/chargePlan/")
        plan = plan_file.extract(now, index, 1)  # 現在時刻の充電計画を取得
        acdc: int = plan["acdc"][0]  # ACDC(鉛充電器)計画:1でON
        inv: int  = plan["inv"][0]   # インバータ計画:1でON

        if batt_voltage_V < 12.0:
            force_charge_start_time = now

        if force_charge_start_time != 0:
            GPIO.output(PIN_ACDC, 1)
            if now - force_charge_start_time > datetime.timedelta(minutes=30):
                force_charge_start_time = 0
                print("Force charge end")
        else:
            GPIO.output(PIN_ACDC, acdc)

        GPIO.output(PIN_INV, inv)

        time.sleep(LOOP_TIME_SEC)

except KeyboardInterrupt:
    GPIO.cleanup()
    pass  # Ctrl+C例外で終了
