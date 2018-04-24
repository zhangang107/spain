#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T09:34:16+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: seman_engine.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-24T09:57:46+08:00
# @Copyright: Copyright by USTC

import angr
import claripy
import re
import copy
from spain import ARCH, comlog

'''
语义分析：
    分析 寄存器(reg)、内存位置(mem)、标志位(flag)的变化
由于汇编码运行模拟器的实现过于复杂，暂使用angr语义分析模块完成大部分工作即寄存器值的变化
    angr对标志位的变化有所涉及，可试用SimState.regs.flags.chop()[0:4]只涉及4个标志位(n,z,c,v)
    补充： mips下，angr中 SimState.regs 没有 flags属性
    angr对内存位置不够友好，因此内存位置暂使用自定义分析
'''
class AngrEngine(object):
    '''
    语义分析引擎之angr语义分析
    本次使用angr语义分析，主要用于寄存器标志的分析,同时可分析标志位
    angr中:
    reg_names = {
        8: 'r0',
        12: 'r1',
        16: 'r2',
        20: 'r3',
        24: 'r4',
        28: 'r5',
        32: 'r6',
        36: 'r7',
        40: 'r8',
        44: 'r9',
        48: 'r10',
        52: 'r11',
        56: 'r12',
        60: 'sp',
        64: 'lr',
        68: 'pc',
    }
    '''
    proj = None
    proj_file_path = None
    def __init__(self, file_path=None):
        # self.__init_proj(file_path)
        self.proj = angr.Project(file_path)

    # @classmethod
    # def __init_proj(cls, file_path):
    #     '''
    #     使用类变量，检查proj是否已经创建，没有才创建
    #     '''
    #     if not cls.proj or not cls.proj_file_path:
    #         cls.proj = angr.Project(file_path)
    #         cls.file_path = file_path
    #     elif cls.proj and cls.proj_file_path == file_path:
    #         return
    #     else:
    #         comlog.debug("something wrong")

    def __sim_block(self, addr_start, addr_end, state=None):

        ip = addr_start
        while ip < addr_end:
            state.ip = claripy.BVV(ip, 32)
            # print 'ip:', state.ip
            # print 'size:', addr_end-addr_start
            # s_tmp = self.proj.factory.blank_state()
            # s_tmp.ip = claripy.BVV(ip, 32)
            # state = (self.proj.factory.successors(state, size=addr_end-addr_start)).all_successors[0]
            st = (state.step(size=addr_end-ip, jumpkind='Ijk_Boring')).all_successors[0]
            self.__copy_regs2state(st, state)
            # state.regs.set_state(st)
            comlog.debug('------->{}'.format(state))
            # print 'regs:\n'
            # print_reg(state, regs)
            ip += (self.proj.factory.block(ip)).size
        # comlog.debug(type(state))
        # print '\n'
        # print state
        # print '\n\n'
        # self.print_reg(state, regs)
        return ip, state

    def __init_state(self, addr):
        s = self.proj.factory.blank_state()
        s.ip = addr
        for reg in self.regs:
            s.regs.__setattr__(reg.lower(), self.regs[reg])
        return s

    def __eval_update_regs(self, SimState):
    	self.print_reg(SimState)
    	for reg in self.regs:
    		self.regs[reg] = SimState.solver.eval(SimState.regs.get(reg.lower()))
        return self.regs

    def __eval_update_flag(self, SimState):
        if not hasattr(SimState.regs, 'flags'):
            return self.flag
        else:
            for k, v in zip(self.flag, SimState.regs.flags.chop()[0:4]):
                self.flag[k] = SimState.solver.eval(v)
            return self.flag

    def print_reg(self, s):
        '''
        打印寄存器与值
        '''
    	for reg in self.regs:
    		comlog.debug('{}, {}'.format(reg, s.regs.get(reg.lower())))

    def __copy_regs2state(self, s1, s2):
        '''
        复制状态间的寄存器值
        '''
        # if not regs:
        #     regs = ['r8', 'r6', 'r2']
        for reg in self.regs:
            reg = reg.lower()
            value = s1.registers.load(reg)
            s2.registers.store(reg, value)
        if hasattr(s1.regs, 'flags'):
            s2.regs.flags = s1.regs.flags

    def update_state_from_addrs(self, addrs, pre_state):
        '''
        从状态模拟器中更新post_state
        @param addrs 地址列表,其中元素addres为二元组, addres[0]基本块起始地址,addres[1]基本块结束地址
        @param pre_state 前状态
        '''
        self.addrs = addrs
        post_state = copy.deepcopy(pre_state)
        self.regs = post_state['reg'].copy()
        self.flag = post_state['flag'].copy()
        if len(addrs) < 1:
            return
        state = self.__init_state(self.addrs[0][0])
        for addr in self.addrs:
            comlog.debug('{}, {}'.format(hex(addr[0]), hex(addr[1])))
            ip, state = self.__sim_block(addr[0], addr[1], state)
            state.ip = claripy.BVV(ip, 32)
        # print "last state:\n", state
        # update_regs(state, post_state[0])
        post_state['reg'] = self.__eval_update_regs(state)
        post_state['flag'] = self.__eval_update_flag(state)
        return post_state


class SemanticEngine(object):
    '''
    语义分析引擎类
    统筹三元组识别器和代码模拟器
    提供get_pre_state函数和get_post_state
    完成必要资源的装载
    '''
    def __init__(self, asms, addrs, arch=None):
        '''
        asms: 汇编码集
        arch: 架构（暂时指arm或mips）
        '''
        self._arch = arch
        self.asms = asms
        self.addrs = addrs
        self.__pre_state = None
        if self._arch is None:
            self._arch = ARCH
        self.__init_state()
        self._sim = AngrEngine
        self._sim_ins = None

    def get_pre_state(self):
        return self.__pre_state

    def get_post_state(self):
        return self._sim_ins.update_state_from_addrs(addrs=self.addrs, pre_state=self.__pre_state)

    def _load(self, load_args):
        '''
        完成必要资源的装载
        '''
        self._sim_ins = self._sim(file_path=load_args)

    @property
    def pre_state(self):
        return self.__pre_state

    @pre_state.setter
    def pre_state(self, pre_state):
        self.__pre_state = pre_state

    @pre_state.getter
    def pre_state(self):
        if self.__pre_state is None:
            self.__init_state()
        return self.__pre_state

    @property
    def arch(self):
        return self._arch

    @arch.setter
    def arch(self, arch):
        self._arch = arch

    @classmethod
    def check_reg(cls, word):
        # arm 寄存器
        # 寄存器已R开头 或 SP 或 PC
        matchObj = re.search(r'^(R\d+|SP|PC)$', word, re.M|re.I)
        return matchObj and True or False

    @classmethod
    def check_reg_mips(cls, word):
        # mips 寄存器
        # 以$开头, 要去掉$
        matchObj = re.search(r'^(\$\w+)', word, re.M|re.I)
        return matchObj and True or False

    @classmethod
    def check_mem(cls, word):
        # arm 内存位置
        # 内存位置形如: []或 loc_
        matchObj = re.search(r'^(\[.+\])', word, re.M|re.I)
        return matchObj and True or False

    @classmethod
    def check_mem_mips(cls, word):
        # mips 内存位置
        # 形如 0x7578+var_7568($sp)， 0($v1)
        matchObj = re.search(r'^(.+\(\$\w+\))', word, re.M|re.I)
        return matchObj and True or False

    @classmethod
    def delete_comment(cls, asm):
        p = re.compile(r'(.*);(.*)')
        return p.sub(r'\1', asm)

    def __check_mem(self, word):
        if self._arch == 'arm':
            return self.check_mem(word)
        elif self._arch == 'mips':
            return self.check_mem_mips

    def __check_reg(self, word):
        if self._arch == 'arm':
            return self.check_reg(word)
        elif self._arch == 'mips':
            return self.check_reg_mips(word)

    def _eval_reg(self, reg):
        '''
        格式处理寄存器名，其实是在mips测试中发现$s0 属性bug,需要去掉$
        '''
        if self._arch == 'mips':
            return reg[1:]
        else:
            return reg

    def __init_state(self):
        '''
        初始化状态，可获取pre_state,与具体架构有关
        '''
        reg = {}
        flag = {'N':0, 'Z':0, 'C':0, 'V':0}
        mem = set()
        for asm in self.asms:
            for word in asm.split():
                if self.__check_mem(word) and word not in mem:
                    mem.add(word)
                for word in [a for a in re.split(' |,|\[|\]', asm) if a]:
                    if self.__check_reg(word) and self._eval_reg(word) not in reg:
                        reg[self._eval_reg(word)] = 0
        self.__pre_state = {'reg':reg, 'flag':flag, 'mem':mem}
