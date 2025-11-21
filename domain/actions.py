from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class DesignAction:
    name: str
    action_type: str
    params: Dict[str, object]

