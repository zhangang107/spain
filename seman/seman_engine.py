#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T09:34:16+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: seman_engine.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-03T09:41:51+08:00
# @Copyright: Copyright by USTC

import angr
import claripy
import re

'''
语义分析：
    分析 寄存器(reg)、内存位置(mem)、标志位(flag)的变化
由于汇编码运行模拟器的实现过于复杂，暂使用angr语义分析模块完成大部分工作即寄存器值的变化
    angr对标志位的变化有所涉及，可试用SimState.regs.flags.chop()[0:4]只涉及4个标志位(n,z,c,v)
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
        self.__init_proj()
        self.post_state = post_state

    @classmethod
    def __init_proj(cls, file_path):
        '''
        使用类变量，检查proj是否已经创建，没有才创建
        '''
        if not cls.proj or not cls.proj_file_path:
            cls.proj = angr.Project(file_path)
            cls.file_path = file_path
        elif cls.proj and cls.proj_file_path == file_path:
            return
        else:
            print("something wrong")

    def __sim_block(self, addr_start, addr_end, state=None):

        ip = addr_start
        while ip < addr_end:
            state.ip = claripy.BVV(ip, 32)
            # print 'ip:', state.ip
            # print 'size:', addr_end-addr_start
            s = proj.factory.blank_state()
            s.ip = claripy.BVV(ip, 32)
            # state = (proj.factory.successors(state, size=addr_end-addr_start)).all_successors[0]
            st = (state.step(size=addr_end-addr_start)).all_successors[0]
            self.__copy_regs2state(st, state)
            # state.regs.set_state(st)
            print '------->', state
            # print 'regs:\n'
            # print_reg(state, regs)
            ip += (proj.factory.block(ip)).size
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
            s.regs.__setattr__(reg.lower(), regs[reg])
        return s

    def __eval_update_regs(self, SimState):
    	self.print_reg(SimState)
    	for reg in self.regs:
    		self.regs[reg] = SimState.solver.eval(SimState.regs.get(reg.lower()))

    def __eval_update_flag(self, SimState):
        for k, v in zip(self.flag, SimState.regs.flags.chop()[0:4]):
            self.flag[k] = SimState.solver.eval(v)

    def print_reg(self, s):
        '''
        打印寄存器与值
        '''
    	for reg in self.regs:
    		print reg, s.regs.get(reg.lower())

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
        s2.regs.flags = s1.regs.flags

    def update_state_from_addrs(self, addrs=None, post_state=None):
        '''
        从状态模拟器中更新post_state
        '''
        if addrs:
            self.addrs = addrs
        if post_state:
            self.post_state = post_state
        regs = self.post_state[0].copy()
        if len(addrs) < 1:
            return
        s = self.__init_state(self.addrs[0][0])
        state = s
        for addr in self.addrs:
            print(hex(addr[0]), hex(addr[1]))
            ip, state = sim_block(addr[0], addr[1], state)
            state.ip = claripy.BVV(ip, 32)
        # print "last state:\n", state
        # update_regs(state, post_state[0])
        self.__eval_update_regs(state)
        self.__eval_update_flag(state)

class SemanticEngine(object):
    '''
    语义分析引擎之自定义分析
    组合AngrEngine完成语义分析
    主要完成angr分析的前期预处理以及完善内存位置分析
    '''
    def __init__(self, asms, arch='arm'):
        '''
        asms: 汇编码集
        arch: 架构（暂时指arm或mips）
        '''
        self._arch = arch
        self.asms = asms
        self.__reg = None
        self.__flag = None
        self.__mem = None
        self.__pre_state = None

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
        # 以$开头
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

    def __init_state(self):
        '''
        初始化状态，可获取pre_state
        '''
        reg = {}
        flag = {'N':0, 'Z':0, 'C':0, 'V':0}
        mem = set()
        for asm in self.asms:
            for word in asm.split():
                if self.__check_mem(word) and word not in mem:
                    mem.add(word)
                for word in [a for a in re.split(' |,|\[|\]', asm) if a]:
                    if self.__check_reg(word) and word not in reg:
                        reg[word] = 0
        self.__pre_state = (reg, flag, mem)



if __name__ == '__main__':
    asms = ('ADD     R8, R6, #0x13',
            'LDR     R2, =0x5C9',
            'LDR     R1, =0x17694C',
            'MOV     R0, R8',
            'BL      CRYPTO_malloc',
            'MOV     R7, R0',
            'MOV     R3, #2',
            'STRB    R3, [R0]',
            'MOV     R3, R6,LSR#8',
            'STRB    R3, [R0,#1]',
            'STRB    R6, [R0,#2]',
            'ADD     R9, R0, #3',
            'MOV     R2, R6',
            'ADD     R1, R5, #3',
            'MOV     R0, R9',
            'BL      sub_115D8',
            'MOV     R1, #0x10',
            'ADD     R0, R9, R6',
            'BL      RAND_pseudo_bytes',
            'MOV     R3, R8',
            'MOV     R2, R7',
            'MOV     R1, #0x18',
            'MOV     R0, R4',
            'BL      dtls1_write_bytes',
            'SUBS    R5, R0, #0',
            'BLT     loc_79E28', )
    print 'start...'
    # proj = angr.Project('./openssl-arm-f')
    proj = None
    regs = init_regs(asms)
    print regs
    print 'end...'
