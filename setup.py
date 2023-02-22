from setuptools import setup, find_packages

setup(
    name='musicpy',
    packages=find_packages(),
    package_data={'musicpy': ['./*']},
    version='6.35',
    license='LGPLv2.1',
    description=
    'Musicpy is a music programming language in Python designed to write music in very handy syntax through music theory and algorithms.',
    author='Rainbow-Dreamer',
    author_email='1036889495@qq.com',
    url='https://github.com/Rainbow-Dreamer/musicpy.git',
    download_url=
    'https://github.com/Rainbow-Dreamer/musicpy/archive/6.35.tar.gz',
    keywords=[
        'music language', 'use codes to write music', 'music language for AI'
    ],
    install_requires=['mido-fix', 'pygame', 'dataclasses'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    include_package_data=True)
