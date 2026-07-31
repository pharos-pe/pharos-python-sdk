"""JSON type aliases used by parsers and transports."""

from __future__ import annotations

from typing import Dict, List, Union

JSONValue = Union[None, bool, int, float, str, List["JSONValue"], Dict[str, "JSONValue"]]
JSONObject = Dict[str, JSONValue]
QueryParams = Dict[str, Union[str, int]]
