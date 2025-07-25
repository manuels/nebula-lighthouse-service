from setuptools import setup, find_packages

setup(
    name='nebula_lighthouse_service',
    version='0.0.1',
    url='https://github.com/mypackage.git',
    author='Author Name',
    author_email='author@gmail.com',
    description='Description of my package',
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
        console_scripts=['webservice = nebula_lighthouse_service.webservice:main'],
    ),
)
