from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, Float, DateTime, func, BigInteger
from datetime import datetime, timezone
from decimal import Decimal

def _dt_to_iso(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _num(n):
    return float(n) if isinstance(n, Decimal) else n

class Base(DeclarativeBase):
    pass

class ServerHealthReading(Base):
    __tablename__ = "server_health_readings"

    id = mapped_column(Integer, primary_key=True)

    trace_id = mapped_column(BigInteger, nullable=False)

    # batch
    server_id = mapped_column(String(36), nullable=False)
    sent_timestamp = mapped_column(DateTime, nullable=False)
    batch_id = mapped_column(String(36), nullable=False)
    server_region = mapped_column(String(50), nullable=False)

    # reading
    server_location = mapped_column(String(100), nullable=True)
    active_players = mapped_column(Integer, nullable=False)
    cpu_usage = mapped_column(Float, nullable=False)
    ram_usage = mapped_column(Float, nullable=False)
    recorded_timestamp = mapped_column(DateTime, nullable=False)

    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "server_id": str(self.server_id),
            "sent_timestamp": _dt_to_iso(self.sent_timestamp),
            "batch_id": str(self.batch_id),
            "server_region": self.server_region,
            "server_location": self.server_location,
            "active_players": self.active_players,
            "cpu_usage": _num(self.cpu_usage),
            "ram_usage": _num(self.ram_usage),
            "recorded_timestamp": _dt_to_iso(self.recorded_timestamp),
            # only include this if it exists in your OpenAPI schema:
            # "date_created": _dt_to_iso(self.date_created),
        }


class PlayerTelemetryEvent(Base):
    __tablename__ = "player_telemetry_events"

    id = mapped_column(Integer, primary_key=True)

    trace_id = mapped_column(BigInteger, nullable=False)

    # batch
    server_id = mapped_column(String(36), nullable=False)
    # when did server send
    sent_timestamp = mapped_column(DateTime, nullable=False)
    batch_id = mapped_column(String(36), nullable=False)

    # event
    player_id = mapped_column(String(36), nullable=False)
    # when was event recorded
    event_timestamp = mapped_column(DateTime, nullable=False)
    player_ping = mapped_column(Integer, nullable=False)
    player_level = mapped_column(Integer, nullable=True)
    action = mapped_column(String(30), nullable=True)
    server_region = mapped_column(String(50), nullable=False)

    # when did it get stored in db
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "server_id": str(self.server_id),
            "sent_timestamp": _dt_to_iso(self.sent_timestamp),
            "batch_id": str(self.batch_id),
            "server_region": getattr(self, "server_region", None),  # only if you store it
            "player_id": str(self.player_id),
            "event_timestamp": _dt_to_iso(self.event_timestamp),
            "player_ping": self.player_ping,
            "player_level": self.player_level,
            "action": self.action,
            "date_created": _dt_to_iso(self.date_created),
        }

