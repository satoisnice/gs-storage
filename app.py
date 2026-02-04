import connexion
from connexion import NoContent
import os
import json
import functools
from datetime import datetime
import logging
import logging.config
import yaml

from db import make_session
from models import ServerHealthReading, PlayerTelemetryEvent

# these files wil be change to url e.g., http://localhost:8088/event/somethign
# change to mysql e.g., mysql://gs_user:computer@localhost
with open("log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

def _save(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
@use_db_session
def report_server_health_reading(session, body):
    # body is a SINGLE flattened object (storage YAML)
    event = ServerHealthReading(
        trace_id=body["trace_id"],

        server_id=body["server_id"],
        sent_timestamp=parse_dt(body["sent_timestamp"]),
        batch_id=body["batch_id"],
        server_region=body["server_region"],

        server_location=body.get("server_location"),
        active_players=body["active_players"],
        cpu_usage=body["cpu_usage"],
        ram_usage=body["ram_usage"],
        recorded_timestamp=parse_dt(body["recorded_timestamp"]),
    )
    session.add(event)
    session.commit()
    logger.debug("Stored event server_health with a trace id of %s", body["trace_id"])
    return NoContent, 201


@use_db_session
def report_player_telemetry_event(session, body):
    event = PlayerTelemetryEvent(
        trace_id=body["trace_id"],

        server_id=body["server_id"],
        sent_timestamp=parse_dt(body["sent_timestamp"]),
        batch_id=body["batch_id"],

        player_id=body["player_id"],
        event_timestamp=parse_dt(body["event_timestamp"]),
        player_ping=body["player_ping"],
        player_level=body.get("player_level"),
        action=body.get("action"),
    )
    session.add(event)
    session.commit()
    logger.debug("Stored event player_telemetry with a trace id of %s", body["trace_id"])
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("game_server_api.yml",
            strict_validation=True,
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8089)