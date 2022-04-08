from pydantic import BaseModel, validator
import uvicorn as uvicorn
from fastapi import FastAPI

from nebula_lighthouse_service import snap_config, nebula_config

app = FastAPI()


def is_nebula_crt(crt: str) -> str:
    if crt.isascii() and crt.startswith('-----BEGIN NEBULA CERTIFICATE-----'):
        return crt
    else:
        raise ValueError('must be a valid NEBULA CERTIFICATE')


class Lighthouse(BaseModel):
    ca_crt: str
    host_crt: str
    host_key: str

    @validator('ca_crt')
    def ca_is_nebula_cert(cls, ca_crt: str) -> str:
        return is_nebula_crt(ca_crt)

    @validator('host_crt')
    def host_is_nebula_cert(cls, host_crt: str) -> str:
        return is_nebula_crt(host_crt)

    @validator('host_key')
    def host_is_nebula_key(cls, host_key: str) -> str:
        if host_key.isascii() and host_key.startswith('-----BEGIN NEBULA') and ' PRIVATE KEY-----' in host_key:
            return host_key
        else:
            raise ValueError('must be a valid NEBULA PRIVATE KEY')


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/lighthouse/")
async def create_lighthouse(lighthouse: Lighthouse):
    lighthouse_id = await snap_config.add_lighthouse(lighthouse.ca_crt,
                                                     lighthouse.host_crt,
                                                     lighthouse.host_key)
    port = nebula_config.get_port(lighthouse_id)

    return {"port": port}


def main():
    port = snap_config.get_webserver_port()
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
