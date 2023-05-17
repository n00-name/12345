#!/bin/bash

pycodestyle ide tests plugins main.py
RETCODE=$?
pycodestyle ide tests plugins main.py | wc -l
echo $RETCODE
exit $RETCODE
