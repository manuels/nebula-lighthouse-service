import subprocess


def enable_lighthouse_service(lighthouse_index):
    service_name = f'nebula-lighthouse-service.lighthouse-{int(lighthouse_index)}'
    cmd = ('snapctl', 'start', service_name, '--enable')
    subprocess.check_call(cmd)


def restart_lighthouse_service(lighthouse_index):
    service_name = f'nebula-lighthouse-service.lighthouse-{int(lighthouse_index)}'
    cmd = ('snapctl', 'restart', service_name)
    subprocess.check_call(cmd)


def restart_webserver_service():
    service_name = f'nebula-lighthouse-service.webservice'
    cmd = ('snapctl', 'restart', service_name)
    subprocess.check_call(cmd)


def start_lighthouse_service(lighthouse_index):
    service_name = f'nebula-lighthouse-service.lighthouse-{int(lighthouse_index)}'
    cmd = ('snapctl', 'start', service_name)
    subprocess.check_call(cmd)


def is_lighthouse_service_running(lighthouse_index):
    service_name = f'nebula-lighthouse-service.lighthouse-{int(lighthouse_index)}'
    cmd = ('snapctl', 'services', service_name)
    output = subprocess.check_output(cmd, encoding='utf-8')
    return 'inactive' not in output