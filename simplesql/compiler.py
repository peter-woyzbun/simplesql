import itertools

import pyparsing as pp

from .select_tree import TableNode


class Grammar(object):

    @property
    def name(self):
        name = pp.Word(pp.alphas, pp.alphanums + '_')
        return name

    @property
    def opt_ws(self):
        opt_ws = pp.Optional(pp.White())
        return opt_ws

    @property
    def primative(self):
        point = pp.Literal('.')
        number = pp.Word(pp.nums)
        integer = pp.Combine(pp.Optional('-') + number)
        float_ = pp.Combine(pp.Optional('-') + number + point + pp.OneOrMore(number))
        string = pp.quotedString
        true = pp.Literal("True") | pp.Literal("true") | pp.Literal("TRUE")
        false = pp.Literal("False") | pp.Literal("false") | pp.Literal("FALSE")
        boolean = true | false
        primative = float_ | integer | string | boolean
        return primative

    @property
    def primative_list(self):
        opt_ws = pp.Optional(pp.White())
        list_body = self.primative + pp.ZeroOrMore(opt_ws + pp.Literal(",") + opt_ws + self.primative)
        primative_list = pp.Combine(pp.Literal("(") + list_body + pp.Literal(")"))
        return primative_list

    @property
    def where_op(self):
        where_op = pp.oneOf('> >= < <= = IN !=') | pp.Literal("NOT IN")
        return where_op

    @property
    def where_clause_body(self):
        where_clause = pp.Combine(self.opt_ws + self.where_op + self.opt_ws + (self.primative | self.primative_list))
        return where_clause

    @property
    def tbl_col_pointer(self):
        tbl_col_pointer = pp.Group(self.name + pp.Suppress(".") + self.name + pp.ZeroOrMore(pp.Suppress(".") + self.name))
        return tbl_col_pointer

    @property
    def get_clause(self):
        get_clause = pp.Suppress("GET") + self.name
        return get_clause

    @property
    def intersect(self):
        intersect = pp.Literal("&").setParseAction(pp.replaceWith("INTERSECT"))
        return intersect

    @property
    def union(self):
        intersect = pp.Literal("|").setParseAction(pp.replaceWith("UNION"))
        return intersect


class Compiler(Grammar):

    def __init__(self, simple_sql_query):
        self.input_query = simple_sql_query
        self.output_query = ""
        self.where_clauses = list()
        self.select_tree = TableNode(tbl_name='')
        self.sub_query_count = itertools.count()

    @property
    def sub_query_index(self):
        return next(self.sub_query_count)

    def _make_query_base(self, tbl_name):
        query_base = """
        SELECT *
        FROM {tbl_name}
        """.format(tbl_name=tbl_name)
        self.output_query = query_base
        return query_base

    def _terminal_where_clause(self, tbl_name, col_name, clause_body):
        clause = """
        SELECT *
        FROM {tbl_name}
        WHERE {clause_body}
        """.format(tbl_name=tbl_name, col_name=col_name, clause_body=clause_body)
        return clause

    def _tbl_list_fk_pairs(self, tbl_list):
        pairs = list()
        for v, w in zip(tbl_list[:-1], tbl_list[1:]):
            pairs.append((v, w))
        return pairs

    def _make_atomic(self, tables, clause_body):
        col_name = tables.pop()
        terminal_clause = self._terminal_where_clause(table=tables[-1], col_name=col_name, clause_body=clause_body)
        if len(tables) > 1:
            fk_pairs = self._tbl_list_fk_pairs(tbl_list=tables)[::-1]
            nested_atomic = self._make_nested_atomic(terminal_clause=terminal_clause, fk_pairs=fk_pairs)
            atomic_query = nested_atomic
        else:
            atomic_query = terminal_clause
        return "( \n" + atomic_query + "\n )"

    def _make_nested_atomic(self, terminal_clause, fk_pairs):
        last_nested = terminal_clause
        for parent_table, child_table in fk_pairs:
            c_index = self.sub_query_index
            p_index = self.sub_query_index
            q = """
            SELECT *
            FROM {parent_table} q{p_index}
            RIGHT JOIN (
                {nested_query}
            ) q{c_index} ON q{c_index}.id = q{p_index}.{child_table}_id

            """.format(parent_table=parent_table,
                       child_table=child_table,
                       c_index=c_index,
                       p_index=p_index,
                       nested_query=last_nested)
            last_nested = q
        return last_nested

    def _terminal_where_clause(self, table, col_name, clause_body):
        clause = """
        SELECT *
        FROM {table_name}
        WHERE {col_name} {clause_body}
        """.format(table_name=table, col_name=col_name, clause_body=clause_body)
        return clause

    def run(self):
        get_clause = pp.Suppress(self.get_clause)

        where_clause = self.tbl_col_pointer + self.where_clause_body
        where_clause.setParseAction(lambda x: self._make_atomic(tables=x[0], clause_body=x[1]))

        lpar = pp.Literal('(')
        rpar = pp.Literal(')')
        expr = pp.Forward()
        atom = where_clause | (lpar + expr + rpar)

        op = self.intersect | self.union

        expr << (atom + pp.ZeroOrMore(op + expr)) | (pp.Suppress("(") + atom + pp.ZeroOrMore(op + expr) + pp.Suppress(")"))
        grammar = get_clause + pp.Optional(pp.Suppress('WHERE') + expr)

        print(" ".join(grammar.parseString(self.input_query)))


compiler = Compiler(simple_sql_query="GET part WHERE (part.active = 123 & part.warehouse.number IN ('abc', 123)) |"
                                     " (part.warehouse.location.name ='abc123')")
compiler.run()