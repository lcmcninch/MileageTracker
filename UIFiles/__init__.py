from glob import glob
from subprocess import call
import os

from PyQt4.uic import compileUi


def ui():
    for uifile in glob(os.path.join('UIFiles', "*.ui")):
        pyfile = uifile[:-3] + "_Ui.py"
        if outdated(pyfile, uifile):
            call('pyuic4 {} > {}'.format(uifile, pyfile), shell=True)


def resource():
    for resfile in glob(os.path.join('UIFiles', "*.qrc")):
        pyfile = resfile[:-4] + "_rc.py"
        if outdated(pyfile, resfile):
            call("pyrcc4 -py3 -o {} {}".format(pyfile, resfile), shell=True)


def outdated(target, dependencies):
    if not os.path.exists(target):
        return True
    mtime = os.stat(target).st_mtime
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    return any(os.stat(f).st_mtime > mtime for f in dependencies)

ui()
resource()
