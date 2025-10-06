from __future__ import annotations

import asyncio
import dataclasses
import logging
import re
import os
import argparse
from typing import Tuple
from pathlib import Path

import importlib.resources
from pydantic import BaseModel, validator
import uvicorn as uvicorn
from fastapi import FastAPI, File
from starlette.responses import HTMLResponse

from nebula_lighthouse_service import snap_config, nebula_config, file_config
from nebula_lighthouse_service.nebula_config import NEBULA_PATH
from nebula_lighthouse_service.version import __version__

app = FastAPI()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

RE_NEBULA = re.compile(r'^[ A-Za-z0-9+/\r\n-=]+$')


def is_nebula_crt(crt: str) -> str:
    if RE_NEBULA.match(crt) and crt.startswith('-----BEGIN NEBULA CERTIFICATE-----'):
        return crt
    else:
        raise ValueError('must be a valid NEBULA CERTIFICATE')

class Web_config(dict):

    def __init__(
            self,
            CONFIG_PATH = Path('/etc/nebula-lighthouse-service/config.yaml'),
            LIGHTHOUSE_PATH = Path('/var/lib/nebula-lighthouse-service'),
            min_port = 49152,
            max_port = 65535,
            web_port = 8080,
            web_ip = "0.0.0.0",
            IS_SNAP = False
    ):
        try:
            os.environ['SNAP']
            dict.__init__(
                self,
                IS_SNAP = True,
                CONFIG_PATH = Path(os.environ['SNAP_COMMON']) / 'config',
                LIGHTHOUSE_PATH = Path(os.environ['SNAP_COMMON']) / 'config',
                min_port = snap_config.get_min_port(),
                max_port = snap_config.get_max_port(),
                web_port = snap_config.get_webserver_port(),
                web_ip = snap_config.get_webserver_ip()
                )

        except:
            dict.__init__(
                self,
                IS_SNAP = False,
                CONFIG_PATH = Path('/etc/nebula-lighthouse-service/config.yaml'),
                LIGHTHOUSE_PATH = Path('/var/lib/nebula-lighthouse-service'),
                min_port = file_config.get_min_port(CONFIG_PATH),
                max_port = file_config.get_max_port(CONFIG_PATH),
                web_port = file_config.get_webserver_port(CONFIG_PATH),
                web_ip = file_config.get_webserver_ip(CONFIG_PATH)
            )

    def set_lighthouse_path(self, path):
        self['LIGHTHOUSE_PATH'] = path

    def set_min_port(self, port):
        self['min_port'] = port
        if self['IS_SNAP']:
            snap_config.set_min_port(port)

    def set_max_port(self, port):
        self['max_port'] = port
        if self['IS_SNAP']:
            snap_config.set_max_port(port)

    def set_web_port(self, port):
        self['web_port'] = port
        if self['IS_SNAP']:
            snap_config.set_webserver_port(port)

    def set_web_ip(self, address):
        self['web_ip'] = address
        if self['IS_SNAP']:
            snap_config.set_webserver_ip(address)


web_config = Web_config()

class Lighthouse(BaseModel):
    ca_crt: str
    host_crt: str
    host_key: str

    def __hash__(self):
        return hash((self.ca_crt, self.host_crt, self.host_key))

    @validator('ca_crt')
    def ca_is_nebula_cert(cls, ca_crt: str) -> str:
        return is_nebula_crt(ca_crt)

    @validator('host_crt')
    def host_is_nebula_cert(cls, host_crt: str) -> str:
        return is_nebula_crt(host_crt)

    @validator('host_key')
    def host_is_nebula_key(cls, host_key: str) -> str:
        if RE_NEBULA.match(host_key) and host_key.startswith('-----BEGIN NEBULA') and ' PRIVATE KEY-----' in host_key:
            return host_key
        else:
            raise ValueError('must be a valid NEBULA PRIVATE KEY')


@dataclasses.dataclass
class LighthouseDaemon:
    port: int
    process: asyncio.subprocess.Process


nebula_lighthouses: dict[Lighthouse, LighthouseDaemon] = {}


@app.on_event("startup")
async def startup():
    log.info('starting nebula services...')
    for path in nebula_config.get_existing_configs(web_config['LIGHTHOUSE_PATH']):
        try:
            ca_crt, host_crt, host_key, port = nebula_config.read_config(path)
        except Exception:
            continue
        log.info('starting nebula', path, port)

        cmd = [f'{NEBULA_PATH}/nebula', '-config', path]
        proc = await asyncio.create_subprocess_exec(*cmd)

        lighthouse = Lighthouse(ca_crt=ca_crt, host_crt=host_crt, host_key=host_key)
        daemon = LighthouseDaemon(port, proc)

        asyncio.create_task(run_nebula(lighthouse, daemon))
        nebula_lighthouses[lighthouse] = daemon


@app.on_event("shutdown")
async def shutdown():
    for daemon in nebula_lighthouses.values():
        daemon.process.kill()


@app.get("/")
async def index():
    return HTMLResponse(importlib.resources.files(__name__).joinpath('static/index.html').read_bytes())


async def start_nebula(lighthouse: Lighthouse) -> Tuple[int, asyncio.subprocess.Process]:
    port = web_config['min_port'] + len(list(nebula_config.get_existing_configs(web_config['LIGHTHOUSE_PATH'])))
    if port > web_config['max_port']:
        raise ValueError('Too many nebula lighthouse services already running')

    config = nebula_config.create_config(lighthouse.ca_crt, lighthouse.host_crt, lighthouse.host_key, port)
    nebula_config.test_config(config)

    path = nebula_config.get_lighthouse_path(web_config['LIGHTHOUSE_PATH'], port)
    path.write_text(config)

    cmd = [f'{NEBULA_PATH}/nebula', '-config', path]
    proc = await asyncio.create_subprocess_exec(*cmd)
    return port, proc


async def run_nebula(lighthouse: Lighthouse, daemon: LighthouseDaemon):
    try:
        await daemon.process.wait()
    finally:
        del nebula_lighthouses[lighthouse]


@app.post("/lighthouse/")
async def create_lighthouse(ca_crt: bytes = File(...),
                            host_crt: bytes = File(...),
                            host_key: bytes = File(...),
                            ):
    lighthouse = Lighthouse(ca_crt=ca_crt.decode('ascii'),
                            host_crt=host_crt.decode('ascii'),
                            host_key=host_key.decode('ascii'))
    if lighthouse not in nebula_lighthouses:
        port, proc = await start_nebula(lighthouse)
        daemon = LighthouseDaemon(port, proc)
        nebula_lighthouses[lighthouse] = daemon

        asyncio.create_task(run_nebula(lighthouse, daemon))
    else:
        daemon = nebula_lighthouses[lighthouse]

    return dict(port=daemon.port)


@app.get("/lighthouse/")
async def lighthouse_status(ca_crt: bytes = File(...),
                            host_crt: bytes = File(...),
                            host_key: bytes = File(...),
                            ):
    lighthouse = Lighthouse(ca_crt=ca_crt.decode('ascii'),
                            host_crt=host_crt.decode('ascii'),
                            host_key=host_key.decode('ascii'))
    daemon = nebula_lighthouses.get(lighthouse)
    is_running = daemon is not None
    response = dict(running=is_running)
    if is_running:
        response['port'] = daemon.port

    return response


def main():
    parser = argparse.ArgumentParser(prog= ''.join(['nebula-lighthouse-service ','v',__version__]) )
    parser.add_argument('--config', help='path of config file')
    parser.add_argument('--lh-path', help='path for lighthouse files')
    parser.add_argument('--min-port', help='min port for lighthouse')
    parser.add_argument('--max-port', help='max port for lighthouse')
    parser.add_argument('--web-port', help='web server port')
    parser.add_argument('--web-ip', help='web server ip address')
    args = parser.parse_args()

    for key, value in vars(args).items():
        if value is not None:
            if key == 'config':
                web_config.__init__(CONFIG_PATH = Path(value))
            elif key == 'lh_path':
                web_config.set_lighthouse_path(Path(value))
            elif key == 'min_port':
                web_config.set_min_port(int(value))
            elif key == 'max_port':
                web_config.set_max_port(int(value))
            elif key == 'web_port':
                web_config.set_web_port(int(value))
            elif key == 'web_ip':
                web_config.set_web_ip(str(value))

    uvicorn.run(app, host=web_config['web_ip'], port=web_config['web_port'])


if __name__ == "__main__":
    main()
