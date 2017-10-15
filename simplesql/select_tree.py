from typing import Dict, List
from collections import defaultdict


class TableColumnSets(object):

    def __init__(self):
        self.table_cols = defaultdict(list)

    def add_col(self, tbl_name):
        self.table_cols[tbl_name].append(tbl_name)

    def select_cols(self, for_table):
        return ", ".join(self.table_cols[for_table])


class TableNode(object):

    def __init__(self, tbl_name, root=True, table_column_sets=None):
        self.root = root
        self.tbl_name = tbl_name
        self.table_column_sets: TableColumnSets = TableColumnSets() if not table_column_sets else table_column_sets
        self.children: Dict['TableNode'] = dict()

    @property
    def is_terminal(self):
        return bool(self.children)

    def __getitem__(self, item):
        return self.children[item]

    def get_table_node(self, path: List[str]) -> 'TableNode':
        table_node = self
        for child_table in path:
            table_node = table_node[child_table]
        return table_node

    def add_child(self, tbl_name):
        self.children[tbl_name] = TableNode(tbl_name=tbl_name, root=False, table_column_sets=self.table_column_sets)

    def get_or_create_table_node(self, tbl_name: str) -> 'TableNode':
        if tbl_name not in self.children.keys():
            self.add_child(tbl_name=tbl_name)
        return self[tbl_name]

    def create_path(self, path: List[str]):
        table_node = self
        for child_tbl in path:
            table_node = table_node.get_or_create_table_node(tbl_name=child_tbl)

    def terminal_query(self):
        query = """
        SELECT {columns}
        FROM {tbl_name}
        """.format(columns=self.table_column_sets.select_cols(for_table=self.tbl_name), tbl_name=self.tbl_name)
        return query

    def nested_query(self):
        query = self.terminal_query()
        for child_tbl in self.children.keys():
            query += """
            JOIN ({child_query}) {child_tbl} ON {tbl_name}.{child_tbl}_id = {child_tbl}.id
            """.format(child_query=self.children[child_tbl].query(), child_tbl=child_tbl)
        return query

    def query(self):
        if self.is_terminal:
            return self.terminal_query()
        else:
            return self.nested_query()







