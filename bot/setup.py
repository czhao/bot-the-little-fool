from setuptools import setup

setup(
    name='bot',
    packages=['app'],
    include_package_data=True,
    install_requires=[
        'flask', 'requests', 'hashlib', 'hmac', 'raven'
    ],
)
