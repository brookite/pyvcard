from setuptools import setup, find_packages

setup(name='pyvcard',
      version='1.0a.dev2',
      description='Powerful vCard parser',
      long_description=open("README.rst").read(),
      long_description_content_type='text/markdown',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
      ],
      keywords='vcard vcf contact pyvcard rfc2426 rfc6350',
      url='http://github.com/frankdog-dev/pyvcard',
      author='frankdog-dev',
      packages=find_packages(),
      python_requires='>=3.6',
      install_requires=['BeautifulSoup4'],
      include_package_data=True,
      zip_safe=False)
