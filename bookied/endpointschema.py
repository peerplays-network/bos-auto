#: Default incident schema as sent from the data proxy
schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Bookie dataproxy Json",
    "description": "Bookie dataproxy exchange event trigger format",
    "type": "object",
    "properties": {
        "id": {
            "type": "object",
            "properties": {
                "sport": {
                    "description": "The unique name of the sport, in english",
                    "type": "string"
                },
                "event_group_name": {
                    "description": "The unique name of the event group, in english (e.g. the league)",
                    "type": "string"
                },
                "start_time": {
                    "description": "The start time of the event in UTC, ISO format",
                    "type": "string",
                    "format": "date-time"
                },
                "home": {
                    "description": "The unique name of the home team, in english",
                    "type": "string"
                },
                "away": {
                    "description": "The unique name of the away team, in english",
                    "type": "string"
                },
            },
            "required": ["sport", "event_group_name", "start_time", "home", "away"]
        },
        "call": {
            "description": "The trigger that was called",
            "type": "string",
            "enum": ["create", "in_progress", "finish", "result", "unknown", "settle"]
        },
        "arguments": {
            "type": "object",
            "properties": {
                "season": {
                    "description": "The unique season of the sport",
                    "type": "string"
                },
                "whistle_start_time": {
                    "description": "The time the end was whistled on in UTC, ISO format",
                    "type": "string",
                    "format": "date-time"
                },
                "whistle_end_time": {
                    "description": "The time the end was whistled off in UTC, ISO format",
                    "type": "string",
                    "format": "date-time"
                },
                "home_score": {
                    "description": "The score of the home team",
                    "type": "string"
                },
                "away_score": {
                    "description": "The score of the away team",
                    "type": "string"
                }
            }
        }
    },
    "required": ["id", "call", "arguments"]
}
