#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:04:06+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: session.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-03T11:25:18+08:00
# @Copyright: Copyright by USTC

from binfile import BinFile
from cfg import CFG

class Session(object):
    '''
    回话类，管理一次补丁分析工程
    主要属性：
        二进制文件路径
        BinDiff结果数据库路径
        函数信息数据库路径
        候选函数列表
        当前函数图对象
        函数质心列表
        函数基本块对应列表
        基本块序列语义分析列表
    主要方法：
        初始化
        BinDiff筛选
        CFG筛选
        处理当前函数图进行补丁基本块定位
        处理当前基本块序列进行语义分析
    '''
    def __init__(self, filenames, diff_name=None, funcinfo_path=None):
        '''
        在初始化中完成IDC以及BinDiff调用,生成BinDiff数据库
        '''
        self.filenames = filenames
        self.diff_name = diff_name
        self.funcinfo_path = funcinfo_path
        self.binfile = BinFile(self.filenames, diff_path=diff_name)
        self._idc_bindiff()
        self.cfg = None

    def _idc_bindiff(self):
        '''
        idc以及Bindiff调用，生成BinDiff数据库
        '''
        self.binfile.diff()

    def bin_filter(self, threshold=None):
        '''
        BinDiff筛选，获取初始候选函数
        '''
        self.binfile.diff_filter(threshold)

    def cfg_filter(self, arg=None):
        '''
        cfg筛选，获取候选函数
        '''
        

    def blocks_locate(self):
        '''
        补丁基本块定位
        '''

    def seman_analysis(self):
        '''
        语义分析
        '''
