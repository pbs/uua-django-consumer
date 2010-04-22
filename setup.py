from setuptools import setup, find_packages

setup(
    name='pbs_uua_consumer',
    version='0.1',
    description='',
    author='',
    author_email='',
    packages = find_packages('src'),
    package_dir={'':'src'},
    include_package_data=True,
    package_data = {
        '': ['templates/*.html', 'templates/*/*.html']
    },
)
