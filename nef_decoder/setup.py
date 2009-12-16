from distutils.core import setup, Extension



module = Extension('binutils', sources = ['binutils.c'])

setup (name = 'binutils',
       version = '1.0',
       description = 'Utilities for dealing with binary data.',
       ext_modules = [module])