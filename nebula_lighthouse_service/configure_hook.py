#!/usr/bin/env python3

from nebula_lighthouse_service import nebula_config
from nebula_lighthouse_service import snap_config
from nebula_lighthouse_service.snap_services import restart_webserver_service
from nebula_lighthouse_service.webservice import web_config

def main():
    web_config['CONFIG_PATH'].mkdir(exist_ok=True)

    web_config.set_web_port(web_config['web_port'])
    web_config.set_web_ip(web_config['web_ip'])
    restart_webserver_service()

    web_config.set_min_port(web_config['min_port'])
    web_config.set_max_port(web_config['max_port'])

if __name__ == '__main__':
    main()
