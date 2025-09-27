from __future__ import annotations

import subprocess
import yaml
import pathlib
from nebula_lighthouse_service.nebula_config import CONFIG_PATH

def get_config(name, default):
    try:
        contents = (CONFIG_PATH / 'config.yaml').read_text()
        cfg = yaml.safe_load(contents)
        output = cfg[name]
    except:
        return default
    return output


def get_ports():
    min_port = max(1, int(get_config('min-port', 49152)))
    max_port = min(65535, int(get_config('max-port', 65535)))
    return min_port, max_port


def get_webserver_port():
    port = min(65535, max(1, int(get_config('webserver.port', 8080))))
    return port

