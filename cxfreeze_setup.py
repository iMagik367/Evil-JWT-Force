import os
from cx_Freeze import setup, Executable

# Inclui arquivos de assets (por exemplo splash screen)
include_files = [(os.path.join('gui', 'assets', 'splash.png'), os.path.join('gui', 'assets', 'splash.png'))]

build_exe_options = {
    'packages': ['core', 'utils', 'config', 'gui', 'scripts'],
    'include_files': include_files
}

setup(
    name = 'EvilJWTForce',
    version = '1.0',
    description = 'Evil JWT Force',
    options = {'build_exe': build_exe_options},
    executables = [Executable('main.py', base=None, target_name='EvilJWTForce.exe')]
) 