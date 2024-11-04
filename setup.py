from setuptools import setup

APP = ['autoclicker.py']  # Your main Python script
DATA_FILES = [
    'logoauto-removebg.png',
    'moon.png',
    'sun (1).png'
]
OPTIONS = {
    'argv_emulation': True,
    'packages': [],  # Add any additional packages if required
    'iconfile': 'icon.icns',  # Optional: add a .icns file if you have an app icon for macOS
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
