"""Alert callbacks for the health-claims DAG. Logs by default; set HCW_ALERT_WEBHOOK to post to a chat webhook."""
from __future__ import annotations

import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)


def deadline_missed(context=None, dag_id: str = "", **_) -> None:
    message = f"{dag_id}: run missed its 2-hour deadline"
    log.error(message)
    url = os.environ.get("HCW_ALERT_WEBHOOK")
    if url:
        req = urllib.request.Request(url, data=json.dumps({"text": message}).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
