# vim : fileencoding=UTF-8 :
from setuptools import setup


setup(
    name='multiprocessing-logging',
    version='0.2.5',
    description='Logger for multiprocessing applications',
    url='https://github.com/jruere/multiprocessing-logging',
    license="LGPLv3",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: POSIX',
    ],
    keywords="multiprocessing logging logger handler",
    author="Javier Ruere",
    author_email="javier@ruere.com.ar",
    zip_safe=False,
    packages=['tests'],
    py_modules=['multiprocessing_logging'],
    platforms=["POSIX"],
    test_suite="tests",
)
