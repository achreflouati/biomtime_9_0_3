from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in biotime/__init__.py
from biotime import __version__ as version

setup(
	name="biotime",
	version=version,
	description="Integration with BioTime servers to fetch check-in list",
	author="ARD",
	author_email="Hadeel.milad@ard.ly",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
