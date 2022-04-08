from setuptools import setup, find_packages

setup(
    name='nebula_lighthouse_service',
    version='1.0.0',
    url='https://github.com/mypackage.git',
    author='Author Name',
    author_email='author@gmail.com',
    description='Description of my package',
    packages=find_packages(),
    install_requires=[
        'fastapi==0.75.1',
        'PyYAML==6.0',
        'uvicorn==0.17.6',
        'pydantic==1.9.0',
    ],
    scripts=[
        './nebula_lighthouse_service/configure_hook.py',
    ],
    entry_points=dict(
        console_scripts=['webservice = nebula_lighthouse_service.webservice:main'],
    ),
)
