#!/usr/bin/env python3
"""
Generate a WAV alarm file with a triangle wave oscillating between 500-1000 Hz.
The frequency steps (non-interpolated) to create a distinctive alarm sound.
"""
import numpy as np
import wave
import struct

# Configuration
SAMPLE_RATE = 44100  # Hz
DURATION = 10.0      # seconds
AMPLITUDE = 0.5      # 0.0 to 1.0

# Frequency stepping parameters
FREQ_LOW = 500       # Hz
FREQ_HIGH = 1000     # Hz
STEP_DURATION = 0.5  # seconds per frequency step
NUM_STEPS = 2        # number of discrete frequency steps (low, high)

OUTPUT_FILE = "alarm.wav"

def generate_triangle_wave(frequency, duration, sample_rate, amplitude):
    """Generate a triangle wave at a given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Triangle wave: sawtooth with phase adjustment
    # Using arcsin(sin(x)) approximation scaled
    period = 1.0 / frequency
    samples = amplitude * (2 * np.abs(2 * ((t / period) % 1.0) - 1) - 1)
    return samples

def main():
    print(f"Generating alarm with triangle wave stepping from {FREQ_LOW}Hz to {FREQ_HIGH}Hz...")
    
    all_samples = []
    num_segments = int(DURATION / STEP_DURATION)
    
    for i in range(num_segments):
        # Alternate between low and high frequency (2 steps)
        freq = FREQ_LOW if (i % 2 == 0) else FREQ_HIGH
        
        # Generate triangle wave segment at this frequency
        samples = generate_triangle_wave(freq, STEP_DURATION, SAMPLE_RATE, AMPLITUDE)
        all_samples.extend(samples)
        
        print(f"  Segment {i+1}/{num_segments}: {freq:.1f} Hz")
    
    # Convert to 16-bit PCM
    samples_array = np.array(all_samples)
    samples_int16 = np.int16(samples_array * 32767)
    
    # Write WAV file
    with wave.open(OUTPUT_FILE, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16-bit)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(samples_int16.tobytes())
    
    print(f"\n✓ Alarm saved to '{OUTPUT_FILE}'")
    print(f"  Duration: {DURATION}s")
    print(f"  Sample rate: {SAMPLE_RATE}Hz")
    print(f"  Frequency range: {FREQ_LOW}-{FREQ_HIGH}Hz in {NUM_STEPS} steps")

if __name__ == '__main__':
    main()
