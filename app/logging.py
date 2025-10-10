import json
import logging
from typing import Any, Dict


with open("app/logging.json", "r", encoding="utf-8") as f:
    API_LOG_CONFIG: Dict[str, Any] = json.load(f)


logger: logging.Logger = logging.getLogger("spotthespy")
