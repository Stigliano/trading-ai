from setuptools import setup

setup(
    name='train_model',
    version='1.0',
    install_requires=[
        'xgboost',
        'pandas',
        'joblib'
    ],
    py_modules=['train_model'],
    entry_points={
        'console_scripts': [
            'train_model = train_model:train_and_save_model',
        ],
    },
)
