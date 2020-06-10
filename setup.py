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
        'vtk>=8.1'
    ],
    extras_require={
        'dev': [
            'coveralls>=2.0',
            'mkdocs>=1.1',
            'pytest>=5.4',
            'pytest-flake8>=1.0',
            'pytest-cov>=2.8',
        ],
    },
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'krak = krak.__main__:main',
            ],
        },
    )
