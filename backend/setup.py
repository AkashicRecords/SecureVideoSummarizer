from setuptools import setup, find_namespace_packages

setup(
    name="secure-video-summarizer",
    version="0.1.0",
    packages=find_namespace_packages(include=['app*', 'tests*']),
    install_requires=[
        'Flask>=2.0.1',
        'transformers>=4.18.0',
        'torch>=2.0.0',
        'numpy>=1.21.0',
        'SpeechRecognition>=3.8.1',
        'pydub>=0.25.1',
        'python-dotenv>=0.19.0',
        'flask-session>=0.4.0',
        'flask-limiter>=2.4.0',
        'requests>=2.25.0'
    ],
    python_requires='>=3.8',
)
