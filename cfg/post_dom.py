#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-02T15:53:40+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: post_dom.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-02T16:01:48+08:00
# @Copyright: Copyright by USTC

import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from itertools import tee


def leniter(iterator):
    """
    leniter(iterator): return the length of an iterator, iterator,consuming it."""
    if hasattr(iterator, "__len__"):
        return len(iterator)
    nelements = 0
    iter_copy, it = tee(iterator)
    for _ in iter_copy:
        nelements += 1
    return (nelements, it)

class ContainerNode(object):
    """
    A container node.

    Only used in post-dominator tree generation. We did this so we can set the index property without modifying the
    original object.
    """
    def __init__(self, obj):
        self._obj = obj
        self.index = None

    @property
    def obj(self):
        return self._obj

    def __eq__(self, other):
        if isinstance(other, ContainerNode):
            return self._obj == other._obj and self.index == other.index
        return False

class Dom(object):
    """
    return dom of CFG graph
    """
    def __init__(self, cfg, start=None, no_construct=False):
        """
        Constructor.

        :param cfg:             The control flow graph upon which this control dependence graph will build
        :param start:           The starting point to begin constructing the control dependence graph
        :param no_construct:    Skip the construction step. Only used in unit-testing.
        """
        self._ancestor = None
        self._semi = None
        self._post_dom = None
        self._label = None
        self._normalized_cfg = None
        self._cfg = cfg
        if start != None:
            self._entry = start
        else:
            self._entry = 'A'
    #
    # Public methods
    #

    def run(self):
        """
        test run
        """
        self._pd_construct()

    def get_post_dominators(self):
        """
        Return the post-dom tree
        """
        return self._post_dom

    def get_rdf(self):
        return self._df_construct(self._post_dom)

    #
    # Private methods
    #

    #
    # Dominance frontier related
    #

    def _df_construct(self, postdom):
        """
        Construct a dominance frontier based on the given post-dominator tree.

        This implementation is based on figure 2 of paper An Efficient Method of Computing Static Single Assignment
        Form by Ron Cytron, etc.

        :param postdom: The post-dominator tree
        :returns:        A dict of dominance frontier
        """

        DF = { }

        # Perform a post-order search on the post-dom tree
        for x in nx.dfs_postorder_nodes(postdom):
            if x != 'start_node' and x != 'end_node':
                DF[x] = self._post_dom.predecessors(x).next()
        return DF
    #
    # Post-dominator tree related
    #
    def _pd_construct(self):
        """
        Find post-dominators for each node in CFG.

        This implementation is based on paper A Fast Algorithm for Finding Dominators in a Flow Graph by Thomas
        Lengauer and Robert E. Tarjan from Stanford University, ACM Transactions on Programming Languages and Systems,
        Vol. 1, No. 1, July 1979
        """

        # Step 1

        _normalized_cfg, vertices, parent = self._pd_normalize_graph()
        # vertices is a list of ContainerNode(CFGNode) instances
        # parent is a dict storing the mapping from ContainerNode(CFGNode) to ContainerNode(CFGNode)
        # Each node in normalized_cfg is a ContainerNode(CFGNode) instance

        bucket = defaultdict(set)
        dom = [None] * (len(vertices))
        self._ancestor = [None] * (len(vertices) + 1)

        for i in xrange(len(vertices) - 1, 0, -1):
            w = vertices[i]

            # Step 2
            if w not in parent:
                # It's one of the start nodes_entry_entry
                continue

            predecessors = _normalized_cfg.predecessors(w)
            for v in predecessors:
                u = self._pd_eval(v)
                if self._semi[u.index].index < self._semi[w.index].index:
                    self._semi[w.index] = self._semi[u.index]

            bucket[vertices[self._semi[w.index].index].index].add(w)

            self._pd_link(parent[w], w)

            # Step 3
            for v in bucket[parent[w].index]:
                u = self._pd_eval(v)
                if self._semi[u.index].index < self._semi[v.index].index:
                    dom[v.index] = u
                else:
                    dom[v.index] = parent[w]

            bucket[parent[w].index].clear()

        for i in xrange(1, len(vertices)):
            w = vertices[i]
            if w not in parent:
                continue
            if dom[w.index].index != vertices[self._semi[w.index].index].index:
                dom[w.index] = dom[dom[w.index].index]

        self._post_dom = nx.DiGraph() # The post-dom tree described in a directional graph
        for i in xrange(1, len(vertices)):
            if dom[i] is not None and vertices[i] is not None:
                self._post_dom.add_edge(dom[i].obj, vertices[i].obj)

        #self._pd_post_process()
        #nx.draw(self._post_dom,arrows=True, with_labels = True, node_size = 350, node_color='r')
        #plt.show()

        # Create the normalized_cfg without the annoying ContainerNodes

        self._normalized_cfg = nx.DiGraph()
        for src, dst in _normalized_cfg.edges():
            self._normalized_cfg.add_edge(src.obj, dst.obj)
        #nx.draw(self._normalized_cfg,arrows=True, with_labels = True, node_size = 350, node_color='r')
        #plt.show()

    def _pd_normalize_graph(self):
        # We want to reverse the CFG, and label each node according to its
        # order in a DFS

        graph = nx.DiGraph()

        #n = _entry
        n = self._entry

        queue = [ n ]
        '''
        start_node = TemporaryNode("start_node")
        # Put the start_node into a Container as well
        start_node = ContainerNode(start_node)
        '''
        start_node = ContainerNode("start_node")

        #start_node = 'A'
        container_nodes = { }

        traversed_nodes = set()
        while len(queue) > 0:
            node = queue.pop()

            '''
            if type(node) is TemporaryNode:
                # This is for testing
                successors = _acyclic_cfg.graph.successors(node)
            else:
                # Real CFGNode!
                successors = _acyclic_cfg.get_successors(node)
            '''

            successors = self._cfg.successors(node)
            # Put it into a container
            if node in container_nodes:
                container_node = container_nodes[node]
            else:
                container_node = ContainerNode(node)
                container_nodes[node] = container_node

            traversed_nodes.add(container_node)

            lenit, successors = leniter(successors)
            if lenit == 0:
                # Add an edge between this node and our start node
                graph.add_edge(start_node, container_node)

            for s in successors:
                if s in container_nodes:
                    container_s = container_nodes[s]
                else:
                    container_s = ContainerNode(s)
                    container_nodes[s] = container_s
                graph.add_edge(container_s, container_node) # Reversed
                if container_s not in traversed_nodes:
                    queue.append(s)

        # Add a start node and an end node
        graph.add_edge(container_nodes[n], ContainerNode("end_node"))
        #nx.draw(graph,arrows=True, with_labels = False, node_size = 350, node_color='r')
        #plt.show()

        all_nodes_count = len(traversed_nodes) + 2 # A start node and an end node
        # l.debug("There should be %d nodes in all", all_nodes_count)
        counter = 0
        vertices = [ ContainerNode("placeholder") ]
        scanned_nodes = set()
        parent = {}
        while True:
            # DFS from the current start node
            stack = [ start_node ]
            while len(stack) > 0:
                node = stack.pop()
                counter += 1

                # Mark it as scanned
                scanned_nodes.add(node)

                # Put the container node into vertices list
                vertices.append(node)

                # Put each successors into the stack
                successors = graph.successors(node)

                # Set the index property of it
                node.index = counter

                for s in successors:
                    if s not in scanned_nodes:
                        stack.append(s)
                        parent[s] = node
                        scanned_nodes.add(s)

            if counter >= all_nodes_count:
                break

            # l.debug("%d nodes are left out during the DFS. They must formed a cycle themselves.", all_nodes_count - counter)
            # Find those nodes
            leftovers = [ s for s in traversed_nodes if s not in scanned_nodes ]
            graph.add_edge(start_node, leftovers[0])
            # We have to start over...
            counter = 0
            parent = {}
            scanned_nodes = set()
            vertices = [ ContainerNode("placeholder") ]

        self._semi = vertices[::]
        self._label = vertices[::]

        return (graph, vertices, parent)

    def _pd_eval(self,v):
        if self._ancestor[v.index] is None:
            return v
        else:
            self._pd_compress(v)
            return self._label[v.index]

    def _pd_link(self, v, w):
        self._ancestor[w.index] = v

    def _pd_compress(self, v):
        if self._ancestor[self._ancestor[v.index].index] != None:
            self._pd_compress(self._ancestor[v.index])
            if self._semi[self._label[self._ancestor[v.index].index].index].index < self._semi[self._label[v.index].index].index:
                self._label[v.index] = self._label[self._ancestor[v.index].index]
            self._ancestor[v.index] = self._ancestor[self._ancestor[v.index].index]
