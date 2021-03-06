import itertools

import networkx as nx


class TableTree(object):

    def __init__(self):
        self._graph = nx.DiGraph()
        self.root_tbl_name = None
        self.sub_query_count = itertools.count()
        self.table_query_indices = dict()

    @property
    def sub_query_index(self):
        return next(self.sub_query_count)

    def table_parent(self, tbl_name):
        if nx.ancestors(self._graph, tbl_name):
            return list(nx.ancestors(self._graph, tbl_name))[0]
        else:
            return None

    def parent_sub_query_index(self, for_table):
        parent_name = self.table_parent(tbl_name=for_table)
        if parent_name:
            return self._graph.node[parent_name]['sub_query_index']
        else:
            return None

    @property
    def ordered_table_names(self):
        return nx.topological_sort(self._graph)

    def ordered_select_data(self):
        data = list()
        for tbl_name in self.ordered_table_names:
            data.append((tbl_name, self.table_cols(tbl_name=tbl_name)))
        return data

    def table_cols(self, tbl_name):
        return self._graph.node[tbl_name]['columns']

    def add_node(self, tbl_name, parent_tbl_name=None):
        if not self.root_tbl_name:
            self.root_tbl_name = tbl_name
        if not self._graph.has_node(tbl_name):
            sub_query_index = self.sub_query_index
            self._graph.add_node(tbl_name)
            self._graph.node[tbl_name]['columns'] = list()
            self._graph.node[tbl_name]['sub_query_index'] = sub_query_index
            self.table_query_indices[tbl_name] = sub_query_index
        if parent_tbl_name:
            self._graph.add_edge(parent_tbl_name, tbl_name)

    def add_node_column(self, tbl_name, col_name):
        self._graph.node[tbl_name]['columns'].append(col_name)


table_tree = TableTree()
table_tree.add_node('part')
table_tree.add_node(tbl_name='supplier', parent_tbl_name='part')
table_tree.add_node_column(tbl_name='part', col_name='part_number')
table_tree.add_node_column(tbl_name='part', col_name='date')
table_tree.add_node_column(tbl_name='supplier', col_name='part_number')
table_tree.add_node(tbl_name='location', parent_tbl_name='supplier')
table_tree.add_node_column(tbl_name='location', col_name='name')
for tbl_name in table_tree.ordered_table_names:
    print(tbl_name)
    print(table_tree.table_query_indices[tbl_name])
    print(table_tree.table_parent(tbl_name))
    print(table_tree.parent_sub_query_index(for_table=tbl_name))