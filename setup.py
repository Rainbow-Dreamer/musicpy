from setuptools import setup, find_packages
from os import path

setup(
    name='musicpy',
    packages=find_packages(),
    package_data={'musicpy': ['./*']},
    version='2.95',
    license='AGPLv3',
    description=
    'Musicpy is a music programming language in Python designed to write music in very handy syntax for musicians. 这是一门可以让你用编程写音乐的python邻域特定语言，可以让你用简洁的语法通过乐理知识写出优美的音乐。',
    author='Rainbow-Dreamer',
    author_email='1036889495@qq.com',
    url='https://github.com/Rainbow-Dreamer/musicpy.git',
    download_url=
    'https://github.com/Rainbow-Dreamer/musicpy/archive/2.95.tar.gz',
    keywords=[
        'music language', 'use codes to write music', 'music language for AI'
    ],
    install_requires=[
        'mido', 'midiutil', 'pygame', 'pillow', 'pyglet==1.5.11'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    include_package_data=True)
