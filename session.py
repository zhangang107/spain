#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:04:06+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: session.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-03T16:01:42+08:00
# @Copyright: Copyright by USTC

from binfile import BinFile
from cfg import CFG
from block import Trace

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
        self.cfg = {'origin':None, 'patch':None}
        self.cur_func = {'origin':None, 'patch':None}
        self.cur_blocks = {}
        self.func_cfg_centroid = {}
        self.func_generator = self.binfile.next_func_graphs()
        self.candidate_func = []

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
        if arg is None:
            # 默认获取下一对候选函数
            self.cur_func['origin'], self.cur_func['patch'] = self.func_generator.next()
        elif isinstance(arg, int) or isinstance(arg, str):
            # 按地址或函数名获取指定候选函数
            self.cur_func['origin'], self.cur_func['patch'] = self.binfile.get_func_graphs(arg)
        self.cfg['origin'] = CFG(self.cur_func['origin'])
        self.cfg['patch'] = CFG(self.cur_func['patch'])
        funcname = self.cfg['origin'].funcname
        self.func_cfg_centroid[funcname] = {
                'origin': self.cfg['origin'].get_centroid(),
                'patch': self.cfg['patch'].get_centroid()}
        if self.cfg['origin'].same_with(self.cfg['patch']):
            self.candidate_func[funcname] = {
                'origin': self.cfg['origin'].address,
                'patch': self.cfg['patch'].address}

    def blocks_locate(self, arg=None):
        '''
        补丁基本块定位
        '''
        self.cur_blocks['funcname'] = self.cfg['origin'].funcname
        self.cur_blocks['address_o'] = self.cfg['origin'].address
        self.cur_blocks['address_p'] = self.cfg['patch'].address
        traces = Trace(self.cfg['origin'].func_graph, self.cfg['patch'].func_graph)
        self.cur_blocks['traces'] = traces.get_trace()

    def seman_analysis(self):
        '''
        语义分析
        '''
        pass
