#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T09:42:06+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: semantic.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-07T21:37:11+08:00
# @Copyright: Copyright by USTC

import re
import calangrv1
import copy
from mylog import comlog
# import conf

class Semantic(object):
    '''
    对每条对应轨迹进行语义分析，求出语义差值
    输入： 轨迹对应汇编码对集，地址对集
    外部资源输入：二进制文件路径（用于启动angr）

    #TODO
    '''
    def __init__(self, asms_o, asms_p, addrs_o, addrs_p):
        self.asms_o = asms_o
        self.asms_p = asms_p
        self.addrs_o = addrs_o
        self.addrs_p = addrs_p
        self._engine = None

    @property
    def engine(self):
        return self._engine

    def load_resource(self, **kwarg):
        if self._engine is None:
            print('engineer must set')
            return
        self._engine_ins = self._engine(**kwarg)

    def get_pre_state(self):
        return self._engine_ins.pre_state

    def get_post_state(self):
        return self._engine_ins.post_state

    def get_diff_semantic(self):
        pass

    def get_semidiff(self):
        pass

def get_pre_state(asms):
    reg = {}
    flag = {'N':0, 'Z':0, 'C':0, 'V':0}
    mem = set()
    if conf.arch == 'arm':
        for asm in asms:
            for word in asm.split():
                if calangrv1.check_mem(word) and word not in mem:
                    mem.add(word)
            for word in [a for a in re.split(' |,|\[|\]', asm) if a]:
                if calangrv1.check_reg(word) and word not in reg:
                    reg[word] = 0
            # opt = asm.split()[0]
            # calangr.handleflag(opt, flag)
    elif conf.arch == 'mips':
        for asm in asms:
            for word in asm.split():
                if calangrv1.check_mem_mips(word) and word not in mem:
                    mem.add(word)
            for word in [a for a in re.split(' |,|\[|\]', asm) if a]:
                if calangrv1.check_reg_mips(word) and word not in reg:
                    reg[word] = 0
    return (reg, flag, mem)

def get_post_state(addrs, post_state, proj):
    # for addr in addrs:
    #     calangr.update_state(addr, post_state, proj)
    # 改为调用calangr函数，以完成内部state更新
    calangrv1.update_state_from_addrs(addrs, post_state, proj)

def get_state(asms, addrs, proj):
    _asms = map(lambda s:' '.join(s.split()), asms)
    pre_state = list(get_pre_state(_asms))
    # print 'pre_state:'
    # print pre_state
    post_state = copy.deepcopy(pre_state)
    get_post_state(addrs, post_state, proj)
    # print 'post_state'
    # print post_state
    return pre_state,post_state

def get_diff_semantic(semantic_o, semantic_p, addrs_o, addrs_p, proj_o, proj_p, threshold):
    # print semantic_o
    semantic_o = map(calangr.delete_comment, semantic_o)
    # print semantic_o
    semantic_p = map(calangr.delete_comment, semantic_p)
    pre_state_o, post_state_o = get_state(semantic_o, addrs_o, proj_o)
    comlog.debug('angr o ok')
    pre_state_p, post_state_p = get_state(semantic_p, addrs_p, proj_p)
    comlog.debug('angr p ok')
    difference = 0
    count = 0
    comlog.debug(post_state_o)
    comlog.debug(post_state_p)
    for reg in post_state_p[0]:
        count += 1
        if reg not in post_state_o[0] or post_state_p[0][reg] != post_state_o[0][reg]:
            difference += 1
    for flag in post_state_p[1]:
        count += 1
        if flag not in post_state_o[1] or post_state_p[1][flag] != post_state_o[1][flag]:
            difference += 1
    for mem in post_state_p[2]:
        count += 1
        if mem not in post_state_o[2]:
            difference += 1
    diffrota = difference / float(count)
    comlog.debug('diffrota: {}'.format(diffrota))
    if diffrota > 0 and diffrota < threshold:
        return True
    else:
        return False

def get_semidiff(semantic_o, semantic_p, addrs_o, addrs_p, proj_o, proj_p):
    semantic_o = map(calangr.delete_comment, semantic_o)
    # print semantic_o
    semantic_p = map(calangr.delete_comment, semantic_p)
    pre_state_o, post_state_o = get_state(semantic_o, addrs_o, proj_o)
    comlog.debug('angr o ok')
    pre_state_p, post_state_p = get_state(semantic_p, addrs_p, proj_p)
    comlog.debug('angr p ok')
    difference = 0
    count = 0
    comlog.debug(post_state_o)
    comlog.debug(post_state_p)
    for reg in post_state_p[0]:
        count += 1
        if reg not in post_state_o[0] or post_state_p[0][reg] != post_state_o[0][reg]:
            difference += 1
    for flag in post_state_p[1]:
        count += 1
        if flag not in post_state_o[1] or post_state_p[1][flag] != post_state_o[1][flag]:
            difference += 1
    for mem in post_state_p[2]:
        count += 1
        if mem not in post_state_o[2]:
            difference +=   1
    diffrota = difference / float(count)
    return diffrota

if __name__ == '__main__':
    _asms = map(lambda s:' '.join(s.split()), asms)
    pre_state = get_pre_state(_asms)
    post_state = pre_state.copy()
    get_post_state(_asms, post_state)
