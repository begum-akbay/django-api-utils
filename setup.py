from setuptools import setup, find_packages

setup(
    name="django-api-utils",
    version="1.0.0",
    description="A Django library for common API utilities.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Begüm Akbay",
    author_email="begum@mosaic.ie",
    url="https://github.com/mosaic/django-api-utils",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=5.1",
        "djangorestframework>=3.15"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
    ],
)