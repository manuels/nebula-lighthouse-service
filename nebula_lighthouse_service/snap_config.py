from __future__ import annotations

import asyncio
import json
import re
import subprocess
from typing import Optional


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


def parse_lighthouse_name(name: str) -> Optional[int]:
    match = re.match('^lighthouse-([0-9]+)$', name)
    if not match:
        return None

    try:
        number = int(match.group(1))
    except ValueError:
        return None

    return number


def get_lighthouses() -> dict[int, dict[str]]:
    output = subprocess.check_output('snapctl get -d lighthouses'.split())
    config = json.loads(output)
    config = config.get('lighthouses', {})

    lighthouse_configs = {parse_lighthouse_name(lighthouse_name): cfg
                          for lighthouse_name, cfg in config.items()}

    lighthouse_configs[None] = None
    del lighthouse_configs[None]

    lighthouse_configs = dict(sorted(lighthouse_configs.items()))

    return lighthouse_configs


def is_same_config(cfg: dict, ca_crt: str, host_crt: str, host_key: str) -> bool:
    return (cfg.get('ca', '') == ca_crt
            and cfg.get('cert', '') == host_crt
            and cfg.get('key', '') == host_key)


async def add_lighthouse(ca_crt: str, host_crt: str, host_key: str) -> int:
    configs = get_lighthouses()

    existing = (lighthouse_id for lighthouse_id, cfg in configs.items()
                if is_same_config(cfg, ca_crt, host_crt, host_key))
    lighthouse_id = next(existing, None)
    if lighthouse_id is not None:
        return lighthouse_id

    lighthouse_id_lists = configs.keys()
    lighthouse_id = max(lighthouse_id_lists, default=-1) + 1

    cfg_prefix = f'lighthouses.lighthouse-{lighthouse_id}'

    cmd = ['snapctl', 'set', 'nebula-lighthouse-service',
           f'{cfg_prefix}.ca={ca_crt}',
           f'{cfg_prefix}.cert={host_crt}',
           f'{cfg_prefix}.key={host_key}',
           ]
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()

    return lighthouse_id
