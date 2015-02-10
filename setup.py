#!/usr/bin/env python

from distutils.core import setup
from build_manpage import build_manpage

setup(name='dvsource-v4l2-other',
      version='1.0',
      description='Video4Linux2 source which supports any input format for DVswitch',
      author='Ben Hutchings',
      author_email='ben@decadent.org.uk',
      url='https://github.com/timvideos/dvsource-v4l2-other/',
      py_modules=['dvsource-v4l2-other'],
      cmdclass={'build_manpage': build_manpage},
      )
