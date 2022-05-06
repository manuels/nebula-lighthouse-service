#!/usr/bin/env python3

from nebula_lighthouse_service import nebula_config
from nebula_lighthouse_service import snap_config
from nebula_lighthouse_service.snap_services import restart_webserver_service


def main():
    nebula_config.CONFIG_PATH.mkdir(exist_ok=True)

    webserver_port = snap_config.get_webserver_port()
    snap_config.set_webserver_port(webserver_port)
    restart_webserver_service()

    min_port, max_port = snap_config.get_ports()
    snap_config.set_ports(min_port=min_port, max_port=max_port)


if __name__ == '__main__':
    main()
