# -*- coding: utf-8 -*-
import RPi.GPIO as gpio
import time
from datetime import datetime

# ===== Config =====
ACTIVE_LOW_VALVE = True     # cambia si tu válvula abre con HIGH
PIN_VALVE = 16

# Bombas (opcional: ajusta o elimina si ya las manejas aparte)
PIN_PUMP_1, PIN_PUMP_2 = 21, 20
PWM_FREQ_PUMPS = 1000
DUTY_P1, DUTY_P2 = 100, 10

# ===== Secuencias =====
# 1) Burst inicial: frecuencia alta y duty fijo por X segundos
BURST_HZ    = 8.0      # 5–10 Hz suele ir bien para “activar” dinámica
BURST_DUTY  = 0.6      # 60% de tiempo abierta en cada ciclo
BURST_TIME  = 3.0      # duración total del burst (s)

# 2) Régimen posterior (time-proportioning por etapas)
REGIMEN = [
    {"label":"bajo" , "period": 1.5, "duty": 0.25, "cycles": 12},
    {"label":"medio", "period": 1.0, "duty": 0.50, "cycles": 12},
    {"label":"alto" , "period": 0.7, "duty": 0.75, "cycles": 20},
]

# ===== Helpers =====
def v_open():  gpio.output(PIN_VALVE, gpio.LOW if ACTIVE_LOW_VALVE else gpio.HIGH)
def v_close(): gpio.output(PIN_VALVE, gpio.HIGH if ACTIVE_LOW_VALVE else gpio.LOW)
def now():     return datetime.now().isoformat(timespec='milliseconds')

def configure():
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.setup(PIN_VALVE, gpio.OUT,
               initial=(gpio.HIGH if ACTIVE_LOW_VALVE else gpio.LOW))
    # Bombas (opcional)
    gpio.setup(PIN_PUMP_1, gpio.OUT, initial=gpio.LOW)
    gpio.setup(PIN_PUMP_2, gpio.OUT, initial=gpio.LOW)
    global pwm1, pwm2
    pwm1 = gpio.PWM(PIN_PUMP_1, PWM_FREQ_PUMPS)
    pwm2 = gpio.PWM(PIN_PUMP_2, PWM_FREQ_PUMPS)
    pwm1.start(0); pwm2.start(0)
    pwm1.ChangeDutyCycle(DUTY_P1)
    pwm2.ChangeDutyCycle(DUTY_P2)

def burst_valve(hz, duty, total_s):
    duty = max(0.0, min(1.0, duty))
    if hz <= 0: return
    period = 1.0 / hz
    on_t = duty * period
    off_t = period - on_t
    t0 = time.time()
    k = 0
    while time.time() - t0 < total_s:
        v_open();  time.sleep(on_t)
        v_close(); time.sleep(off_t)
        k += 1
    print(f"[{now()}] Burst done: {k} ciclos @ {hz} Hz, duty={duty*100:.0f}%")

def regimen_valve(stages):
    for s in stages:
        label  = s["label"]; period = float(s["period"])
        duty   = max(0.0, min(1.0, float(s["duty"])))
        cycles = int(s["cycles"])
        on_t, off_t = duty*period, max(0.0, period - duty*period)
        for i in range(1, cycles+1):
            v_open();  time.sleep(on_t)
            v_close(); time.sleep(off_t)
        print(f"[{now()}] Etapa '{label}' completada ({cycles} ciclos, period={period}s, duty={duty*100:.0f}%)")

# ===== Main =====
try:
    configure()
    # 1) Arranque rápido para “asentar” la neumática
    burst_valve(BURST_HZ, BURST_DUTY, BURST_TIME)

    # 2) Cambiar a régimen de prueba
    regimen_valve(REGIMEN)

except KeyboardInterrupt:
    pass
finally:
    # Seguridad: bombas a 0 y dejar válvula como prefieras (aquí se libera)
    try:
        pwm1.ChangeDutyCycle(0); pwm2.ChangeDutyCycle(0)
        v_open(); time.sleep(0.1)
        pwm1.stop(); pwm2.stop()
    except Exception:
        pass
    gpio.cleanup()
