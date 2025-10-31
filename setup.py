from setuptools import setup, find_packages

setup(
    name="ph_coder_docstr",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ph_coder_docstr=ph_coder_docstr.__main__:main",
        ],
    },
    author="PH Coder",
    description="A tool to automatically add docstrings to code using AI",
    python_requires=">=3.8",
)

