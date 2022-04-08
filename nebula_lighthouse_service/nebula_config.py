import subprocess
import yaml
import os
from pathlib import Path

SNAP = Path(os.environ['SNAP'])
CONFIG_PATH = Path(os.environ['SNAP_COMMON']) / 'config'


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
    subprocess.run(f'{SNAP}/bin/nebula -test -config /dev/stdin'.split(),
                   check=True,
                   input=yaml_config.encode())


def get_port(lighthouse_id: int) -> int:
    lighthouse_config_path = get_config_path(lighthouse_id)
    contents = lighthouse_config_path.read_text()

    cfg = yaml.safe_load(contents)
    return cfg.get('listen', {})['port']


def get_config_path(lighthouse_index: int) -> Path:
    return CONFIG_PATH / f'lighthouse-{int(lighthouse_index)}.yaml'
