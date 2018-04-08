#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-02T16:02:17+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: mylog.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-07T21:14:03+08:00
# @Copyright: Copyright by USTC

import logging
from logging import Logger, FileHandler, Formatter, StreamHandler
import os
import time
import sys
sys.path.append("..")
from setting import BASE_DIR

logdir = os.path.join(BASE_DIR, 'log')
date = time.strftime('%Y-%m-%d')
logdatedir = os.path.join(logdir, date)
os.mkdir(logdatedir) if not os.path.exists(logdatedir) else None


'''
日志模块
简单版本：
filehandler 和 console 分别输出到文件和终端
'''
class Mylog(Logger):
    def __init__(self, name, filename, console_on=False, level=logging.DEBUG):
        super(Mylog, self).__init__(name)
        self.filename = os.path.join(logdatedir, filename)
        self.filehandler = FileHandler(self.filename)
        self.console_on = console_on
        self.console = StreamHandler()
        self.level = level
        self._config()

    def _config(self):
        self.format = Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                "%Y-%m-%d %H:%M:%S")
        self.filehandler.setFormatter(self.format)
        self.addHandler(self.filehandler)
        self.setLevel(self.level)
        if self.console_on:
            self.console.setFormatter(self.format)
            self.console.setLevel(logging.INFO)
            self.addHandler(self.console)

    def add_console(self):
        self.console.setFormatter(self.format)
        self.console.setLevel(logging.INFO)
        self.addHandler(self.console)

comlog = Mylog(name='common log',filename="default.log", console_on=True)
if __name__ == '__main__':
    log = Mylog(name='test log',filename="testlog.log", console_on=True)
    log.debug('this is a debug msg')
    log.info('this is a info msg')
    log.warn('this is warn msg')
    log.error('this is a error msg')
    log.critical('this is a critical msg')
    ll = range(10)
    log.info('\n\n')
    log.info(ll)
