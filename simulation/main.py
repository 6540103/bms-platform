#!/usr/bin/env python3
"""
BMS Battery Simulator - Main Entry Point

Simulates a 13S NMC battery pack using Thevenin first-order equivalent
circuit model. Publishes real-time battery data to Kafka (bms.realtime),
and accepts control commands via Kafka (bms.commands).

Usage:
    python3 main.py                          # Default: 40Ah, 90% SOC, real-time
    python3 main.py --capacity 60           # 60Ah pack
    python3 main.py --soc 0.5 --no-realtime # Start at 50%, run fast
    python3 main.py --no-kafka               # Run without Kafka (console only)
    python3 main.py --max-steps 3600        # Run for 1 hour of sim time
"""

import sys
import signal
import argparse
from simulation_engine import SimulationEngine
from kafka_producer import BatteryKafkaProducer
from kafka_consumer import CommandConsumer


def parse_args():
    parser = argparse.ArgumentParser(description="BMS Battery Simulator")
    parser.add_argument(
        "--capacity", type=float, default=None,
        help="Battery capacity in Ah (default: 40)",
    )
    parser.add_argument(
        "--soc", type=float, default=None,
        help="Initial SOC fraction 0-1 (default: 0.9)",
    )
    parser.add_argument(
        "--no-kafka", action="store_true",
        help="Disable Kafka (run simulation only, print to console)",
    )
    parser.add_argument(
        "--no-realtime", action="store_true",
        help="Run as fast as possible (no real-time pacing)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=None,
        help="Maximum simulation steps (default: unlimited)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("  BMS Battery Simulator")
    print("  13S NMC Battery Pack - Thevenin First-Order ECM")
    print("=" * 60)

    # Create simulation engine
    engine = SimulationEngine(
        capacity_ah=args.capacity,
        initial_soc=args.soc,
        real_time=not args.no_realtime,
    )

    # Kafka producer
    kafka_producer = None
    if not args.no_kafka:
        kafka_producer = BatteryKafkaProducer()
        if kafka_producer._connected:
            engine.add_callback(kafka_producer.send_realtime)
            kafka_producer.send_event("simulation_started", {
                "capacity_ah": engine.pack.capacity_ah,
                "num_cells": engine.pack.num_cells,
                "initial_soc": round(engine.pack.soc, 4),
            })
        else:
            print("[Main] Kafka not available, running without Kafka")
            kafka_producer = None

    # Command consumer (listens for control commands)
    command_consumer = None
    if not args.no_kafka and kafka_producer:
        command_consumer = CommandConsumer(engine)
        command_consumer.start()

    # Graceful shutdown handler
    def signal_handler(sig, frame):
        print("\n[Main] Shutting down...")
        engine.stop()
        if command_consumer:
            command_consumer.stop()
        if kafka_producer:
            kafka_producer.send_event("simulation_stopped", {"reason": "signal"})
            kafka_producer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run simulation
    try:
        final_state = engine.run(max_steps=args.max_steps)
        print(
            f"\n[Main] Final: SOC={final_state['soc']:.1f}%, "
            f"V={final_state['pack_voltage']:.2f}V, "
            f"T={final_state['temperature'][0]:.1f}C"
        )
    finally:
        if command_consumer:
            command_consumer.stop()
        if kafka_producer:
            kafka_producer.send_event("simulation_stopped", {"reason": "completed"})
            kafka_producer.close()

    print("[Main] Done.")


if __name__ == "__main__":
    main()
