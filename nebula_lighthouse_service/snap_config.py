from __future__ import annotations

import json
import subprocess


def get_config(name, default):
    output = subprocess.check_output(['snapctl', 'get', '-d', name])
    if output == b'':
        return default

    config = json.loads(output)
    return config.get(name, default)


def get_ports():
    min_port = max(1, int(get_config('min-port', 49152)))
    max_port = min(65535, int(get_config('max-port', 65535)))
    return min_port, max_port

def get_min_port():
    min_port = max(1, int(get_config('min-port', 49152)))
    return min_port

def get_max_port():
    max_port = min(65535, int(get_config('max-port', 65535)))
    return max_port

def get_webserver_port():
    port = min(65535, max(1, int(get_config('webserver.port', 80))))
    return port


def set_webserver_port(port: int):
    subprocess.check_call(['snapctl', 'set',
                           f'webserver.port={int(port)}',
                           ])


def set_ports(min_port, max_port):
    subprocess.check_call(['snapctl', 'set',
                           f'min-port={int(min_port)}',
                           f'max-port={int(max_port)}'
                           ])

def set_min_port(min_port):
    subprocess.check_call(['snapctl', 'set',
                           f'min-port={int(min_port)}',
                           ])

def set_max_port(max_port):
    subprocess.check_call(['snapctl', 'set',
                           f'max-port={int(max_port)}'
                           ])
