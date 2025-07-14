from setuptools import setup

setup(
    name='agandock-cli',
    version='0.1.0',
    packages=['agandock_cli', 'agandock_cli.scripts'],
    include_package_data=True,
    install_requires=[
        'pandas',
        'numpy',
        'rdkit',
        'openbabel-wheel',
        'torch',
        'psutil',
    ],
    entry_points={
        'console_scripts': [
            'agandock = agandock_cli.cli:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A CLI for Agandock operations',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/agandock-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)