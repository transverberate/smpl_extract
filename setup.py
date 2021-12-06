from setuptools import setup


version = "0.1.0"


setup(
    name="smpl_extract",
    packages=["smpl_extract"],
    version=version,
    description="A python library/tool for extracting programs and samples from AKAI S3000 images.",
    author="Counselor Chip",
    install_requires=["future", "numpy"],
    setup_requires=[
        "numpy"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)

