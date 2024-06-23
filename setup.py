from setuptools import setup, find_packages

from pyvcard import __author__, __license__

setup(name='pyvcard',
      version='1.0b0',
      description='Powerful vCard (.vcf files) parser',
      long_description=open("README.md").read(),
      long_description_content_type='text/markdown',
      classifiers=[
        "Topic :: Text Processing",
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
      ],
      keywords='vcard vcf contact pyvcard rfc2426 rfc6350',
      url='http://github.com/brookite/pyvcard',
      author=__author__,
      python_requires='>=3.6',
      license=__license__,
      install_requires=['BeautifulSoup4'],
      include_package_data=True,
      zip_safe=False)
