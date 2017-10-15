import itertools

from pyparsing import (Literal,
                       Word,
                       ZeroOrMore,
                       Forward,
                       nums,
                       oneOf,
                       alphas,
                       Suppress,
                       Group,
                       replaceWith,
                       QuotedString,
                       delimitedList)


class SimpleSQL(object):

    def __init__(self, query):
        self.pre_query = query
        self.sub_query_count = itertools.count()

    @property
    def sub_query_index(self):
        return next(self.sub_query_count)

    def _list_pairs(self, lis):
        pairs = list()
        for v, w in zip(lis[:-1], lis[1:]):
            pairs.append((v, w))
        return pairs

    def _make_atomic(self, tables, col_name, op, value):
        terminal_clause = self._terminal_where_clause(table=tables[-1], col_name=col_name, op=op, value=value)
        if len(tables) > 1:
            fk_pairs = self._list_pairs(lis=tables)[::-1]
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

    def _terminal_where_clause(self, table, col_name, op, value):
        clause = """
        SELECT *
        FROM {table_name}
        WHERE {col_name} {op} {value}
        """.format(table_name=table, col_name=col_name, op=op, value=value)
        return clause

    def compiled_sql(self):
        where_op = oneOf('> >= < <= = IN !=') | Literal("NOT IN")
        number = Word(nums)
        string = (QuotedString(quoteChar="'") | QuotedString(quoteChar='"')).setParseAction(lambda x: '"' + x[0] + '"')
        where_val = number | string
        lpar = Literal('(')
        rpar = Literal(')')
        tables = Group(Word(alphas) + ZeroOrMore(Suppress(Literal('>>>')) + Word(alphas)))
        tbl_col = tables + Suppress(Literal('.')) + Word(alphas)
        where_clause = tbl_col + where_op + where_val
        where_clause.setParseAction(lambda x: self._make_atomic(tables=x[0], col_name=x[1], op=x[2], value=x[3]))
        expr = Forward()
        atom = where_clause | (lpar + expr + rpar)
        op = Literal("&").setParseAction(replaceWith("INTERSECT")) | Literal("|").setParseAction(replaceWith("UNION"))
        expr << (atom + ZeroOrMore(op + expr)) | (Suppress("(") + atom + ZeroOrMore(op + expr) + Suppress(")"))
        results = expr.parseString(self.pre_query)
        print(' '.join(results))
        return results




# simple_sql = SimpleSQL('((part.number = "abc") & (part..supplier.name = "Panasonic")) | (part.number = "xyz")')
simple_sql = SimpleSQL('(part.status = "ACTIVE") & (part>>>supplier.name = "Acme") & (part>>>warehouse>>>location.id = "BM10-00400") | (part.this = "today")')
sql = simple_sql.compiled_sql()