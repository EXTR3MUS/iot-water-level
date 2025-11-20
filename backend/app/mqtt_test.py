import time
import json
import os
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime

# allow overriding host + credentials via env
# default stays localhost for local dev, but Compose will set `MQTT_HOST=mosquitto`
BROKER_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "esp32/test/hello_world_001")

# Database file next to this script
DB_PATH = os.path.join(os.path.dirname(__file__), "water_levels.db")

# create a single connection usable from callbacks (allow threading)
_conn = None

def init_db():
    global _conn
    if _conn:
        return
    _conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
    cur = _conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA busy_timeout = 5000;")
    cur.execute("PRAGMA table_info(water_levels);")
    columns = [row[1] for row in cur.fetchall()]
    if columns and columns != ["id", "water_level", "recorded_ts"]:
        cur.execute("DROP TABLE IF EXISTS water_levels;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS water_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        water_level REAL NOT NULL,
        recorded_ts REAL NOT NULL
    )
    """)
    _conn.commit()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC, qos=1)
    print(f"Subscribed to {TOPIC}")

def on_message(client, userdata, msg):
    init_db()
    assert _conn is not None
    try:
        payload = msg.payload.decode("utf-8")
        try:
            payload_json = json.loads(payload)
            pretty = json.dumps(payload_json, indent=2)
            print(f"\nReceived on {msg.topic}:\n{pretty}")
        except Exception:
            payload_json = None
            print(f"\nReceived on {msg.topic} (raw):\n{payload}")

        rows_inserted = 0
        if isinstance(payload_json, dict) and "buffer" in payload_json and isinstance(payload_json["buffer"], list):
            items = payload_json["buffer"]
            if items:
                base_ts = time.time()
                rows_to_insert = []
                total = len(items)
                for idx, item in enumerate(items):
                    wl = None
                    if isinstance(item, dict):
                        wl = item.get("water_level")
                    elif isinstance(item, (int, float)):
                        wl = float(item)
                    if wl is None:
                        continue
                    offset = (total - 1 - idx) * 5
                    rows_to_insert.append((float(wl), base_ts - offset))
                if rows_to_insert:
                    attempts = 0
                    while True:
                        try:
                            cur = _conn.cursor()
                            cur.executemany(
                                "INSERT INTO water_levels (water_level, recorded_ts) VALUES (?, ?)",
                                rows_to_insert
                            )
                            cur.close()
                            _conn.commit()
                            rows_inserted = len(rows_to_insert)
                            break
                        except sqlite3.OperationalError as oe:
                            if "locked" in str(oe).lower() and attempts < 5:
                                attempts += 1
                                time.sleep(0.2 * attempts)
                                continue
                            raise
        print(f"Stored {rows_inserted} rows to {DB_PATH}")
    except Exception as e:
        print("Error decoding or persisting message:", e)

if __name__ == "__main__":
    client = mqtt.Client(client_id="mqtt-listener")
    if MQTT_USERNAME is not None:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    try:
        print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}, listening on '{TOPIC}'. Press Ctrl+C to exit.")
        init_db()
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nInterrupted by user, disconnecting...")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass
        if _conn:
            try:
                _conn.close()
            except Exception:
                pass
        print("Disconnected.")