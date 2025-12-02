import os
import time
import json
import random
import signal
import sys
import paho.mqtt.client as mqtt

# Configuration from environment
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "esp32/test/hello_world_001")
INTERVAL = float(os.getenv("MQTT_INTERVAL", "1"))
BUFFER_ITEMS = int(os.getenv("BUFFER_ITEMS", "2"))

client = mqtt.Client(client_id="simulator-publisher")
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

stop = False

def handle_sig(sig, frame):
    global stop
    stop = True

signal.signal(signal.SIGINT, handle_sig)
signal.signal(signal.SIGTERM, handle_sig)

def connect():
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        return True
    except Exception as e:
        print(f"Failed to connect to MQTT at {MQTT_HOST}:{MQTT_PORT}: {e}")
        return False

def make_payload(base=1.0):
    buf = []
    for i in range(BUFFER_ITEMS):
        value = round(base + i * 0.1 + random.uniform(-0.2, 0.2), 2)
        buf.append({"water_level": value})
    return {"buffer": buf}

def main():
    base = random.uniform(1.0, 3.0)
    if not connect():
        # try a few times before exiting
        attempts = 0
        while attempts < 5 and not stop:
            attempts += 1
            time.sleep(2)
            if connect():
                break
        if not client.is_connected():
            print("Could not connect to MQTT broker, exiting")
            sys.exit(1)

    print(f"Publishing to topic '{MQTT_TOPIC}' every {INTERVAL}s (broker={MQTT_HOST}:{MQTT_PORT})")
    
    # Loop sequence: 4.0 -> 2.7 -> 1.0 -> 4.0 (5 seconds each, repeating)
    loop_sequence = [
        (4.0, 5),   # normal level for 5 seconds
        (2.7, 5),   # warning level for 5 seconds
        (1.0, 5),   # critical level for 5 seconds
    ]
    
    seq_index = 0
    seq_time_left = loop_sequence[0][1]
    current_value = loop_sequence[0][0]
    
    try:
        while not stop:
            payload = {"buffer": [{"water_level": current_value}] * BUFFER_ITEMS}
            payload_str = json.dumps(payload)
            rc = client.publish(MQTT_TOPIC, payload_str)
            print(f"Published: {payload_str}")
            
            time.sleep(INTERVAL)
            seq_time_left -= INTERVAL
            
            # Move to next sequence step and loop back to start
            if seq_time_left <= 0:
                seq_index = (seq_index + 1) % len(loop_sequence)
                current_value = loop_sequence[seq_index][0]
                seq_time_left = loop_sequence[seq_index][1]
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass

if __name__ == '__main__':
    main()
