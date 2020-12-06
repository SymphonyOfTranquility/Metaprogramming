from setuptools import setup, find_packages

classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
]

setup(
    name="symphony_of_tranquility_php_formatter",
    version="0.0.1",
    author="SymphonyOfTranquility",
    author_email="symphony.of.tranquility@gmail.com",
    description="Php verifier and formatter",
    long_description="Php verifier and formatter of your projects, files and directories",
    url="",
    packages=find_packages(),
    entry_points={
        "console_scripts": ['PhpCCF=php_formatter.main:main']
        },
    python_requires='>=3.6',
)