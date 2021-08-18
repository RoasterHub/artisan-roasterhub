#!/usr/bin/env python3

# ABOUT
# Artisan Platform Dialog

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import platform

from artisanlib import __version__
from artisanlib import __revision__

from artisanlib.dialogs import ArtisanDialog

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QTextEdit

class platformDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(platformDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Artisan Platform", None))
        platformdic = {}
        platformdic["Architecture"] = str(platform.architecture())
        platformdic["Machine"] = str(platform.machine())
        platformdic["Platform name"] =  str(platform.platform())
        platformdic["Processor"] = str(platform.processor())
        platformdic["Python Build"] = str(platform.python_build())
        platformdic["Python Compiler"] = str(platform.python_compiler())
        platformdic["Python Branch"] = str(platform.python_branch())
        platformdic["Python Implementation"] = str(platform.python_implementation())
        platformdic["Python Revision"] = str(platform.python_revision())
        platformdic["Release"] = str(platform.release())
        platformdic["System"] = str(platform.system())
        platformdic["Version"] = str(platform.version())
        platformdic["Python version"] = str(platform.python_version())
        system = str(platform.system())
        if system == "Windows":
            platformdic["Win32"] = str(platform.win32_ver())
        elif system == "Darwin":
            platformdic["Mac"] = str(platform.mac_ver())
        elif system == "Linux":
            platformdic["Linux"] = str(platform.linux_distribution())
            platformdic["Libc"] = str(platform.libc_ver())
        htmlplatform = "<b>version =</b> " + __version__ + " (" + __revision__ + ")<br>"
        for key in sorted(platformdic):
            htmlplatform += "<b>" + key + " = </b> <i>" + platformdic[key] + "</i><br>"
        platformEdit = QTextEdit()
        platformEdit.setHtml(htmlplatform)
        platformEdit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(platformEdit)
        self.setLayout(layout)



