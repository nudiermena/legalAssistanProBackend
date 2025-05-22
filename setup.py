from setuptools import setup, find_packages

setup(
    name="legal_assistant_pro",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "boto3",
        "requests",
        "python-docx",
        "markdown"
    ]
) 