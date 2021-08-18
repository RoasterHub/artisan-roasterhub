#!/usr/bin/env python
"""
Start the application.
"""

import platform
import json
from pathlib import Path

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import sys
#import imp # deprecated favour of importlib
import os
from platform import system

# roasterhub init
if platform.system() == "Linux":
    home = os.environ['HOME']
elif platform.system() == "Windows":
    home = os.environ['HOMEPATH']

Path(home + '/.rhub').mkdir(parents=True, exist_ok=True)
usercrpath = home + '/.rhub/usercr.json'

if not os.path.exists(usercrpath):
    data = {
        'user': 'email',
        'password': 'key',
        'data': 'machine id',
    }
    json_data = json.dumps(data)
    f = open(usercrpath, "w")
    f.write(json_data)
    f.close()
# end roasterhub init


# highDPI support must be set before creating the Application instance
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
#    os.environ["QT_SCALE_FACTOR"] = "1"
except:
    pass

try:
    # PyQt new exit scheme (default from 5.14 on)
    from PyQt5.QtCore import pyqt5_enable_new_onexit_scheme  # @UnresolvedImport
    pyqt5_enable_new_onexit_scheme(True)
except:
    pass
        
# on Qt5, the platform plugin cocoa/windows is not found in the plugin directory (dispite the qt.conf file) if we do not
# extend the libraryPath accordingly
if system() == 'Darwin':
    try:
        if str(sys.frozen) == "macosx_app":
            from PyQt5.QtWidgets import QApplication # @Reimport
            QApplication.addLibraryPath(os.path.dirname(os.path.abspath(__file__)) + "/qt_plugins/")
    except Exception:
        pass
elif system().startswith("Windows"):
    try:
        ib = (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
#            or imp.is_frozen("__main__")) # tools/freeze
             or getattr(sys, 'frozen', False)) # tools/freeze           
        from PyQt5.QtWidgets import QApplication # @Reimport 
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "plugins"))            
        else:
            import site # @Reimport @UnusedImport
            #gives error in python 3.4: could not find or load the Qt platform plugin "windows"
            QApplication.addLibraryPath(site.getsitepackages()[1] + "\\PyQt5\\plugins")

    except Exception:
        pass
else: # Linux
    try:
        ib = getattr(sys, 'frozen', False)
        from PyQt5.QtWidgets import QApplication # @Reimport
        if ib:
            QApplication.addLibraryPath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources/qt_plugins"))            
        else:
            import site # @Reimport
            QApplication.addLibraryPath(os.path.dirname(site.getsitepackages()[0]) + "/PyQt5/qt_plugins")
    except Exception:
        pass
        
    

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    from artisanlib import main    

    if system() == "Windows" and (hasattr(sys, "frozen") # new py2exe
                                or hasattr(sys, "importers") # old py2exe
    #                            or imp.is_frozen("__main__")): # tools/freeze
                                or getattr(sys, 'frozen', False)): # tools/freeze
        from multiprocessing import set_executable
        executable = os.path.join(os.path.dirname(sys.executable), 'artisan.exe')
        set_executable(executable)    
        del executable
            
    if os.environ.get('TRAVIS'):
        # Hack to exit inside Travis CI
        # Ideally we would use pytest-qt.
        import threading
        t = threading.Timer(30, lambda: os._exit(0))
        t.start()
    main.main()


# EOF
