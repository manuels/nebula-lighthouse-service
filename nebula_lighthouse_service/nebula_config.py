import subprocess
from typing import Iterator, Tuple

import yaml
import os
import shutil
from pathlib import Path

NEBULA_PATH = Path(shutil.which('nebula')).parent

def create_config(ca: str, cert: str, key: str, port: int) -> str:
    cfg = dict(
        lighthouse=dict(am_lighthouse=True),
        tun=dict(disabled=True),
        punchy=dict(
            punch=True,
            respond=True,
        ),
        listen=dict(port=int(port)),
        pki=dict(
            ca=ca,
            cert=cert,
            key=key,
        ),
    )

    return yaml.safe_dump(cfg)


def test_config(yaml_config: str):
    subprocess.run(f'{NEBULA_PATH}/nebula -test -config /dev/stdin'.split(),
                   check=True,
                   input=yaml_config.encode())


def read_config(path: Path) -> Tuple[str, str, str, int]:
    contents = path.read_text()
    cfg = yaml.safe_load(contents)

    pki = cfg.get('pki', {})
    ca_crt = pki['ca']
    host_crt = pki['cert']
    host_key = pki['key']
    port = cfg.get('listen', {})['port']

    return ca_crt, host_crt, host_key, port


def get_existing_configs(path) -> Iterator[Path]:
    return path.glob('lighthouse-*.yaml')


def get_lighthouse_path(path, lighthouse_index: int) -> Path:
    return path / f'lighthouse-{int(lighthouse_index)}.yaml'
