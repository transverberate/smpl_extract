from setuptools import Extension
from setuptools import find_packages
from setuptools import setup


version = "0.2.0"
# cython accelerated filters
extensions = [
    Extension(
        "smpl_extract.filters.fir", 
        ["smpl_extract/filters/fir.pyx"],
    ),
    Extension(
        "smpl_extract.filters.iir",
        ["smpl_extract/filters/iir.pyx"],
    )
]


setup(
    name="smpl_extract",
    packages=find_packages("."),
    version=version,
    description="A python library/tool for extracting patches and samples from various sampler/audio disc image formats.",
    author="Counselor Chip",
    install_requires=[
        "future", 
        "numpy",
        "construct"
    ],
    setup_requires=[
        "setuptools>=18.0",
        "cython",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    ext_modules=extensions
)

