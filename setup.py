from setuptools import setup

import krak


setup(
    name=krak.__name__,
    version=krak.__version__,
    description=krak.__description__,
    url=krak.__url__,
    author=krak.__author__,
    author_email=krak.__email__,
    install_requires=[
        'connextion[swagger-ui]',
        'docker',
        'flask',
        'pytest',
        'pytest-flake8',
        'sqlalchemy',
        'sphinx',
	'sphinxcontrib-openapi',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'krak = krak.__main__:main',
            ],
        },
    )
