"""Setup script for e-ink barcode testing application."""

from setuptools import setup, find_packages

setup(
    name="eink-barcodes",
    version="0.1.0",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'PyQt6>=6.8.1',
        'Pillow>=11.1.0',
        'numpy>=2.2.3',
        'websockets>=15.0',
    ],
    extras_require={
        'test': [
            'coverage>=7.4.1',
            'pytest>=8.0.0',
            'pytest-asyncio>=0.23.5',
            'pytest-qt>=4.4.0',
            'pytest-cov>=4.1.0',
        ],
        'dev': [
            'black>=24.1.1',
            'mypy>=1.8.0',
            'pylint>=3.0.3',
        ],
    },
    python_requires='>=3.8',
)
