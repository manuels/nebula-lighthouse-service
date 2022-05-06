#!/usr/bin/env python3
from pathlib import Path

import requests


def main():
    path = Path(__file__).parent

    data = dict(ca_crt=(path / 'ca.crt').read_text(),
                host_crt=(path / 'lighthouse2.crt').read_text(),
                host_key=(path / 'lighthouse2.key').read_text(),
                )
    print(data)
    r = requests.post('http://localhost:80/lighthouse/', data=data)
    r.raise_for_status()
    print(r.json())

    r = requests.get('http://localhost:80/lighthouse/', data=data)
    r.raise_for_status()
    print(r.json())


if __name__ == '__main__':
    main()
