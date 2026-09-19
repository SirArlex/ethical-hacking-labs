from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='scyfix-tools',
    version='3.0',
    author='Chinedu Alex Chukwuma',
    author_email='alexchukwuma999@gmail.com',
    description='Scyfix Security Testing Toolkit — port scanner, multi-protocol brute forcer, directory scanner, and recon tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/SirArlex/ethical-hacking-labs',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
        'Topic :: Security',
    ],
    python_requires='>=3.7',
    install_requires=[
        'requests',
        'beautifulsoup4',
        'termcolor',
        'lxml',
        'paramiko',
    ],
    entry_points={
        'console_scripts': [
            'scyfix-brute=scyfix.bruteforcer:main',
            'scyfix-scan=scyfix.dirscanner:main',
            'scyfix-port=scyfix.portscanner:main',
            'scyfix-recon=scyfix.recontool:main',
        ],
    },
)
