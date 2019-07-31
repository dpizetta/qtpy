# -*- coding: utf-8 -*-
#
# Copyright © 2009- The Spyder Development Team
# Copyright © 2014-2015 Colin Duquesnoy
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
**QtPy** is a shim over the various Python Qt bindings. It is used to
write Qt binding independent libraries or applications.

If one of the APIs has already been imported, then it will be used.
Otherwise, the shim will automatically select the first available API
following the list below; in that case, you can force the use of one
specific binding (e.g. if your application is using one specific binding
and you need to use a library that uses QtPy) by setting up the
``QT_API`` environment variable.

For each selected binding, there will be more three attempts if it is
not found, following the most recent (Qt5) and most stable (PyQt) API.
See below:

* pyqt5: PyQt5, PySide2, PyQt4, PySide
* pyside2: PySide2, PyQt5, PyQt4, PySide
* pyqt4: PyQt4, PySide, PyQt5, PySide2
* pyside: PySide, PyQt4, PyQt5, PySide2

The clearest way to set which API is to be used by QtPy is setting
``QT_API`` environment variable. The default value for ``QT_API = 'pyqt5'``
(not case sensitive).

The priority when setting the Qt binding API is detailed below:

1 Have been already imported any Qt binding (not recommended, implicit):
    1.1 Just one binding is found imported;
        1.1.1 QT_API is not set, pass, no output;
        1.1.2 QT_API is set to the same binding, pass, no output;
        1.1.3 QT_API is set to a different binding, ignore QT_API, pass but warns;
    2.1 More than one binding is found imported;

2 Have NOT been already imported any Qt binding (explicitly setting):
    2.1 QT_API is set correctly, pass;
        2.1.1 If binding is found, pass, no output;
        2.1.2 If binding is not found, try another one (three more);
            2.1.2.a If any is found (different from set), pass but warns;
            2.1.2.b If no one is found, stop, error;
    2.2 QT_API is not set correctly, stop, error;
    2.3 QT_API is not set, use default, continue to 2.1.1, without 2.1.2.a;

Note 1: If any Qt binding is imported (a different one) after QtPy
import, issues and errors may occur and QtPy won't be able to help you
with any warning.

Note 2: We always preffer to not break the code when something is not
found, so we use ``warnings`` module to alert changes and show information
that may be useful when developing using QtPy. Remember to set warnings
to show messages.

PyQt5
=====

For PyQt5, you don't have to set anything as it will be used automatically::

    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide2
=======

Set the QT_API environment variable to 'PySide2' before importing other
packages::

    >>> import os
    >>> os.environ['QT_API'] = 'pyside2'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PyQt4
=====

Set the ``QT_API`` environment variable to 'PyQt4' before importing any python
package::

    >>> import os
    >>> os.environ['QT_API'] = 'pyqt4'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide
======

Set the QT_API environment variable to 'PySide' before importing other
packages::

    >>> import os
    >>> os.environ['QT_API'] = 'pyside'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

"""

import os
import pkgutil
import platform
import sys
import warnings
from distutils.version import LooseVersion

# Version of QtPy
from ._version import __version__


class PythonQtError(RuntimeError):
    """Error raise if no bindings could be selected."""
    pass


class PythonQtWarning(Warning):
    """Warning if some features are not implemented in a binding."""
    pass


def get_imported_bindings(import_list):
    """Return an ordered list of Qt bindings that have been already imported.

    ``import_list`` is a list of importing names, case sensitive.

    Return the same list excluding binding names not imported.
    """

    imported_api = []

    for api_name in import_list:
        if api_name in sys.modules:
            imported_api.append(api_name)

    return imported_api


def get_available_bindings(import_list):
    """Return an ordered list of Qt bindings that are available (installed).

    ``import_list`` is a list of importing names, case sensitive.

    Return the same list excluding binding names not available.
    """

    available_bindings = []

    for api_name in import_list:
        # Using 'try...import' or __import__ to TEST causes the
        # api_name to be imported and accumulating on sys.modules
        # Using pkgutil.get_loader(), that works on both py2 and py3
        # it works as expected without the need of restore sys.path
        can_import = pkgutil.get_loader(api_name)

        if can_import:
            available_bindings.append(api_name)

    return available_bindings


def get_api_information(api_name):
    """Get API information of version and Qt version.

    ``api_name`` is an importing name, case sensitive.

    Note: this function is not prepared to be called more than once, yet.
    Multiple calls will accumulate imports on sys.modules if api_name is
    installed. It must be rewrite to use pkgutil/importlib to check
    check version numbers.
    """

    if api_name == 'PyQt4':
        try:
            import sip
            try:
                sip.setapi('QString', 2)
                sip.setapi('QVariant', 2)
                sip.setapi('QDate', 2)
                sip.setapi('QDateTime', 2)
                sip.setapi('QTextStream', 2)
                sip.setapi('QTime', 2)
                sip.setapi('QUrl', 2)
            except (AttributeError, ValueError):
                # PyQt < v4.6
                pass
            from PyQt4.Qt import PYQT_VERSION_STR as api_version  # analysis:ignore
            from PyQt4.Qt import QT_VERSION_STR as qt_version  # analysis:ignore
        except ImportError:
            raise PythonQtError('PyQt4 cannot be imported in QtPy.')

    elif api_name == 'PyQt5':
        try:
            from PyQt5.QtCore import PYQT_VERSION_STR as api_version  # analysis:ignore
            from PyQt5.QtCore import QT_VERSION_STR as qt_version  # analysis:ignore
        except ImportError:
            raise PythonQtError('PyQt5 cannot be imported in QtPy.')

        if sys.platform == 'darwin':

            macos_version = LooseVersion(platform.mac_ver()[0])

            if macos_version < LooseVersion('10.10'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.9'):
                    raise PythonQtError("Qt 5.9 or higher only works in "
                                        "macOS 10.10 or higher. Your "
                                        "program will fail in this "
                                        "system.")
            elif macos_version < LooseVersion('10.11'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")
            del macos_version

    elif api_name == 'PySide':
        try:
            from PySide import __version__ as api_version  # analysis:ignore
            from PySide.QtCore import __version__ as qt_version  # analysis:ignore
        except ImportError:
            raise PythonQtError('PySide cannot be imported in QtPy.')

    elif api_name == 'PySide2':
        try:
            from PySide2 import __version__ as api_version  # analysis:ignore
            from PySide2.QtCore import __version__ as qt_version  # analysis:ignore
        except ImportError:
            raise PythonQtError('PySide2 cannot be imported in QtPy.')

        if sys.platform == 'darwin':

            macos_version = LooseVersion(platform.mac_ver()[0])

            if macos_version < LooseVersion('10.11'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version

    else:
        return (None, None)

    return (api_version, qt_version)


# Qt API environment variable name
QT_API = 'QT_API'

# Default/Preferrable API, must be one of api_names keys
default_api = 'pyqt5'

# All false/none/empty because they were not imported yet
PYQT5 = PYQT4 = PYSIDE = PYSIDE2 = False
API = API_NAME = API_VERSION = QT_VERSION = ''
PYQT_VERSION = PYSIDE_VERSION = ''
is_old_pyqt = is_pyqt46 = False

# Keys: names of the expected Qt API (internal names)
# Values: ordered list of importing names based on its key
# The sequence preserves the most recent (Qt5) and stable (PyQt) api
api_names = {'pyqt4': ['PyQt4', 'PySide', 'PyQt5', 'PySide2'],
             'pyqt5': ['PyQt5', 'PySide2', 'PyQt4', 'PySide'],
             'pyside': ['PySide', 'PyQt4', 'PyQt5', 'PySide2'],
             'pyside2': ['PySide2', 'PyQt5', 'PyQt4', 'PySide']}

# Other keys for the same Qt API that can be used, for compatibility
# pyqt4 -> pyqode.qt original name, pyqt -> name used in IPython.qt
api_names['pyqt'] = api_names['pyqt4']

# Detecting if a binding was specified by the user
binding_specified = QT_API in os.environ

# Setting a default value for QT_API
os.environ.setdefault(QT_API, default_api)

# Get the value from environment (or default if not set)
env_api = os.environ[QT_API].lower()

# Check if it was correctly set with environment variable
if env_api not in api_names.keys():
    msg = 'Qt binding "{}" is unknown. Use one from these: {}.'
    msg = msg.format(env_api, api_names[default_api])
    raise PythonQtError(msg)

# The preference sequence is given by env_api
environment_api_list = api_names[env_api]

# Check if Qt bindings have been already imported in 'sys.modules'
imported_api_list = get_imported_bindings(api_names[env_api])

# If more than one Qt binding is imported, just warns for now
if len(imported_api_list) >= 2:
    msg = 'There is more than one imported Qt binding: {}. '
    msg += 'This may cause some issues. Check your code for consistence.'
    msg = msg.format(imported_api_list)
    warnings.warn(msg, RuntimeWarning)

# Importing order for bindings if they are not found
api_trial = imported_api_list if imported_api_list else environment_api_list

# Refined import order with installed ones
api_trial_avaliable = get_available_bindings(api_trial)

# Check bindings available, maybe overtested
if not api_trial_avaliable:
    msg = 'No Qt binding can be imported. Install at least one of these: {}.'
    msg = msg.format(api_names[default_api])
    raise PythonQtError(msg)

# Initial value for API is get always from environment first trial, index 0
initial_api = environment_api_list[0]

# In most cases, it will execute only the first item as expected
# because we already refined the list of installed bindings
# Only if any importing problem occurs it will try other ones
for api_name in api_trial_avaliable:
    try:
        API_VERSION, QT_VERSION = get_api_information(api_name)
    except PythonQtError as er:
        msg = 'The binding "{}" is installed but cannot be used. '
        msg += 'Check the original error message: {}.'
        msg = msg.format(api_name, str(er))
        warnings.warn(msg, RuntimeWarning)
    else:
        if API_VERSION and QT_VERSION:
            API = api_name.lower()
            API_NAME = api_name
            if api_name == 'PyQt4':
                PYQT4 = True
                PYQT4_VERSION = API_VERSION
                versions = ('4.4', '4.5', '4.6', '4.7')
                is_old_pyqt = PYQT4_VERSION.startswith(versions)
                is_pyqt46 = PYQT4_VERSION.startswith('4.6')
                import sip
                try:
                    API_NAME += (" (API v{0})".format(sip.getapi('QString')))
                except AttributeError:
                    pass
            elif api_name == 'PyQt5':
                PYQT5 = True
                PYQT4_VERSION = API_VERSION
            elif api_name == 'PySide':
                PYSIDE = True
                PYSIDE_VERSION = API_VERSION
            elif api_name == 'PySide2':
                PYSIDE2 = True
                PYSIDE_VERSION = API_VERSION
            break

# Set the environment variable to the current used API
os.environ['QT_API'] = API

if API_NAME != initial_api and binding_specified:
    # If the code is using QtPy is not supposed do directly import Qt api's,
    # so a warning is sent to check consistence
    if imported_api_list:
        msg = 'Selected binding "{}" could not be set because "{}" has '
        msg += 'already been imported. Check your code for consistence.'
        msg = msg.format(initial_api, API_NAME)
        warnings.warn(msg, RuntimeWarning)
    # If a correct API name is passed to QT_API and it cannot be found,
    # switches to another and informs through the warning
    else:
        msg = 'Selected binding "{}" could not be found, using "{}".'
        msg = msg.format(initial_api, API_NAME)
        warnings.warn(msg, RuntimeWarning)


# When `FORCE_QT_API` is set, we disregard
# any previously imported python bindings.
if os.environ.get('FORCE_QT_API') is not None:
    if 'PyQt5' in sys.modules:
        API = initial_api if initial_api in PYQT5_API else 'pyqt5'
    elif 'PySide2' in sys.modules:
        API = initial_api if initial_api in PYSIDE2_API else 'pyside2'
    elif 'PyQt4' in sys.modules:
        API = initial_api if initial_api in PYQT4_API else 'pyqt4'
    elif 'PySide' in sys.modules:
        API = initial_api if initial_api in PYSIDE_API else 'pyside'
