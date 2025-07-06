import json
import logging
from typing import Generator, Dict, Any
import requests

logger = logging.getLogger(__name__)


def generate_json_objects(
    resp: requests.Response,
) -> Generator[Dict[str, Any], None, None]:
    buffer = ""
    for chunk in resp.iter_content(chunk_size=8192, decode_unicode=True):
        buffer += chunk
        while True:
            try:
                obj = json.loads(buffer)
                yield obj
                buffer = ""
            except json.JSONDecodeError:
                break
    if buffer:
        logger.error(f"Incomplete JSON object in buffer at end of stream: {buffer}")
