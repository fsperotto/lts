from setuptools import setup, find_packages, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = ['numpy>=1.10.4']

setup(
    #name="lts-pkg-fsperotto",
    name="lts",
    version="0.0.2",
    author="Filipo Studzinski Perotto",
    author_email="filipo.perotto.univ@gmail.com",
    description="A compilation of text tiling, text segmentation and text classification methods.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fsperotto/lts",
    license = 'MIT',
    #packages=find_packages(),
	#packages=['lts', 'lts.emb_seg_text'],
    #packages=find_packages(exclude=['data', 'notebooks']), 
    packages=find_namespace_packages(include=['lts','lts.uts','lts.readless','lts.nts'],exclude=['data', 'notebooks']),
    #include_package_data = True,
    #package_data={'corpus': ['corpus']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    #install_requires = requirements,
    #tests_require = [],    
)