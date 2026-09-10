#!/usr/bin/env python3
"""
Test consumer - subscribes to bms.realtime and prints battery data.

Use this to verify the simulation is producing and sending data correctly.

Usage:
    python3 test_consumer.py              # Listen to bms.realtime
    python3 test_consumer.py bms.events   # Listen to bms.events
"""

import json
import sys
from kafka import KafkaConsumer
from config import KAFKA_CONFIG


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else KAFKA_CONFIG["realtime_topic"]

    print(f"Connecting to Kafka at {KAFKA_CONFIG['bootstrap_servers']}")
    print(f"Subscribing to topic: {topic}")
    print("Press Ctrl+C to stop\n")

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
        group_id="test-consumer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    count = 0
    try:
        for message in consumer:
            data = message.value
            count += 1

            if count == 1 or count % 30 == 0:
                print(f"--- Message #{count} (t={data.get('sim_time', 0):.0f}s) ---")
                print(
                    f"  Pack: {data['pack_voltage']:.2f}V | "
                    f"{data['current']:.2f}A | "
                    f"{data['power']:.1f}W | "
                    f"SOC={data['soc']:.1f}%"
                )
                print(
                    f"  Temp: {data['temperature'][0]:.1f}C | "
                    f"Status: {data['status']}"
                )
                print(
                    f"  Cells: min={data['min_cell_voltage']:.3f}V "
                    f"max={data['max_cell_voltage']:.3f}V "
                    f"delta={data['voltage_imbalance']*1000:.1f}mV"
                )
                if count == 1:
                    print(f"  Cell voltages: {data['cell_voltage']}")
                    print(f"  Cell SOCs: {data['cell_soc']}")

    except KeyboardInterrupt:
        print(f"\n\nReceived {count} messages total.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
