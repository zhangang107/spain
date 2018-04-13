#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-11T15:28:57+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: simi_block.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-13T09:37:58+08:00
# @Copyright: Copyright by USTC

'''
杨寿国，基本块比对算法
'''
class SimiBlock(object):
    '''
    相似块类，提供基本块相似的判定算法
    此处使用最长公共子序列来计算基本块的相似度。
    建议：
        可以引入相似度算法 余弦相似度、欧几里得距离、皮尔逊相关度、Jaccard系数等
        这些算法之前实验过效果，在复杂情况下也不是很好。个人感觉在复杂情况下的关键是
        要将复杂的图切割成以及有关联的子图，分别求取子图，再合并结果。
    '''
    def __init__(self, graph_o, graph_p):
        '''
        @param graph_o 原函数
        @param graph_p 补丁函数
        '''
        self.graph_o = graph_o
        self.graph_p = graph_p
        self.scores = {}
        self.scores_P_O = {}

    def get_simi(self, threshold=0.8):
        '''
        调用接口
        @return tags {nodep:nodeo}一一匹配的基本块
        '''
        tags = {}
        for nodep in self.graph_p.nodes:
            self.scores_P_O[nodep] = {}
            for nodeo in self.graph_o.nodes:
                block1 = self._get_block(self.graph_p, nodep)
                block2 = self._get_block(self.graph_o, nodeo)
                self.scores_P_O[nodep][nodeo] = self._similarity(block1, block2)
        self.scores = self._similarity_with_content()
        self._n_scores = {}
        scores = []
        for nodep in self.scores:
            nodep_dic = self.scores[nodep]
            nd = sorted(nodep_dic.items(), key=lambda item:item[1], reverse=True)
            self._n_scores[nodep] = nd
            # 直接获取匹配度最高且>threshold的，组成tags
            if len(nd)>0:
                if nd[0][1]>threshold:
                    tags[nodep] = nd[0][0]
                    scores.append([{'nodep':nodep, 'nodeo':nd[0][0], 'score':nd[0][1]}])
        return tags , scores

    def _get_block(self, graph, n):
        '''
        构造需要比较的字符串，暂时 汇编助记符
        @param graph 要比较的函数
        @param n 要比较的节点
        '''
        block = graph.nodes[n]['mnem_list']
        return block

    def _similarity(self, block1, block2):
        '''
        算法1 利用最长公共子序列
        @param block1 待比较基本块字符串(可选特征：汇编助记符等)
        '''
        dp = [[0 for j in range(len(block2)+1)] for i in range(len(block1)+1)]
        for i in range(1, len(block1)+1):
            for j in range(1, len(block2)+1):
                if block1[i-1] == block2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max([dp[i-1][j], dp[i][j-1]])

        return dp[len(block1)][len(block2)]*2 / (len(block1)+len(block2))

    def _similarity_with_content(self):
        '''
        根据上下文信息重新计算相似度
        '''
        naive_score_rate = 0.8 #原来的得分占比重
        scores = {}
        scores_P_O = self.scores_P_O
        #算法待优化
        #算法效率待优化
        for nodeid_P in scores_P_O:
            scores[nodeid_P] = {}
            child_nodesP = list(self.graph_p.successors(nodeid_P))
            for nodeid_O in scores_P_O[nodeid_P]:
                scores[nodeid_P][nodeid_O] = naive_score_rate*scores_P_O[nodeid_P][nodeid_O]
                child_nodesO = list(self.graph_o.successors(nodeid_O))
                if len(child_nodesO) == 0 or len(child_nodesP) == 0:
                    scores[nodeid_P][nodeid_O] /= 0.9
                    continue
                child_rate = (1- naive_score_rate)/(len(child_nodesO)+len(child_nodesP))
                for p in child_nodesP:
                    for o in child_nodesO:
                        # 如果后继节点相似度太低，不计入得分 2018年04月09日11:28:31
                        if scores_P_O[int(p)][int(o)] < naive_score_rate:
                            continue
                        scores[nodeid_P][nodeid_O] += child_rate*scores_P_O[int(p)][int(o)]
        return scores
