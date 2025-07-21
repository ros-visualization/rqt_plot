from setuptools import setup

package_name = 'rqt_plot'

setup(
    name=package_name,
    version='1.4.4',
    packages=[package_name, package_name + '/data_plot'],
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name + '/resource',
            ['resource/plot.ui']),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['plugin.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    author='Dorian Scholz',
    maintainer='Brandon Ong',
    maintainer_email='brandon@openrobotics.org',
    keywords=['ROS'],
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    description=(
        'rqt_plot provides a GUI plugin visualizing numeric values in a 2D plot ' +
        'using different plotting backends.'
    ),
    license='BSD',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'rqt_plot = ' + package_name + '.main:main',
        ],
    },
)
