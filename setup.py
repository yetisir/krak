from setuptools import setup


setup(
    name='krak',
    version='0.1.1',
    description='KraK Python Library',
    url='http://github.com/yetisir/krak',
    author='M.Yetisir',
    author_email='yetisir@gmail.com',
    install_requires=[
        'vtk>=8.1',
        'pyvista>=0.24',
        'meshio[all]>=4.0',
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
)
