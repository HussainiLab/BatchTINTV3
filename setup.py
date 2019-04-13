import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

pkgs = setuptools.find_packages()
print('found these packages:', pkgs)

pkg_name = "BatchTINTV3"

setuptools.setup(
    name=pkg_name,
    version="3.0.11",
    author="Geoffrey Barrett",
    author_email="geoffrey.m.barrett@gmail.com",
    description="BatchTINTV3 - GUI created to more efficiently sort Axona/Tint data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HussainiLab/BatchTINTV3.git",
    packages=pkgs,
    install_requires=
    [
        'PyQt5',
        # 'PyQt5_sip'
        'pillow',
    ],
    package_data={'BatchTINTV3': ['img/*.png']},
    classifiers=[
        "Programming Language :: Python :: 3.7 ",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3) ",
        "Operating System :: OS Independent",
    ],
)
