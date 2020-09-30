import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lts-pkg-fsperotto", # Replace with your own username
    version="0.0.1",
    author="Filipo Studzinski Perotto",
    author_email="filipo.perotto.univ@gmail.com",
    description="A compilation of text tiling, text segmentation and text classification methods.",
    long_description=long_description,
	#long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/fsperotto/lts",
    #packages=setuptools.find_packages(),
	packages=['lts', 'lts.emb_seg_text'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)