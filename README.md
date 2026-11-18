# Vintage geared clock — 28BYJ-48 + ESP32-S3

180 mm Roman-numeral dial, hour and minute hands, no seconds hand. Time comes from NTP over Wi-Fi with Sydney daylight saving built in. Two hall sensors let it find 12:00 by itself after a power cut.

## How it works
- **Drive:** motor 15T drives the centre wheel 30T, so the motor turns twice per hour. The centre wheel sits on a 3 mm arbor that turns the minute hand.
- **Motion works (12:1):** cannon pinion 15T → minute wheel 45T (3:1), then minute pinion 12T → hour wheel 48T (4:1).
- **Gear standard:** all gears are module 1, 20° pressure angle.
- **Shafts:** the minute hand rides on a 4 mm brass "cannon" tube glued to the arbor. The hour hand rides on a 5 mm brass pipe that turns freely on that tube.
- **Sensors:** a magnet in the centre wheel marks the top of each hour. A magnet in the hour wheel marks the 12 o'clock window. On every boot the clock homes to 12:00, then runs forward to the current time. It never runs backwards, which keeps gear slack out of the hands.
- **Self-correction:** every time the minute magnet passes its sensor, the firmware re-zeroes its step count, so step-count errors can't build up.

## Parts list
| Qty | Item | Notes |
|---|---|---|
| 1 | ESP32-S3 dev board | e.g. ESP32-S3-DevKitC-1 |
| 1 | 28BYJ-48 5 V motor + ULN2003 board | usually sold together |
| 1 | 5 V USB supply, ≥1 A | |
| 2 | 683ZZ bearings, 3×7×3 | |
| 2 | A3144 hall sensors, bare (not KY-003 modules) | KY-003 boards pull the output up to 5 V, which is unsafe for the ESP32 |
| 2 | 3×2 mm neodymium disc magnets | |
| 36 mm | 3 mm steel or brass rod | arbor |
| 24 mm | 4 mm brass tube, about 3.1 ID | cannon |
| 16 mm | 5 mm brass tube, about 4.1 ID | hour pipe; must spin freely on the 4 mm tube |
| 4 | M3×25 screws + 4 M3 nuts | pillars; the screw tips self-tap into the dial bosses |
| 1 | M3×16 screw, M3 nyloc nut, 2 washers | minute-wheel stud |
| 2 | M3 or M4 ×8 screws + nuts | motor ears (4.2 mm holes) |
| — | CA glue or epoxy, dupont wires | |

## Printed parts (`out/`)
| Part | Qty | Notes |
|---|---|---|
| back_plate | 1 | includes the wall feet and keyhole |
| front_plate | 1 | |
| pillar | 4 | |
| motor_pinion | 1 | |
| centre_wheel | 1 | |
| cannon_pinion | 1 | |
| minute_wheel | 1 | 45T wheel and 12T pinion as one part |
| hour_wheel | 1 | |
| hour_hand | 1 | |
| minute_hand | 1 | |
| dial **or** dial_plain | 1 | |

**Print settings:** PLA or PETG. Use 0.12–0.16 mm layers for the gears and 3 walls. Print the dial face-down on a smooth plate.

**Three dial options:**
1. `dial.stl` with engraved numerals, then rub dark paint into them.
2. `dial.stl` plus `dial_inlay_2colour.stl` as a second body on a multi-material printer.
3. `dial_plain.stl` with `dial_face_A4.pdf` printed on cream card and glued on. Print the PDF at 100% / "actual size" and check the 100 mm scale bar with a ruler.

## Wiring
```
ULN2003  IN1 -> GPIO4   IN2 -> GPIO5   IN3 -> GPIO6   IN4 -> GPIO7
ULN2003  +   -> 5V (VBUS pin)          -    -> GND
Motor plug   -> ULN2003 socket

A3144 (branded face toward magnet; pins left->right with the text facing you)
  pin1 VCC -> 5V      pin2 GND -> GND
  pin3 OUT -> GPIO15  (minute sensor, back plate)
  pin3 OUT -> GPIO16  (hour sensor, front-plate pad)
```
The sensor outputs are open-collector. The ESP32's internal pull-ups take them to 3.3 V, so no resistors are needed.

The A3144 only responds to one pole of the magnet. If a sensor never triggers, flip that magnet over.

## Assembly
1. **Bearings:** press a 683ZZ into the back of the back plate, and another into the inner boss of the front plate.
2. **Motor:** bolt it to the back of the back plate, with the shaft poking through to the front. Push the motor pinion onto the shaft until it's just clear of the plate.
3. **Minute sensor:** lay it in the pocket on the front face of the back plate, branded face up. Bend the legs down through the slot. Glue a magnet into the back of the centre wheel.
4. **Arbor:** fit the 3 mm rod into the back bearing. Glue the centre wheel to the rod about 0.5 mm off the plate, meshed with the motor pinion.
5. **Hour sensor:** fit it in the pad pocket on the front plate the same way. Its legs go through to the space between the plates.
6. **Close up the movement:** put the 4 pillars between the plates. Fit M3×25 screws from the back and finger-tighten the nuts on the front face.
7. **Minute wheel:** fit the M3×16 screw from behind the front plate at the stud hole. Stack a washer, the minute wheel (big gear toward the plate) and a washer, then the nyloc nut. Tighten until the wheel spins freely with no wobble.
8. **Cannon:** slide the 4 mm tube over the arbor and glue it to the arbor only, keeping glue away from the bearing. Push the cannon pinion onto the tube about 0.5 mm off the front plate, meshed with the minute wheel, and glue it.
9. **Hour wheel:** glue the 5 mm pipe into it, flush at the back. Glue a magnet into its pocket. Slide it onto the cannon tube, but leave it unmeshed for now.
10. **Firmware:** wire everything up. Edit `firmware/config.py` with your Wi-Fi details, then copy `config.py` and `main.py` to the board (Thonny or `mpremote cp`).
11. **Hand-fitting mode:** hold BOOT while you power up. The clock homes to the minute sensor and stops.
12. **Align the hour wheel:** turn it until its magnet sits over the hour sensor, then mesh it.
13. **Dial:** fit it over the screw tips. The nuts sit in the recesses in its bosses. Turn the screws in so they self-tap into the bosses.
14. **Hands:** press the hour hand onto the 5 mm pipe and the minute hand onto the 4 mm tube, both pointing at XII. Press BOOT and the clock runs forward to the current time.

**Wall mounting:** hang it on a screw through the keyhole in the top foot. The screw head must be ≤8 mm across and the shank ≤4 mm.

## Calibrating
Watch the serial output for an hour. If every hour it prints `drift corrected: ±40` or so, your motor is a true 64:1 clone. Set `HALF_STEPS_PER_REV = 4096`. Small corrections of a few half-steps are normal.

If the hands run backwards, set `REVERSE = True`.

If the motor skips steps while homing, raise `STEP_US_FAST`.

## Limits
- **Unproven on hardware.** The CAD has been collision-checked in the assembled position, and the firmware's daylight-saving logic was checked against the real Sydney time-zone rules hourly over three years. None of it has been printed or run on a board.
- **Startup takes a few minutes.** Homing can take up to about 2 minutes, then running forward to the current time up to another 2.
- **Hand wobble.** Expect about 1° of slack at the minute hand from printed gear backlash. Driving the hands forward only hides most of it.
- **The motor hums** briefly every 10 seconds when it advances. Set `UPDATE_S = 60` for less frequent, larger moves.
