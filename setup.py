import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='tumblr_tools',
    version='1.0.0',
    author='callMeIvan',
    author_email='ivan@callmeivan.com',
    description='A tool kit for bringing order to you Tumblr Account.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='',
    packages=['src'],
    install_requires=[
        "pytumblr"
    ],
)
