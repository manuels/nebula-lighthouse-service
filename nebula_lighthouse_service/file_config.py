from __future__ import annotations

import subprocess
import yaml
import pathlib

def get_config(path, name, default):
    try:
        contents = (path).read_text()
        cfg = yaml.safe_load(contents)
        output = cfg[name]
    except:
        return default
    return output


def get_ports(path):
    min_port = max(1, int(get_config(path, 'min-port', 49152)))
    max_port = min(65535, int(get_config(path, 'max-port', 65535)))
    return min_port, max_port

def get_min_port(path):
    min_port = max(1, int(get_config(path, 'min-port', 49152)))
    return min_port

def get_max_port(path):
    max_port = min(65535, int(get_config(path, 'max-port', 65535)))
    return max_port

def get_webserver_port(path):
    port = min(65535, max(1, int(get_config(path, 'webserver.port', 8080))))
    return port

