from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, Float, DateTime, func

class Base(DeclarativeBase):
    pass

class ServerHealthReading(Base):
    __tablename__ = "server_health_readings"

    id = mapped_column(Integer, primary_key=True)

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

class PlayerTelemetryEvent(Base):
    __tablename__ = "player_telemetry_events"

    id = mapped_column(Integer, primary_key=True)

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

    # when did it get stored in db
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
