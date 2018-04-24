#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T09:42:06+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: semantic.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-18T15:43:07+08:00
# @Copyright: Copyright by USTC

from seman_engine import SemanticEngine
from spain import comlog

class Semantic(object):
    '''
    对每条对应轨迹进行语义分析，求出语义差值
    输入： 轨迹对应汇编码对集，地址对集
    外部资源输入：二进制文件路径（用于启动angr）
    要分析原文件和补丁文件,因此需要两个语义分析引擎实例
    '''
    def __init__(self, asms_o, asms_p, addrs_o, addrs_p, load_args=None):
        '''
        @param asms_o 原文件汇编代码块
        @param asms_p 补丁文件汇编代码块
        @param addrs_o 原文件基本块的首末地址列表
        @param addrs_p 补丁文件基本块的首末地址列表
        '''
        self.asms_o = asms_o
        self.asms_p = asms_p
        self.addrs_o = addrs_o
        self.addrs_p = addrs_p
        self._engine = SemanticEngine
        self._engine_ins_o = None
        self._engine_ins_p = None
        self._state_o = {'pre_state':None, 'post_state':None}
        self._state_p = {'pre_state':None, 'post_state':None}
        self._init_engine()
        self._load_resource(load_args)

    @property
    def engine(self):
        '''
        语义分析引擎，此处可先用angr封装
        '''
        return self._engine

    def _init_engine(self):
        '''
        语义分析引擎初始化
        '''
        self._engine_ins_o = self._engine(asms=self.asms_o, addrs=self.addrs_o)
        self._engine_ins_p = self._engine(asms=self.asms_p, addrs=self.addrs_p)

    def _load_resource(self, filenames):
        '''
        装载必要资源，此处为装载angr工程
        @param filenames 二进制文件长路径名
        '''
        self._engine_ins_o._load(load_args=filenames[0])
        self._engine_ins_p._load(load_args=filenames[1])

    def get_pre_state(self):
        '''
        获取三元组pre_state
        '''
        self._state_o['pre_state'] = self._engine_ins_o.get_pre_state()
        self._state_p['pre_state'] = self._engine_ins_p.get_pre_state()
        return self._state_o['pre_state'], self._state_p['pre_state']

    def get_post_state(self):
        '''
        获取三元组post_state
        '''
        self._state_o['post_state'] = self._engine_ins_o.get_post_state()
        self._state_p['post_state'] = self._engine_ins_p.get_post_state()
        return self._state_o['post_state'], self._state_p['post_state']

    def get_diff_semantic(self, threshold=0.1):
        '''
        获取语义判定
        '''
        diffrota = self.get_semidiff()
        if diffrota > 0 and diffrota < threshold:
            return True
        else:
            return False

    def get_semidiff(self):
        '''
        获取语义差值
        '''
        difference = 0
        count = 0
        post_state_o = self._state_o['post_state']
        post_state_p = self._state_p['post_state']
        comlog.debug(post_state_o)
        comlog.debug(post_state_p)
        for reg in post_state_p['reg']:
            count += 1
            if reg not in post_state_o['reg'] or post_state_p['reg'] != post_state_o['reg']:
                difference += 1
        for flag in post_state_p['flag']:
            count += 1
            if flag not in post_state_o['flag'] or post_state_p['flag'] != post_state_o['flag']:
                difference += 1
        for mem in post_state_p['mem']:
            count += 1
            if mem not in post_state_o['mem']:
                difference += 1
        diffrota = difference / float(count)
        comlog.debug('diffrota: {}'.format(diffrota))
        return diffrota
