from setuptools import setup

APP = ['autoclicker.py']  # Your main Python script
DATA_FILES = [
    'logoauto-removebg.png',
    'moon.png',
    'sun (1).png'
]
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'PIL',           # for Pillow
        'pyautogui', 
        'keyboard', 
        'pynput', 
        'pystray',
        'tkinter',       # tkinter might need explicit inclusion
    ],
    'excludes': ['winreg', 'nt', '_winapi', '_frozen_importlib_external'],  # Exclude Windows-specific modules
    'verbose': True
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
