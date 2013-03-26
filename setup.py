from distutils.core import setup

setup(
    name='resync',
    version='0.1',
    packages=['resync'],
    classifiers=["Development Status :: 3 - Alpha",
                 "Programming Language :: Python",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    author='Simeon Warner',
    author_email='simeon.warner@cornell.edu',
    long_description=open('README.md').read(),
    url='http://github.com/resync/resync',
)
