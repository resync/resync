from setuptools import setup
# setuptools used instead of distutils.core so that 
# dependencies can be handled automatically

# Extract version number from resync/_version.py. Here we 
# are very strict about the format of the version string 
# as an extra sanity check. (Thanks for comments in 
# http://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package )
import re
VERSIONFILE="resync/_version.py"
verfilestr = open(VERSIONFILE, "rt").read()
match = re.search(r"^__version__ = '(\d\.\d.\d+(\.\d+)?)'", verfilestr, re.MULTILINE)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE))

setup(
    name='resync',
    version=version,
    packages=['resync'],
    scripts=['bin/resync','bin/resync-explorer'],
    classifiers=["Development Status :: 3 - Alpha",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: Apache Software License",
                 "Operating System :: OS Independent", #is this true? know Linux & OS X ok
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 2.6",
                 "Programming Language :: Python :: 2.7",
                 "Topic :: Internet :: WWW/HTTP",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    author='Simeon Warner',
    author_email='simeon.warner@cornell.edu',
    description='ResourceSync library and client',
    long_description=open('README').read(),
    url='http://github.com/resync/resync',
    install_requires=[
        "requests",
        "python-dateutil>=1.5",
        "defusedxml>=0.4.1"
    ],
    test_suite="tests",
)
