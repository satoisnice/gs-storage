import connexion
from connexion import NoContent
import os
import json
from datetime import datetime

MAX_BATCH_EVENTS = 5 
# these files wil be change to url e.g., http://localhost:8088/event/somethign
PLAYER_TELEMETRY_FILE = "./player_telemetry.json"
SERVER_HEALTH_FILE = "./server_health.json"

def _save(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def report_server_health_readings(body):
    """ Receives a server health reading batch event """
    if os.path.exists(SERVER_HEALTH_FILE):
        with open(SERVER_HEALTH_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {} 
    
    if "num_server_health_batches" not in data:
        data["num_server_health_batches"] = 0
    
    if "recent_batch_data" not in data:
        data["recent_batch_data"] = []

    data["num_server_health_batches"] += 1

    total_cpu = 0
    total_ram = 0
    total_players = 0
    max_players = 0
    count = 0
    
    for reading in body["readings"]:
        total_cpu += reading["cpu_usage"]
        total_ram += reading["ram_usage"]
        total_players += reading["active_players"]

        if reading["active_players"] > max_players:
            max_players = reading["active_players"]

        count += 1
    
    cpu_avg = total_cpu / count if count > 0 else 0
    ram_avg = total_ram / count if count > 0 else 0
    players_avg = total_players / count if count > 0 else 0

    batch_summary = {
        "cpu_average_percent": cpu_avg,
        "ram_average_percent": ram_avg,
        "avg_active_players": players_avg,
        "max_active_players": max_players,
        "num_readings": count,
        "received_timestamp": str(datetime.now())
    }

    data["recent_batch_data"].append(batch_summary)

    while len(data["recent_batch_data"]) > MAX_BATCH_EVENTS:
        data["recent_batch_data"].pop(0)

    _save(SERVER_HEALTH_FILE, data)

    return NoContent, 201

def report_player_telemetry_event(body):
    """ Receives a player telemetry event """
    if os.path.exists(PLAYER_TELEMETRY_FILE):
        with open(PLAYER_TELEMETRY_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    if "num_player_telemetry_batches" not in data:
        data["num_player_telemetry_batches"] = 0
    
    if "recent_batch_data" not in data:
        data["recent_batch_data"] = []
    
    
    data["num_player_telemetry_batches"] += 1

    events = body["events"]

    count = 0
    total_ping = 0
    min_ping = None
    max_ping = None

    total_level = 0
    level_count = 0

    action_counts = {}
    
    for event in body["events"]:
        count += 1

        ping = event["player_ping"]
        total_ping += ping

        if min_ping is None or ping < min_ping:
            min_ping = ping
        if max_ping is None or ping > max_ping:
            max_ping = ping
        
        if "action" in event and event["action"] is not None:
            action = event["action"]
            if action not in action_counts:
                action_counts[action] = 0
            action_counts[action] += 1
        
        if "player_level" in event and event["player_level"] is not None:
            total_level += event["player_level"]
            level_count += 1

    avg_ping = total_ping / count if count > 0 else 0
    avg_level = (total_level / level_count) if level_count > 0 else 0

    batch_summary = {
        "ping_average_ms": avg_ping,
        "min_ping_ms": min_ping if min_ping is not None else 0,
        "max_ping_ms": max_ping if max_ping is not None else 0,
        "num_events": count,
        "action_counts": action_counts,
        "avg_player_level": avg_level,
        "received_timestamp": str(datetime.now())
    }

    data["recent_batch_data"].append(batch_summary)

    while len(data["recent_batch_data"]) > MAX_BATCH_EVENTS:
        data["recent_batch_data"].pop(0)
    
    _save(PLAYER_TELEMETRY_FILE, data)

    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("game_server_api.yml",
            strict_validation=True,
            validate_responses=True)


if __name__ == "__main__":
    app.run(port=8088)