from setuptools import setup, find_packages

setup(name='pyvcard',
      version='1.0a.dev1',
      description='Powerful vCard parser',
      long_description=open("README.rst").read(),
      long_description_content_type='text/markdown',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
      ],
      keywords='vcard vcf contact pyvcard',
      url='http://github.com/frankdog-dev/pyvcard',
      author='frankdog-dev',
      packages=find_packages(),
      py_modules=['pyiofile'],
      include_package_data=True,
      zip_safe=False)
