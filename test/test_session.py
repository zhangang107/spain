#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-09T16:11:36+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_session.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-19T17:00:58+08:00
# @Copyright: Copyright by USTC

import sys
import os
sys.path.append("..")
from setting import BASE_DIR
from session import Session

# file_o = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-f')
# file_p = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-g')
file_o = os.path.join(BASE_DIR, 'data/binfile/my_cgi07.cgi')
file_p = os.path.join(BASE_DIR, 'data/binfile/my_cgi08.cgi')
filenames = [file_o, file_p]

session = Session(filenames)
session.init_func()
session.analysis()
