from setuptools import setup
from os import path
setup(
  name = 'musicpy', 
  packages = ['musicpy'],
  package_data = {'musicpy': ['./*'],},
  version = '1.63',  
  license='bsd-2-clause',    
  description = 'A music programming language to write music in syntax based on music theory, and make a piece of music simple in short sentences', 
  author = 'Rainbow-Dreamer',
  author_email = '1036889495@qq.com', 
  url = 'https://github.com/Rainbow-Dreamer/musicpy.git',
  download_url = 'https://github.com/Rainbow-Dreamer/musicpy/archive/1.63.tar.gz',
  keywords = ['music language', 'use codes to write music', 'music language for AI'],
  install_requires=[  
          'mido',
          'midiutil',
          'pygame',
          'pillow'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',  
    'Intended Audience :: Developers', 
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
  long_description=open('README.md',encoding='utf-8').read(),
  long_description_content_type='text/markdown',
  include_package_data=True
)