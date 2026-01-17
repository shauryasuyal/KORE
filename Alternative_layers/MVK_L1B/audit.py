import json
import datetime

class AuditLogger:
    def __init__(self, path: str):
        self.path = path

    def log(self, plan_id, index, op, status):
        entry = {
            "time": datetime.datetime.utcnow().isoformat(),
            "plan_id": plan_id,
            "index": index,
            "source": op["source"],
            "destination": op["destination"],
            "status": status
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
