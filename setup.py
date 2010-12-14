from setuptools import setup, find_packages

setup(
    name='pbs_uua_consumer',
    version='1.0',
    description='',
    author='PBS',
    author_email='no-reply@pbs.org',
    packages = find_packages('src'),
    package_dir={'':'src'},
)
