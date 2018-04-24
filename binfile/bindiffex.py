#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T09:47:16+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: bindiffex.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-24T09:49:35+08:00
# @Copyright: Copyright by USTC

import commands
import sqlite3
import os
from spain import BASE_DIR, comlog

differ_dir = os.path.join(BASE_DIR,'spain')

class BinException(Exception):
    def __init__(self, msg):
        self.msg = msg

def _eval_name(filename):
        '''
        debug 出现新问题，二进制文件名带后缀的情况下，如'my_cgi07.cgi'，生成的BinExport文件为'my_cgi07.BinExport',即会去掉后缀名
        为解决上述问题添加 _eval_name函数，只取文件名前缀
        '''
        return filename.split('.')[0]

class BinDiffEx(object):
    '''
    管理BinDiffEx调用
    包括：
        BinDiff的前期准备即利用IDC脚本生成'.BinExport'文件
        通过'./differ'命令调用BinDiff生成格式数据库
        提供筛选查询方法隐藏数据库
    '''
    def __init__(self, filenames, diff_dir=None, sql_name=None):
        '''
        :param diff_name: BinDiff 所得数据库名
        :type path: string
        '''
        self.diff_dir = diff_dir
        self.sql_name = sql_name
        self.filenames = filenames
        self.exefilenames = []
        self._efilenames = {'origin':None, 'patch':None}
        self.func_sums = []
        self.cmp_func_sum = 0
        self.functions = []
        self.libfunctions = []
        self.basicblocks = []
        self.cmpedaddrs = None
        if self.diff_dir is None:
            self.diff_dir = './'
        if self.sql_name is None:
            self.sql_name = 'diff.db'
        if self._check_filenames():
            self._split_file()
        self.diff_name = os.path.join(self.diff_dir, self.sql_name)

    def _check_filenames(self):
        if len(self.filenames) == 2:
            return True
        else:
            return False

    def _check_files(self, filenames):
        '''
        检查文件是否存在
        '''
        exist = True
        if self._check_filenames():
            for filename in filenames:
                try:
                    f = open(filename)
                    f.close()
                except Exception as err:
                    exist = False
                    comlog.error('{} not exist, something wrong'.format(filename))
                    comlog.error('error info: {}'.format(err))
        else:
            exist = False
        return exist

    def _call_idc(self):
        '''
        调用IDC生成'.BinExport'文件（2个）
        '''
        if self._check_files(self.filenames):
            for filename in self.filenames:
                cmd = 'TVHEADLESS=1 idal -A -Sbindiff_export.idc {}'.format(filename)
                (status, output) = commands.getstatusoutput(cmd)
                if status != 0:
                    comlog.error("call idc error")
                    comlog.error('error info: {}'.format(output))
                    raise BinException('call idc wrong!')
        return True

    def _split_file(self):
        '''
        分解文件名
        '''
        _, exef1 = os.path.split(self.filenames[0])
        self._efilenames['origin'] = exef1
        _, exef2 = os.path.split(self.filenames[1])
        self._efilenames['patch'] = exef2

    def _call_diff(self):
        '''
        调用BinDiff生成结果数据库
        '''
        self._split_file()
        export_files = []
        export_files.append('/tmp/zynamics/BinExport/{}.BinExport'.format(_eval_name(self._efilenames['origin'])))
        export_files.append('/tmp/zynamics/BinExport/{}.BinExport'.format(_eval_name(self._efilenames['patch'])))
        if self._check_files(export_files):
            cmd = '{0}/differ --primary={1} --secondary={2} --output_dir={3}'.format(
                        differ_dir, export_files[0], export_files[1], self.diff_dir)
            comlog.info(cmd)
            (status, output) = commands.getstatusoutput(cmd)
            if status != 0:
                comlog.error('differ error')
                comlog.error('error info: {}'.format(output))
                raise BinException('differ wrong!')
            rename_cmd = 'mv {0}/*.BinDiff {0}/{1}'.format(self.diff_dir, self.sql_name)
            comlog.info(rename_cmd)
            (status, output) = commands.getstatusoutput(rename_cmd)
            if status != 0:
                comlog.error('rename sql error')
                comlog.error('error info: {}'.format(output))
                raise BinException('rename sql wrong!')
        self._getattrs()
        return True

    def _getattrs(self):
        '''
        内部函数，连接数据库，获取基本属性
        '''
        conn = sqlite3.connect(self.diff_name)
        cur = conn.cursor()
        '''
        获取 名称，函数， 基本快信息
        '''
        rows = cur.execute('SELECT filename, exefilename, functions, libfunctions, basicblocks FROM file')
        for row in rows:
            self.filenames.append(str(row[0]))
            self.exefilenames.append(str(row[1]))
            self.functions.append(int(row[2]))
            self.libfunctions.append(int(row[3]))
            self.basicblocks.append(int(row[4]))
        '''
        获取 可比较函数总数
        '''
        rs = cur.execute('SELECT count(*) FROM function').fetchone()
        self.cmp_func_sum = int(rs[0])
        cur.close()
        conn.close()

    def setfilenames(self, *args):
        '''
        设置二进制文件名（含路径）
        @param *args 文件名列表
        @type *args list 长度应为2
        '''
        if (len(args) == 2):
            for filename in args:
                self.filenames.append(filename)
            self._split_file()
        else:
            raise BinException('setfilenames erro')

    def differ(self, *args):
        '''
        主功能1，完成IDC调用,'./differ'调用
        @param args 可选参数 二进制文件名
        @type args list 长度为2
        '''
        if len(args) == 0:
            # 不带文件名调用
            if self._call_idc():
                return self._call_diff()
        elif len(args) == 2:
            # 带文件名调用
            self.setfilenames(*args)
            if self._call_idc():
                return self._call_diff()
        else:
            # 传参错误
            raise BinException('differ args error')

    def getcmped(self, threshold):
        '''
        与阈值比较， 获取初始候选函数地址对
        '''
        conn = sqlite3.connect(self.diff_name)
        cur = conn.cursor()
        rows = cur.execute('SELECT address1, address2 FROM function WHERE similarity < {0}'.format(threshold))
        cmpedaddrs = [(row[0], row[1]) for row in rows]
        return cmpedaddrs
