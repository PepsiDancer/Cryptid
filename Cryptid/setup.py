import sys
from setuptools import setup, Extension
import pybind11

cpp_args = ['-std=c++17', '-O3', '-ffast-math']

if sys.platform == 'win32':
    cpp_args = ['/std:c++17', '/O2', '/fp:fast']

ext_modules = [
    Extension(
        "physics_core",
        ["physics_core.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=cpp_args,
    )
]

setup(
    name="physics_core",
    version="1.0.0",
    author="Physics Engine Dev",
    description="2D Soft Body physics backend using C++ and Pybind11",
    ext_modules=ext_modules,
)