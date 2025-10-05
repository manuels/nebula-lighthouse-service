from setuptools import setup, find_packages

setup(
    name='nebula_lighthouse_service',
    version = '2.0.0,
    url='https://github.com/manuels/nebula-lighthouse-service',
    author='manuels',
    maintainer='manuels bloominstrong',
    description='This server is a public Nebula VPN Lighthouse Service. You can use it in case you don’t have a publicly accessible server to run your own Nebula Lighthouse.',
    packages=find_packages(),
    package_data=dict(nebula_lighthouse_service=["static/*.html"]),
    install_requires=[
        'fastapi==0.116.1',
        'PyYAML==6.0.2',
        'uvicorn==0.35.0',
        'pydantic==1.10.21',
        'python-multipart==0.0.20',
    ],
    scripts=[
        './nebula_lighthouse_service/configure_hook.py',
    ],
    entry_points=dict(
        console_scripts=['nebula-lighthouse-service = nebula_lighthouse_service.webservice:main'],
    ),
)
