# Vintage geared clock — ESP32-S3 + 28BYJ-48 (ULN2003) + 2x A3144 hall sensors
# MicroPython. Copy config.py and main.py to the board.
import time, network, ntptime
from machine import Pin
import config as C

# ---------------- hardware ----------------
coils = [Pin(p, Pin.OUT, value=0) for p in C.MOTOR_PINS]
min_sens = Pin(C.MINUTE_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
hour_sens = Pin(C.HOUR_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
boot_btn = Pin(C.BOOT_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

SEQ = ((1,0,0,0),(1,1,0,0),(0,1,0,0),(0,1,1,0),(0,0,1,0),(0,0,1,1),(0,0,0,1),(1,0,0,1))
SPH = C.HALF_STEPS_PER_REV * C.DRIVE_RATIO      # half-steps per hour (one minute-hand turn)
CYCLE = SPH * 12                                 # half-steps per 12 h
STEPS_PER_SEC = SPH / 3600

phase = 0
pos = 0.0           # half-steps since 12:00, kept in [0, CYCLE)
_last_min = 1


def minute_active():
    return min_sens.value() == 0

def hour_active():
    return hour_sens.value() == 0


def release():
    for c in coils:
        c.value(0)


def step(n, us, watch=True):
    """Advance n half-steps clockwise. If watch, re-sync pos on each minute-sensor edge."""
    global phase, pos, _last_min
    d = -1 if C.REVERSE else 1
    for _ in range(n):
        phase = (phase + d) % 8
        s = SEQ[phase]
        for i in range(4):
            coils[i].value(s[i])
        time.sleep_us(us)
        pos += 1
        if pos >= CYCLE:
            pos -= CYCLE
        m = min_sens.value()
        if watch and _last_min == 1 and m == 0:     # falling edge = top of the hour
            k = round(pos / SPH)
            err = pos - k * SPH
            if abs(err) < SPH / 8:
                if abs(err) >= 2:
                    print("drift corrected:", err, "half-steps")
                pos = (k * SPH) % CYCLE
        _last_min = m


def run_until(cond, limit, us):
    """Step until cond() is true. Returns steps taken, or -1 if limit hit."""
    for n in range(limit):
        if cond():
            return n
        step(1, us, watch=False)
    return -1


def home(use_hour=True):
    """Bring the hands to exactly 12:00 using the sensors."""
    global pos, _last_min
    limit = int(CYCLE * 1.1)
    print("homing (may take a few minutes)...")
    if use_hour:
        if hour_active():
            run_until(lambda: not hour_active(), limit, C.STEP_US_FAST)
        if run_until(hour_active, limit, C.STEP_US_FAST) < 0:
            print("ERROR: hour sensor never triggered — check magnet / wiring")
            release()
            return False
    if minute_active():
        run_until(lambda: not minute_active(), int(SPH), C.STEP_US_FAST)
    if run_until(minute_active, int(SPH * 1.2), C.STEP_US_FAST) < 0:
        print("ERROR: minute sensor never triggered — check magnet / wiring")
        release()
        return False
    if use_hour and not hour_active():
        print("WARNING: minute mark found outside the hour-sensor window — re-align the hour wheel")
    pos = 0.0
    _last_min = 0
    release()
    print("homed: hands at 12:00")
    return True


# ---------------- time ----------------
def first_sunday(y, mon):
    wd = time.localtime(time.mktime((y, mon, 1, 0, 0, 0, 0, 0)))[6]   # Mon=0 .. Sun=6
    return 1 + (6 - wd) % 7


def transition(y, rule, offset_h):
    mon, hr = rule
    return time.mktime((y, mon, first_sunday(y, mon), hr, 0, 0, 0, 0)) - offset_h * 3600


def utc_offset_h(t):
    if not C.DST_START:
        return C.STD_OFFSET_H
    y = time.localtime(t)[0]
    start = transition(y, C.DST_START, C.STD_OFFSET_H)
    end = transition(y, C.DST_END, C.DST_OFFSET_H)
    if start > end:                         # southern hemisphere
        dst = t >= start or t < end
    else:
        dst = start <= t < end
    return C.DST_OFFSET_H if dst else C.STD_OFFSET_H


def seconds_since_12():
    t = time.time()
    return (t + utc_offset_h(t) * 3600) % 43200


def wifi_ntp():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(C.WIFI_SSID, C.WIFI_PASS)
        for _ in range(40):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    if not wlan.isconnected():
        print("Wi-Fi failed")
        return False
    ntptime.host = C.NTP_HOST
    for _ in range(3):
        try:
            ntptime.settime()
            print("NTP ok, UTC", time.localtime())
            return True
        except OSError:
            time.sleep(2)
    print("NTP failed")
    return False


# ---------------- main ----------------
def show_hands():
    global pos
    target = seconds_since_12() * STEPS_PER_SEC
    diff = target - pos
    if diff < -SPH / 120:                    # target is behind us (DST end) -> go round
        diff += CYCLE
    elif diff < 0:
        return
    n = int(diff)
    if n:
        step(n, C.STEP_US_FAST if n > 400 else C.STEP_US_SLOW)
        release()


def main():
    fitting = boot_btn.value() == 0
    while not wifi_ntp():
        time.sleep(30)
    if fitting:
        home(use_hour=False)
        print("HAND-FITTING MODE: minute arbor is at the top of the hour.")
        print(" 1. Fit the hour wheel with its magnet over the hour sensor.")
        print(" 2. Push both hands on pointing at XII.")
        print(" 3. Press BOOT to start the clock.")
        while boot_btn.value() == 1:
            time.sleep(0.05)
        time.sleep(0.5)
    else:
        home(use_hour=True)
    last_sync = time.time()
    while True:
        show_hands()
        if time.time() - last_sync > C.NTP_RESYNC_H * 3600:
            wifi_ntp()
            last_sync = time.time()
        time.sleep(C.UPDATE_S)


main()
