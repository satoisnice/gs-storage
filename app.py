import connexion
from connexion import NoContent
import json
import functools
from datetime import datetime, timezone
import logging
import logging.config
import yaml
from sqlalchemy import select
import threading
from kafka import KafkaConsumer

from db import make_session
from models import ServerHealthReading, PlayerTelemetryEvent

# using ISO 8601 UTC
# these files wil be change to url e.g., http://localhost:8088/event/somethign
# change to mysql e.g., mysql://gs_user:computer@localhost
with open("app_conf.yml", "r") as f:
    APP_CONFIG = yaml.safe_load(f.read())

with open("log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


def parse_dt(s):
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)  # naive UTC
    return dt

def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

def process_messages():
    """ Process event messages from Kafka """
    hostname = f"{APP_CONFIG['events']['hostname']}:{APP_CONFIG['events']['port']}"
    topic = APP_CONFIG['events']['topic']
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[hostname],
        group_id='event_group',
        auto_offset_reset='latest',
        enable_auto_commit=False,
        api_version=(3, 7, 0),
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    logger.info(f"Kafka Consumer started. Connected to {hostname} on topic '{topic}'")

    for msg in consumer:
        msg_payload = msg.value
        msg_type = msg_payload.get("type")
        payload = msg_payload.get("payload")
        trace_id = payload.get("trace_id") if payload else "unknown"

        logger.info(f"Received {msg_type} message with trace_id: {trace_id}")

        session = make_session()
        try:
            if msg_type == "server_health":
                event = ServerHealthReading(
                    trace_id=payload["trace_id"],
                    server_id=payload["server_id"],
                    sent_timestamp=parse_dt(payload["sent_timestamp"]),
                    batch_id=payload["batch_id"],
                    server_region=payload["server_region"],
                    server_location=payload.get("server_location"),
                    active_players=payload["active_players"],
                    cpu_usage=payload["cpu_usage"],
                    ram_usage=payload["ram_usage"],
                    recorded_timestamp=parse_dt(payload["recorded_timestamp"]),
                )
                session.add(event)
                
            elif msg_type == "player_telemetry":
                event = PlayerTelemetryEvent(
                    trace_id=payload["trace_id"],
                    server_id=payload["server_id"],
                    sent_timestamp=parse_dt(payload["sent_timestamp"]),
                    batch_id=payload["batch_id"],
                    server_region=payload["server_region"],
                    player_id=payload["player_id"],
                    event_timestamp=parse_dt(payload["event_timestamp"]),
                    player_ping=payload["player_ping"],
                    player_level=payload.get("player_level"),
                    action=payload.get("action"),
                )
                session.add(event)

            session.commit()
            consumer.commit() 

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            session.rollback()
        finally:
            session.close()

@use_db_session
def get_server_health_readings(session, start_timestamp, end_timestamp):
    """Gets server health readings between start >= and end < """
    start = parse_dt(start_timestamp)
    end = parse_dt(end_timestamp)

    statement = (
        select(ServerHealthReading)
        .where(ServerHealthReading.date_created >= start)
        .where(ServerHealthReading.date_created < end)
        .order_by(ServerHealthReading.date_created.asc())
    )

    results = [
        row.to_dict()
        for row in session.execute(statement).scalars().all()
    ]

    logger.debug(
        "Found %d server health readings (start: %s, end: %s)",
        len(results), start, end
    )

    return results, 200

# @use_db_session
# def report_server_health_reading(session, body):
#     # body is a SINGLE flattened object (storage YAML)
#     event = ServerHealthReading(
#         trace_id=body["trace_id"],

#         server_id=body["server_id"],
#         sent_timestamp=parse_dt(body["sent_timestamp"]),
#         batch_id=body["batch_id"],
#         server_region=body["server_region"],

#         server_location=body.get("server_location"),
#         active_players=body["active_players"],
#         cpu_usage=body["cpu_usage"],
#         ram_usage=body["ram_usage"],
#        recorded_timestamp=parse_dt(body["recorded_timestamp"]),
#     )
#     session.add(event)
#     session.commit()
#     logger.debug("Stored event server_health with a trace id of %s", body["trace_id"])
#     return NoContent, 201

@use_db_session
def get_player_telemetry_events(session, start_timestamp, end_timestamp):
    """Gets player telemetry events between start >= and end <"""
    start = parse_dt(start_timestamp)
    end = parse_dt(end_timestamp)

    statement = (
        select(PlayerTelemetryEvent)
        .where(PlayerTelemetryEvent.date_created >= start)
        .where(PlayerTelemetryEvent.date_created < end)
        .order_by(PlayerTelemetryEvent.date_created.asc())
    )

    results = [
        row.to_dict()
        for row in session.execute(statement).scalars().all()
    ]

    logger.debug(
        "Found %d player telemetry events (start: %s, end: %s)",
        len(results), start, end
    )
    
    return results, 200

# @use_db_session
# def report_player_telemetry_event(session, body):
#     event = PlayerTelemetryEvent(
#         trace_id=body["trace_id"],

#         server_id=body["server_id"],
#         sent_timestamp=parse_dt(body["sent_timestamp"]),
#         batch_id=body["batch_id"],
#         server_region=body["server_region"],

#         player_id=body["player_id"],
#         event_timestamp=parse_dt(body["event_timestamp"]),
#         player_ping=body["player_ping"],
#         player_level=body.get("player_level"),
#         action=body.get("action"),
#     )
#     session.add(event)
#     session.commit()
#     logger.debug("Stored event player_telemetry with a trace id of %s", body["trace_id"])
#     return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("game_server_api.yml",
            strict_validation=True,
            validate_responses=True)

if __name__ == "__main__":
    t = threading.Thread(target=process_messages)
    t.daemon = True
    t.start()
    app.run(port=8089, host="0.0.0.0")