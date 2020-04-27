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
        'pytest',
        'pytest-flake8',
        'flask',
        'docker',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'krak = krak.__main__:main',
            ],
        },
    )
