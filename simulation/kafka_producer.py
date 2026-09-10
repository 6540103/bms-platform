"""Kafka producer for sending real-time battery data and events."""

import json
import time
import threading
from kafka import KafkaProducer
from config import KAFKA_CONFIG


class BatteryKafkaProducer:
    def __init__(self):
        self.config = KAFKA_CONFIG
        self.producer = None
        self._lock = threading.Lock()
        self._connected = False
        self._connect()

    def _connect(self):
        """Connect to Kafka broker."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks=1,
                retries=3,
                linger_ms=10,
                request_timeout_ms=10000,
            )
            # Verify connection by fetching broker metadata
            self.producer.bootstrap_connected()
            self._connected = True
            print(f"[Kafka] Connected to {self.config['bootstrap_servers']}")
        except Exception as e:
            self._connected = False
            print(f"[Kafka] Connection failed: {e}")

    def send_realtime(self, state):
        """Send real-time battery state to bms.realtime topic (non-blocking)."""
        if not self._connected or not self.producer:
            return
        try:
            self.producer.send(
                self.config["realtime_topic"],
                key="bms-pack-01",
                value=state,
            )
        except Exception as e:
            print(f"[Kafka] Send error: {e}")

    def send_event(self, event_type, details=None):
        """Send an event to bms.events topic."""
        if not self._connected or not self.producer:
            return
        event = {
            "timestamp": time.time(),
            "event": event_type,
            "details": details or {},
        }
        try:
            self.producer.send(
                self.config["events_topic"],
                key="bms-pack-01",
                value=event,
            )
            self.producer.flush()
            print(f"[Kafka] Event sent: {event_type}")
        except Exception as e:
            print(f"[Kafka] Event send error: {e}")

    def flush(self):
        """Flush all pending messages."""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close producer connection."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception:
                pass
            self._connected = False
            print("[Kafka] Producer closed")
