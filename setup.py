from setuptools import setup

setup(name='genwiki',
	version='0.1',
	packages=['genwiki'],
	data_files=[('',['__main__.py'])],
	include_package_data=True,
	package_data= {'': ['static/css/*.css', 'static/js/*.js', 'templates/*.html']}
	)
