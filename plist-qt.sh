#!/bin/sh
if [ $1 = 'pyside' ]; then
    export QT_API=pyside;
else
    export QT_API=pyqt;
fi;
export DJANGO_SETTINGS_MODULE=puente.settings
python listview.py
