# vim : fileencoding=UTF-8 :
import io
import os.path

from setuptools import setup


readme_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'README.md')


setup(
    name='multiprocessing-logging',
    version='0.3.0',
    description='Logger for multiprocessing applications',
    long_description_content_type="text/markdown",
    long_description=io.open(readme_file, 'rt', encoding='utf-8').read(),
    url='https://github.com/jruere/multiprocessing-logging',
    license="LGPLv3",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords="multiprocessing logging logger handler",
    author="Javier Ruere",
    author_email="javier@ruere.com.ar",
    zip_safe=False,
    packages=['tests'],
    py_modules=['multiprocessing_logging'],
    platforms=["POSIX"],
    test_suite="tests",
    tests_require=["mock~=2.0.0 ; python_version < '3.3'"],
)
