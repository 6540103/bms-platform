"""Kafka consumer for receiving control commands from bms.commands topic."""

import json
import time
import threading
from kafka import KafkaConsumer
from config import KAFKA_CONFIG


class CommandConsumer:
    def __init__(self, simulation_engine):
        self.engine = simulation_engine
        self.config = KAFKA_CONFIG
        self.consumer = None
        self.running = False
        self._thread = None

    def start(self):
        """Start consuming commands in a background thread."""
        try:
            self.consumer = KafkaConsumer(
                self.config["commands_topic"],
                bootstrap_servers=self.config["bootstrap_servers"],
                group_id="bms-simulator-commands",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
            )
            self.running = True
            self._thread = threading.Thread(target=self._consume_loop, daemon=True)
            self._thread.start()
            print(f"[CommandConsumer] Started, listening on {self.config['commands_topic']}")
        except Exception as e:
            print(f"[CommandConsumer] Failed to start: {e}")

    def _consume_loop(self):
        """Background consumption loop."""
        while self.running:
            try:
                for message in self.consumer:
                    if not self.running:
                        break
                    command = message.value
                    self._handle_command(command)
            except Exception as e:
                if self.running:
                    print(f"[CommandConsumer] Error: {e}")
                    time.sleep(1)

    def _handle_command(self, command):
        """Handle an incoming command dictionary."""
        if not isinstance(command, dict):
            print(f"[CommandConsumer] Invalid command format: {command}")
            return

        cmd = str(command.get("command", "")).lower()
        print(f"[CommandConsumer] Received: {command}")

        if cmd == "start":
            self.engine.resume()
            print("[CommandConsumer] Simulation resumed")

        elif cmd == "stop":
            self.engine.pause()
            print("[CommandConsumer] Simulation paused")

        elif cmd == "set_current":
            current = float(command.get("current", 0.0))
            self.engine.set_current(current)
            print(f"[CommandConsumer] Current set to {current}A")

        elif cmd == "reset":
            soc = float(command.get("soc", 0.9))
            self.engine.reset(soc)
            print(f"[CommandConsumer] Simulation reset to SOC={soc*100:.0f}%")

        elif cmd == "set_profile":
            profile = command.get("profile", [])
            if profile:
                self.engine.set_profile(profile)
                print(f"[CommandConsumer] Profile set: {len(profile)} segments")

        else:
            print(f"[CommandConsumer] Unknown command: {cmd}")

    def stop(self):
        """Stop the consumer."""
        self.running = False
        if self.consumer:
            try:
                self.consumer.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)
        print("[CommandConsumer] Stopped")
