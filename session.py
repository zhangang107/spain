#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:04:06+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: session.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-18T15:58:54+08:00
# @Copyright: Copyright by USTC

from binfile import BinFile, FuncGraph
from cfg import CFG
from block import Trace
from seman import Semantic
from log.mylog import comlog

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
    def __init__(self, filenames, diff_dir=None, sql_name=None, json_dir=None,
                    json_names=None, funcinfo_dir=None, funcinfo_name=None):
        '''
        在初始化中完成IDC以及BinDiff调用,生成BinDiff数据库
        '''
        self.filenames = filenames
        self.diff_dir = diff_dir
        self.sql_name = sql_name
        self.json_dir = json_dir
        self.json_names = json_names
        self.funcinfo_dir = funcinfo_dir
        self.funcinfo_name = funcinfo_name
        self.binfile = BinFile(self.filenames, diff_dir=self.diff_dir, sql_name=self.sql_name,
                        json_dir=self.json_dir, json_names=self.json_names,
                        funcinfo_dir=self.funcinfo_dir, funcinfo_name=self.funcinfo_name)
        self.cfg = {'origin':None, 'patch':None}
        self.cur_func = {'origin':None, 'patch':None}
        self.cur_blocks = {}
        self.func_cfg_centroid = {}
        self.func_generator = self.binfile.next_func_graphs()
        self.candidate_func = {}
        self.cfg_iter_count = 0

    def _idc_bindiff(self):
        '''
        idc以及Bindiff调用，生成BinDiff数据库
        '''
        self.exefilenames = self.binfile.exefilenames
        self.binfile.diff()
        self.cmp_func_sum = self.binfile.cmp_func_sum

    def bin_filter(self, threshold=None):
        '''
        BinDiff筛选，获取初始候选函数
        @return 返回初始候选函数表长度
        '''
        return self.binfile.diff_filter(threshold)

    def cfg_filter(self, arg=None):
        '''
        cfg筛选，获取候选函数存入self.candidate_func中
        '''
        if arg is None:
            # 默认获取下一对候选函数
            self.cur_func['origin'], self.cur_func['patch'] = self.func_generator.next()
        elif isinstance(arg, int) or isinstance(arg, str):
            # 按地址或函数名获取指定候选函数
            self.cur_func['origin'], self.cur_func['patch'] = self.binfile.get_func_graphs(arg)
        elif isinstance(arg, list) and isinstance(arg[0], FuncGraph):
            # 直接传递候选函数
            self.cur_func['origin'], self.cur_func['patch'] = arg[0], arg[1]
        self.cfg['origin'] = CFG(self.cur_func['origin'])
        self.cfg['patch'] = CFG(self.cur_func['patch'])
        funcname = self.cfg['origin'].funcname
        self.func_cfg_centroid[funcname] = {
                'origin': self.cfg['origin'].get_centroid(),
                'patch': self.cfg['patch'].get_centroid()}
        if not self.cfg['origin'].same_with(self.cfg['patch']):
            self.candidate_func[funcname] = {
                'origin': self.cfg['origin'].address,
                'patch': self.cfg['patch'].address}
        # comlog.info('candidate_func {}'.format(self.candidate_func))

    def blocks_locate(self, arg=None):
        '''
        补丁基本块定位
        '''
        if arg is None:
            # 无参调用,调用当前图
            self.cur_blocks['funcname'] = self.cfg['origin'].funcname
            self.cur_blocks['address_o'] = self.cfg['origin'].address
            self.cur_blocks['address_p'] = self.cfg['patch'].address
            traces = Trace(self.cfg['origin'].func_graph, self.cfg['patch'].func_graph)
        elif isinstance(arg, tuple):
            # 传入函数名和地址调用，参数的格式为('funcname':{'origin':address1, 'patch': address2})
            self.cur_blocks['funcname'] = arg[0]
            self.cur_blocks['address_o'] = arg[1]['origin']
            self.cur_blocks['address_p'] = arg[1]['patch']
            func_o, func_p = self.binfile.get_func_graphs(arg[0])
            traces = Trace(func_o, func_p)
        self.cur_blocks['traces'] = traces.get_trace()
        self.cur_blocks['traces_nodes'] = traces.traces2nodes()
        comlog.info('funcname: {}'.format(self.cur_blocks['funcname']))
        comlog.info('cur_blocks {}'.format(self.cur_blocks))
        return len(self.cur_blocks['traces_nodes'])

    def seman_analysis(self):
        '''
        语义分析
        '''
        nodes_o_list, nodes_p_list = self.cur_blocks['traces_nodes']
        sem_data = self.binfile.get_seman_data(nodes_o_list, nodes_p_list)
        seman_result = []
        for _sem in sem_data:
            # comlog.info('nodes {}'.format(_sem))
            if not _sem[0] or not _sem[1]:
                # 为空跳过
                continue
            sim = Semantic(*_sem, load_args=self.filenames)
            cur_pre = sim.get_pre_state()
            cur_post = sim.get_post_state()
            # comlog.debug(cur_pre)
            # comlog.debug(cur_post)
            cur_diff = sim.get_semidiff()
            is_security = sim.get_diff_semantic()
            seman_result.append((_sem[2:4], cur_diff, is_security))
            comlog.info('[*]\033[40;43m {} \033[0m'.format(cur_diff))
        return seman_result

    def analysis(self):
        '''
        快速分析
        '''
        nums = self.bin_filter()
        for i in range(nums):
            self.cfg_filter()
            self.blocks_locate()
            self.seman_analysis()
