from setuptools import setup, find_packages

setup(name='pyvcard',
      version='1.0a.dev4',
      description='Powerful vCard parser',
      long_description=open("README.md").read(),
      long_description_content_type='text/markdown',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License',
      ],
      keywords='vcard vcf contact pyvcard rfc2426 rfc6350',
      url='http://github.com/frankdog-dev/pyvcard',
      author='brookit',
      python_requires='>=3.6',
      license="MIT",
      install_requires=['BeautifulSoup4'],
      packages=["pyvcard", "pyvcard.sources"],
      package_data={"": ["LICENSE", "README.md"], },
      include_package_data=True,
      zip_safe=False)
