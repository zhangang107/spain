#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-04T11:12:49+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: setting.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-04T16:26:10+08:00
# @Copyright: Copyright by USTC

import os

# SPAIN项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 输出文件目录相对BASE_DIR路径
OUT_DIR = 'data/output'

# bindiff输出文件路径名称
BINDIFF = {
    'DIFF_DIR': os.path.join(BASE_DIR, OUT_DIR),
    'SQL_NAME': 'diff.db',
}

# IDAPython输出json文件路径名称
JSONFILE = {
    'JSON_DIR': os.path.join(BASE_DIR, OUT_DIR),
    'JSON_NAME_O': 'func_o.json',
    'JSON_NAME_P': 'func_p.json',
}

# 函数信息数据库路径名称
FUNCINFOSQL = {
    'FUNC_INFO_DIR': os.path.join(BASE_DIR, OUT_DIR),
    'FUNC_INFO_NAME': 'func_info.db',
}
