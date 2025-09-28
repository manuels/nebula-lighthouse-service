from __future__ import annotations

import asyncio
import dataclasses
import logging
import re
from typing import Tuple

import importlib.resources
from pydantic import BaseModel, validator
import uvicorn as uvicorn
from fastapi import FastAPI, File
from starlette.responses import HTMLResponse

from nebula_lighthouse_service import snap_config, nebula_config, web_config
from nebula_lighthouse_service.nebula_config import NEBULA_PATH, IS_SNAP

app = FastAPI()

log = logging.getLogger()
log.setLevel(logging.DEBUG)

RE_NEBULA = re.compile(r'^[ A-Za-z0-9+/\r\n-=]+$')


def is_nebula_crt(crt: str) -> str:
    if RE_NEBULA.match(crt) and crt.startswith('-----BEGIN NEBULA CERTIFICATE-----'):
        return crt
    else:
        raise ValueError('must be a valid NEBULA CERTIFICATE')


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
    for path in nebula_config.get_existing_configs():
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
    if IS_SNAP:
        min_port, max_port = snap_config.get_ports()
    else:
        min_port, max_port = web_config.get_ports()
    port = min_port + len(list(nebula_config.get_existing_configs()))
    if port > max_port:
        raise ValueError('Too many nebula lighthouse services already running')

    config = nebula_config.create_config(lighthouse.ca_crt, lighthouse.host_crt, lighthouse.host_key, port)
    nebula_config.test_config(config)

    path = nebula_config.get_lighthouse_path(port)
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
    if IS_SNAP:
        port = snap_config.get_webserver_port()
    else:
        port = web_config.get_webserver_port()

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
