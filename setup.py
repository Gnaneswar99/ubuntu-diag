from setuptools import setup, find_packages

setup(
    name='ubuntu-diag',
    version='0.1.0',
    description='Ubuntu Infrastructure Diagnostics & Auto-Remediation CLI Tool',
    author='Gnaneswar M',
    author_email='gnaneswarm2024@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    package_data={'reports': ['templates/*.j2']},
    install_requires=[
        'click>=8.0',
        'rich>=13.0',
        'jinja2>=3.0',
        'psutil>=5.9',
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'ubuntu-diag=cli:cli',
        ],
    },
    python_requires='>=3.8',
)
