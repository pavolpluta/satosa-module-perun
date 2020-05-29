from setuptools import setup, find_packages

setup(
    name="satosa_perun",
    version="0.0.1",
    author="Pavel Vyskocil",
    author_email="Pavel.Vyskocil@cesnet.cz",
    description="perun package for SaToSa",
    long_description="perun package for SaToSa",
    long_description_content_type="text/markdown",
    url="https://github.com/CESNET/satosa-module-perun",
    packages=find_packages('src/'),
    package_dir={'': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "ldap3",
        "pycurl"
    ],
    python_requires='>=3.7',
)
