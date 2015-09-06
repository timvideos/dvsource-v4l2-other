#!/usr/bin/env python

from distutils.core import setup
from build_manpage import build_manpage

setup(name='dvsource-v4l2-other',
      version='0.1.0',
      description='Video4Linux2 source which supports any input format for DVswitch',
      author="Tim 'mithro' Ansell",
      author_email='mithro@mithis.com',
      url='https://github.com/timvideos/dvsource-v4l2-other/',
      py_modules=['dvsource-v4l2-other'],
      cmdclass={'build_manpage': build_manpage},
      )
