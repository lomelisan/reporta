from setuptools import setup

setup(name='reporta',
	version='1.0',
	description="Central Routin Report Procesing App",
	author='lomelisan',
	author_email='lomelisan@gmail.com',
	url='http://www.python.org/sigs/distutils-sig/',
	install_requires=[
		'Flask==0.10.1',
		'Flask-SQLAlchemy==1.0',
		'Flask-Login==0.2.7',
		'Flask-WTF==0.9.2',
		'flask_mail',
		'alembic'
		'openpyxl']
		)
