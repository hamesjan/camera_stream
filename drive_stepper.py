import lgpio
import time

# --- Pin Definitions ---
M1_DIR = 17
M1_STEP = 27
M1_EN = 22

M2_DIR = 5
M2_STEP = 6
M2_EN = 13

# --- Setup ---
h = lgpio.gpiochip_open(0)

for pin in [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]:
    lgpio.gpio_claim_output(h, pin)
    lgpio.gpio_write(h, pin, 0)

def enable_motor(motor_id):
    if motor_id == 1:
        lgpio.gpio_write(h, M1_EN, 0)  # LOW = Enabled
    elif motor_id == 2:
        lgpio.gpio_write(h, M2_EN, 0)

def disable_motor(motor_id):
    if motor_id == 1:
        lgpio.gpio_write(h, M1_EN, 1)
    elif motor_id == 2:
        lgpio.gpio_write(h, M2_EN, 1)

def step_motor(motor_id, direction, steps, delay=0.001):
    dir_pin = M1_DIR if motor_id == 1 else M2_DIR
    step_pin = M1_STEP if motor_id == 1 else M2_STEP

    lgpio.gpio_write(h, dir_pin, 1 if direction == 1 else 0)
    for _ in range(steps):
        lgpio.gpio_write(h, step_pin, 1)
        time.sleep(delay)
        lgpio.gpio_write(h, step_pin, 0)
        time.sleep(delay)

# --- Example Usage ---
try:
    enable_motor(1)
    enable_motor(2)

    direction = 1


    while (1):
        print("Stepping Motor 1 Forward")
        step_motor(1, direction=direction, steps=1000, delay=0.002)

        print("Stepping Motor 2 Reverse")
        step_motor(2, direction=direction, steps=3000, delay=0.001)

        direction = direction * -1
            

    disable_motor(1)
    disable_motor(2)

finally:
    lgpio.gpiochip_close(h)
