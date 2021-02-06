from setuptools import setup
from os import path
setup(
    name='musicpy',
    packages=['musicpy'],
    package_data={
        'musicpy': ['./*'],
    },
    version='1.74',
    license='bsd-2-clause',
    description=
    'Musicpy is a python domain-specific language designed to write music in very handy syntax for musicians. 这是一个可以让你用编程写音乐的python领域特定语言，可以让你用简洁的语法通过乐理知识写出优美的音乐。',
    author='Rainbow-Dreamer',
    author_email='1036889495@qq.com',
    url='https://github.com/Rainbow-Dreamer/musicpy.git',
    download_url=
    'https://github.com/Rainbow-Dreamer/musicpy/archive/1.74.tar.gz',
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
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    include_package_data=True)
