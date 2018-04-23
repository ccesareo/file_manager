import re
import sys

if sys.version_info[0] > 2:
    _string_types = str,
else:
    _string_types = basestring,

_SQL_KEYWORDS = ('database', 'table', 'type')


class Query(object):
    class DBLANG(object):
        MYSQL = 'MYSQL'
        POSTGRES = 'postgresql'

    class OP(object):
        EQ = '='
        OR = 'OR'
        GT = '>'
        LT = '<'
        NEQ = '!='
        AND = 'AND'
        GTE = '>='
        LTE = '<='
        ISIN = 'IN'
        MATCH = '~'
        ISNIN = 'NOT IN'
        NMATCH = '!~'
        ISNULL = 'IS NULL'
        ISNOTNULL = 'IS NOT NULL'

        @staticmethod
        def get(language, operator, match_case):
            """
            Default operator enums are defined for the postgresql language.
            This method is used to apply any subtle change to the operator,
                or to get an operator for a different language.
            :param match_case:
            :type match_case:
            :param operator:
            :type operator:
            :param language:
            :type language:
            """
            if language == Query.DBLANG.MYSQL:
                if operator == Query.OP.MATCH:
                    return 'REGEXP'
                elif operator == Query.OP.NMATCH:
                    return 'NOT REGEXP'
                else:
                    return operator
            else:
                if operator in (Query.OP.MATCH, Query.OP.NMATCH) and not match_case:
                    operator += "*"
                return operator

    class ORDER(object):
        ASC = 'ASC'
        DESC = 'DESC'

    """
    :type _where_filter_group_stack: list[FilterGroup]
    """

    DEFAULT_LANG = None

    def __init__(self, table_name, **filters):
        self._where_filter_group_stack = []

        self._select_statement = _SelectStatement()
        self._from_statement = _FromStatement()
        self._where_statement = _WhereStatement()
        self._group_by_statement = _GroupByStatement()
        self._order_by_statement = _OrderByStatement()
        self._limit_statement = _LimitStatement()
        self._offset_statement = _OffsetStatement()

        self.start_filter_group(Query.OP.AND)

        if table_name:
            self._select_statement.set_columns(table_name)
            self._from_statement.table = table_name

        for column, value in sorted(filters.items()):
            self.add_filter(column, value)

    @staticmethod
    def format_query(raw_query):
        """
        Format a str from queryBuilding into a readable format for SQL.

        See QueryBuilder docTest for information on how to utilize the pprintQuery( ) method.

        :class:`QueryBuilder`

        :type raw_query: str
        :rtype: str
        :return: Return a string formatted for SQL to query a database.
        """
        inner_paren_regex = re.compile(r"([(][^)(]+[)])")
        inner_paren_matches = re.findall(inner_paren_regex, raw_query)
        query = re.sub(inner_paren_regex, '%%s', raw_query)

        string_reg = re.compile(r"'.+?(?<!')'(?!')")
        string_matches = re.findall(string_reg, query)
        query = re.sub(string_reg, '%s', query)

        query = query.replace('(', '(\n')
        query = query.replace(')', '\n)\n')
        query = query.replace('FROM', '\nFROM')
        query = query.replace('AS', '\nAS')
        query = query.replace('AND', '\nAND')
        query = query.replace('ON', '\nON')
        query = query.replace('WHERE', '\nWHERE')
        query = query.replace('ORDER', '\nORDER')
        query = query.replace('LIMIT', '\nLIMIT')
        query = query.replace('GROUP', '\nGROUP')
        new_query = ''
        tab_level = 0

        for line in query.splitlines(False):
            line = line.strip()
            if not line:
                continue
            if line.endswith('('):
                new_query += ('\t' * tab_level) + line + '\n'
                tab_level += 1
            elif line == ')':
                tab_level -= 1
                new_query += ('\t' * tab_level) + line + '\n'
            elif line.startswith('AS') or line.startswith('ON'):
                new_query += ('\t' * (tab_level + 1)) + line + '\n'
            elif line == ')':
                tab_level -= 1
                new_query += ('\t' * tab_level) + line + '\n'
            else:
                new_query += ('\t' * tab_level) + line + '\n'

        new_query = new_query % tuple(string_matches)
        new_query = new_query % tuple(inner_paren_matches)

        return new_query

    @staticmethod
    def format_sql_column_names(column_names):
        """
        :type column_names: list[str]
        :return: in place, no return
        """
        for i, column_name in enumerate(column_names):
            if column_name in _SQL_KEYWORDS:
                column_names[i] = '"%s"' % column_name

    def add_filter(self, lvalue, rvalue=None, operator=OP.EQ, match_case=True):
        self._where_filter_group_stack[-1].add_filter(lvalue, rvalue, operator, match_case)
        return self

    def add_filters(self, *filters):
        self._where_filter_group_stack[-1].add_filters(*filters)
        return self

    def add_group_by(self, column):
        self._group_by_statement.add_column(column)
        return self

    def add_order_by(self, column, direction):
        self._order_by_statement.add_sort(column, direction)
        return self

    def append_where_filter_group(self, filter_group):
        """
        Add a pre-built filter group object to the end of the stack.

        :type filter_group: FilterGroup
        """
        # if there are no groups then set the new filter group to the where statement
        # the _WhereStatement class will build the string.
        if not self._where_filter_group_stack:
            self._where_statement.filter_group = filter_group
        # else append the new group to the previous group and set the new group as the current group in the stack
        else:
            self._where_filter_group_stack[-1].add_filter_group(filter_group)

        self._where_filter_group_stack.append(filter_group)
        return self

    def build_query(self, language):
        statement = self._select_statement.get_string()
        statement += self._from_statement.get_string()
        statement += self._where_statement.get_string(language)

        if self._group_by_statement.is_valid():
            statement += self._group_by_statement.get_string()

        if self._order_by_statement.is_valid():
            statement += self._order_by_statement.get_string()

        if self._limit_statement.is_valid:
            statement += self._limit_statement.get_string()

        if self._offset_statement.is_valid:
            statement += self._offset_statement.get_string()

        return statement

    def columns(self):
        return self._select_statement.columns

    def end_filter_group(self):
        self._where_filter_group_stack.pop()
        return self

    def get_where_string(self, language):
        return self._where_statement.get_string(language)

    def set_limit(self, limit):
        self._limit_statement.set_limit(limit)
        return self

    def set_offset(self, offset):
        self._offset_statement.set_offset(offset)
        return self

    def start_filter_group(self, operator):
        filter_group = FilterGroup(operator)
        self.append_where_filter_group(filter_group)
        return self

    def table(self):
        """
        :rtype: str or None
        """
        return self._from_statement.table


class Filter(object):
    def __init__(self, lvalue, rvalue=None, operator=Query.OP.EQ, match_case=True):
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.operator = operator
        self.match_case = match_case

        if rvalue is None and self.operator == Query.OP.EQ:
            self.operator = Query.OP.ISNULL

    def __str__(self):
        return str((self.lvalue, self.operator, self.rvalue, self.match_case))

    def _format_filter(self, language):
        operator = Query.OP.get(language, self.operator, self.match_case)

        # FORMAT LVALUE
        lvalue = str(self.lvalue)

        # FORMAT RVALUE
        if self.rvalue is None:
            rvalue = None
        elif self.operator in (Query.OP.ISIN, Query.OP.ISNIN):
            fixed_vals = list()
            for v in self.rvalue:
                fixed_vals.append(str(v).replace("'", "''"))
            rvalue = "('%s')" % "', '".join(fixed_vals)
        else:
            rvalue = "'%s'" % str(self.rvalue).strip("'")

        if self.operator in (Query.OP.ISNULL, Query.OP.ISNOTNULL):
            return lvalue + ' ' + operator

        return "%s %s %s" % (lvalue, operator, rvalue)

    def get_string(self, language=None):
        language = language or Query.DEFAULT_LANG
        assert language, 'No default launguage set on QueryBuilder.'

        # RVALUE of None MUST be used with IS NULL or IS NOT NULL
        if self.rvalue is None:
            assert self.operator in (Query.OP.ISNULL, Query.OP.ISNOTNULL), \
                'Invalid operator for NULL. %s%s' % (self.lvalue, self.operator)

        # IS IN - IS NOT IN
        if type(self.rvalue) in (list, tuple, set) or self.operator in (Query.OP.ISIN, Query.OP.ISNIN):
            assert self.operator in (Query.OP.ISIN, Query.OP.ISNIN), \
                'Invalid operator for iterable. %s' % self.operator
            assert type(self.rvalue) in (
                list, tuple, set, Query), 'Rvalue must be iterable or QueryBuilder to use %s' % self.operator

        # HAS LVALUE
        assert self.lvalue is not None, 'Left value cannot be NULL.'

        return self._format_filter(language)


class _SelectStatement(object):
    def __init__(self):
        self.columns = list()

    def set_columns(self, table):
        self.columns = list()
        self.columns.append((table, '%s.*' % table))

    def get_string(self):
        column_names = [t[1] for t in self.columns]
        Query.format_sql_column_names(column_names)

        statement = 'SELECT '
        statement += ', '.join(column_names)
        statement += ' '
        return statement


class _FromStatement(object):
    def __init__(self):
        self.table = None

    def get_string(self):
        return 'FROM %s ' % self.table


class _WhereStatement(object):
    def __init__(self):
        self.filter_group = None

    def get_string(self, language):
        if not self.filter_group or not self.filter_group.has_filters():
            return ''

        statement = 'WHERE '
        statement += self.filter_group.get_string(language)
        statement += ' '
        return statement


class FilterGroup(object):
    def __init__(self, operator):
        self._operator = operator
        self._filters = []

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not FilterGroup.__eq__(self, other)

    def __hash__(self):
        return hash(','.join([str(filter_obj) for filter_obj in self._filters]))

    def __nonzero__(self):
        return self.has_filters()

    def add_filter(self, lvalue, rvalue=None, operator=Query.OP.EQ, match_case=True):
        if isinstance(lvalue, _string_types) and rvalue is None and operator in (Query.OP.EQ, Query.OP.NEQ):
            operator = Query.OP.ISNULL if operator == Query.OP.EQ else Query.OP.ISNOTNULL

        elif isinstance(lvalue, _string_types) and isinstance(rvalue, _string_types):
            if not rvalue and operator == Query.OP.EQ:
                rvalue = None
                operator = Query.OP.ISNULL
            if not rvalue and operator == Query.OP.NEQ:
                rvalue = None
                operator = Query.OP.ISNOTNULL

        if isinstance(rvalue, (list, tuple, set)):
            if operator == Query.OP.EQ:
                operator = Query.OP.ISIN
            elif operator == Query.OP.NEQ:
                operator = Query.OP.ISNIN

        self._filters.append(Filter(lvalue, rvalue=rvalue, operator=operator, match_case=match_case))

    def add_filters(self, *filters):
        self._filters.extend(filters)

    def add_filter_group(self, filter_group):
        self._filters.append(filter_group)

    def get_string(self, language):
        statement = '( '
        op = ' ' + self._operator + ' '
        statement += op.join(fo.get_string(language) for fo in self._filters if fo)
        statement += ' )'
        return statement

    def has_filters(self):
        return any([x for x in self._filters])


class _GroupByStatement(object):
    def __init__(self):
        self._columns = []

    def add_column(self, column):
        self._columns.append(column)

    def is_valid(self):
        return bool(self._columns)

    def get_string(self):
        column_names = self._columns[:]
        Query.format_sql_column_names(column_names)

        statement = 'GROUP BY '
        statement += ', '.join(column_names)
        statement += ' '
        return statement


class _OrderByStatement(object):
    class OrderByObject(object):
        def __init__(self, column, direction):
            self._column = column
            self._direction = direction

        def get_string(self):
            statement = ' '.join([self._column, self._direction])
            return statement

        def column(self):
            return self._column

        def direction(self):
            return self._direction

    def __init__(self):
        self._order_by_objects = []

    def add_sort(self, column, direction):
        self._order_by_objects.append(_OrderByStatement.OrderByObject(column, direction))

    def is_valid(self):
        return bool(self._order_by_objects)

    def get_string(self):
        statement = 'ORDER BY '
        statement += ', '.join(obo.get_string() for obo in self._order_by_objects)
        statement += ' '
        return statement

    def get_pairs(self):
        return [(obo.column(), obo.direction()) for obo in self._order_by_objects]


class _OffsetStatement(object):
    def __init__(self):
        self.offset = 0
        self.is_valid = False

    def is_valid(self):
        return self.is_valid

    def set_offset(self, limit):
        self.offset = limit
        self.is_valid = True

    def set_valid(self, valid):
        self.is_valid = valid

    def get_string(self):
        return 'OFFSET %s ' % self.offset


class _LimitStatement(object):
    def __init__(self):
        self.limit = 0
        self.is_valid = False

    def set_limit(self, limit):
        self.limit = limit
        self.is_valid = True

    def get_string(self):
        return 'LIMIT %s ' % self.limit
