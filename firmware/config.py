# ---- Clock configuration (MicroPython, ESP32-S3) ----

# Wi-Fi for NTP time (2.4 GHz only — the ESP32 has no 5 GHz radio)
WIFI_SSID = "your-ssid"
WIFI_PASS = "your-password"
NTP_HOST  = "pool.ntp.org"
NTP_RESYNC_H = 6

# Time zone — Australia/Sydney (AEST +10, AEDT +11)
STD_OFFSET_H = 10
DST_OFFSET_H = 11
# DST starts first Sunday of October at 02:00 standard time,
# ends first Sunday of April at 03:00 daylight time. Set DST_START = None to disable.
DST_START = (10, 2)     # (month, local hour)
DST_END   = (4, 3)

# ULN2003 driver inputs IN1..IN4
MOTOR_PINS = (4, 5, 6, 7)
# A3144 hall sensors (open collector, internal pull-up, active LOW)
MINUTE_SENSOR_PIN = 15
HOUR_SENSOR_PIN   = 16
BOOT_BUTTON_PIN   = 0     # hold at power-up for hand-fitting mode

# Mechanics
# 28BYJ-48 gearbox is 63.68395:1 -> 4075.7728 half-steps per output turn.
# Some clones are a true 64:1 (4096). Measure: see README "Calibrating".
HALF_STEPS_PER_REV = 4075.7728
DRIVE_RATIO = 2           # motor turns per minute-hand turn (15T -> 30T)
REVERSE = False           # flip if the hands run backwards

STEP_US_FAST = 1300       # homing / catch-up speed (raise if the motor skips)
STEP_US_SLOW = 2500       # normal ticking speed (quieter)
UPDATE_S = 10             # how often the minute hand is advanced
