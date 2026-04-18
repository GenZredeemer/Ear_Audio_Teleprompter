import serial
import time
import numpy as np
import matplotlib.pyplot as plt

PORT = "COM7"  # Ensure this matches your ESP32-S3 port
BAUD = 115200
DURATION = 10

# ─── 1. Data Collection ───
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # Wait for serial connection to stabilize

values = []
start = time.time()

try:
    print("Recording... Speak at a normal, clear volume!")
    while time.time() - start < DURATION:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            parts = line.split(",")
            try:
                values.append(int(parts[0]))
            except ValueError:
                pass
finally:
    ser.close()
    print(f"Captured {len(values)} samples")

values = np.array(values, dtype=float)

# ─── 2. Understandable & Efficient DSP ───

# A. Robust Baseline
baseline = np.median(values)

# B. Moving Average (Smoothing via Convolution)
WINDOW = 20
kernel = np.ones(WINDOW) / WINDOW
padded_values = np.pad(values, (WINDOW//2, WINDOW//2 - 1), mode='edge')
smoothed = np.convolve(padded_values, kernel, mode='valid')

# C. Dynamic Peak Thresholding (The "40% Rule")
# 1. Calculate the background noise variance (still useful for the graph)
mad = np.median(np.abs(smoothed - baseline))

# 2. Find the loudest peak in the smoothed speaking envelope
peak_volume = np.max(smoothed)

# 3. Calculate the total dynamic range (from room silence to loudest word)
dynamic_range = peak_volume - baseline

# 4. Set the threshold to 40% of that range. 
# This perfectly validates the "upper parts" of the wave.
VALID_WAVE_PERCENT = 0.40 
minimum_voice_threshold = baseline + (VALID_WAVE_PERCENT * dynamic_range)

print(f"Room Silence Baseline: {baseline:.1f}")
print(f"Loudest Peak:          {peak_volume:.1f}")
print(f"Minimum Voice Threshold: {minimum_voice_threshold:.1f}")

# ─── 3. Plotting (With Noise Floor & Red LED Zone Visualization) ───
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
x_axis = range(len(values))

# Top Plot: Raw Signal
ax1.plot(values, color='steelblue', linewidth=0.8, label='Raw ADC')
ax1.fill_between(x_axis, baseline - mad, baseline + mad, color='gray', alpha=0.2, label='Room Noise Floor')
ax1.axhline(y=minimum_voice_threshold, color='green', linestyle='--', label=f'Good Vol. ({minimum_voice_threshold:.0f})')
ax1.axhline(y=baseline, color='black', linestyle=':', label='Baseline')
ax1.set_title("KY-037 Sound — Raw Signal vs. Room Noise")
ax1.set_ylabel("ADC Value")
ax1.legend(loc="upper left")

# Bottom Plot: Smoothed Signal & Hardware Emulation
ax2.plot(smoothed, color='orange', linewidth=2, label='Smoothed Loudness Envelope')
ax2.fill_between(x_axis, baseline - mad, baseline + mad, color='gray', alpha=0.2)
ax2.axhline(y=minimum_voice_threshold, color='green', linestyle='--', label=f'Green LED Threshold')

# Visually shade the area where the Red LED will be turned on
ax2.fill_between(x_axis, 0, minimum_voice_threshold, where=(smoothed < minimum_voice_threshold), color='red', alpha=0.1, label='Red LED ON (Too Quiet)')

ax2.axhline(y=baseline, color='black', linestyle=':', label='Baseline')
ax2.set_title("KY-037 Sound — AI Volume Check Logic & LED Triggers")
ax2.set_xlabel("Sample")
ax2.set_ylabel("ADC Value")
ax2.legend(loc="upper left")

plt.tight_layout()
plt.show()