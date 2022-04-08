#!/usr/bin/env python3

import contextlib
from nebula_lighthouse_service import nebula_config
from nebula_lighthouse_service import snap_config
from nebula_lighthouse_service.snap_services import enable_lighthouse_service, restart_lighthouse_service, \
    start_lighthouse_service, is_lighthouse_service_running, restart_webserver_service


def main():
    nebula_config.CONFIG_PATH.mkdir(exist_ok=True)

    webserver_port = snap_config.get_webserver_port()
    snap_config.set_webserver_port(webserver_port)
    restart_webserver_service()

    min_port, max_port = snap_config.get_ports()
    snap_config.set_ports(min_port=min_port, max_port=max_port)

    for lighthouse_index, cfg in snap_config.get_lighthouses().items():
        lighthouse_config_path = nebula_config.get_config_path(lighthouse_index)

        port = min_port + lighthouse_index

        if port > max_port:
            raise ValueError(f'Too many lighthouses for max_port = {max_port}')

        ca = str(cfg.get('ca', ''))
        cert = str(cfg.get('cert', ''))
        key = str(cfg.get('key', ''))

        new_config = nebula_config.create_config(ca, cert, key, port)

        with contextlib.suppress(FileNotFoundError):
            old_config = ''
            old_config = lighthouse_config_path.read_text()

        if old_config != new_config:
            nebula_config.test_config(new_config)
            lighthouse_config_path.write_text(new_config)

        enable_lighthouse_service(lighthouse_index)

        if is_lighthouse_service_running(lighthouse_index):
            if old_config == new_config:
                # config did not change and is still running
                pass
            else:
                restart_lighthouse_service(lighthouse_index)
        else:
            start_lighthouse_service(lighthouse_index)


if __name__ == '__main__':
    main()
