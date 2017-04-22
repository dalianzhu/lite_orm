import inspect
import logging
import my_models.set_logging as set_logging

if not set_logging.ISSET:
    set_logging.set_logger()

class Model(object):
    def __init__(self):
        pass

    def save(self):
        """
        insert into 表名(id,name) values(0,'XX')
        """
        table_name = self.__class__.__name__
        table_property = self.__dict__.items()

        sql = "insert into {table_name}({names}) values({values})"
        names = ""
        values = ""
        for name, val in table_property:
            names += name + ","
            if isinstance(val, int):
                values += str(val) + ","
            else:
                values += "'{}'".format(val) + ","

        names = names[:-1]
        values = values[:-1]

        sql = sql.format(table_name=table_name, names=names, values=values)
        # logging.debug("sql {}".format(sql))
        return True
    
    @classmethod
    def where(cls, search_obj):
        sql = "select * from {table_name} where {query}"
        table_name = cls.__name__

        query = search_obj.sql
        sql = sql.format(table_name=table_name, query=query)
        # logging.debug("sql {}".format(sql))
        pre_exec = PreExec()
        pre_exec.sql = sql
        return pre_exec
    
    @classmethod
    def query_where(cls, query):
        sql = "select * from {table_name} where {query}"
        table_name = cls.__name__

        sql = sql.format(table_name=table_name, query=query)
        # logging.debug("sql {}".format(sql))
        pre_exec = PreExec()
        pre_exec.sql = sql
        return pre_exec


class SQ(object):
    def __init__(self):
        self.sql = ""

    @classmethod
    def eq(cls, **kwargs):
        sq = SQ()
        for k in kwargs:
            if isinstance(kwargs[k], int):
                sq.sql = "{}={}".format(k,kwargs[k])
            else:
                sq.sql = "{}='{}'".format(k,kwargs[k])
            # logging.debug("sql {}".format(self.sql))
            break
        return sq

    def or_eq(self, **kwargs):
        return self._opt("or","=", **kwargs)
    
    def and_eq(self, **kwargs):
        return self._opt("and","=", **kwargs)

    @classmethod
    def more(cls, **kwargs):
        sq = SQ()
        for k in kwargs:
            if isinstance(kwargs[k], int):
                sq.sql = "{}>{}".format(k,kwargs[k])
            else:
                sq.sql = "{}>'{}'".format(k,kwargs[k])
            # logging.debug("sql {}".format(self.sql))
            break
        return sq

    def and_more(self, **kwargs):
        return self._opt("and",">", **kwargs)

    def or_more(self, **kwargs):
        return self._opt("or",">", **kwargs)


    @classmethod
    def less(cls, **kwargs):
        sq = SQ()
        for k in kwargs:
            if isinstance(kwargs[k], int):
                sq.sql = "{}<{}".format(k,kwargs[k])
            else:
                sq.sql = "{}<'{}'".format(k,kwargs[k])
            # logging.debug("sql {}".format(self.sql))
            break
        return sq

    def or_less(self, **kwargs):
        return self._opt("or","<", **kwargs)
    
    def and_less(self, **kwargs):
        return self._opt("and","<", **kwargs)

    def _opt(self,relation, op, **kwargs):
        for k in kwargs:
            if isinstance(kwargs[k], int):
                self.sql += " {} {}{}{}".format(relation, k,op,kwargs[k])
            else:
                self.sql += " {} {}{}'{}'".format(relation, k,op,kwargs[k])
            # logging.debug("sql {}".format(self.sql))
            break
        return self
    
    def and_merge(self, search_query_obj):
        self.sql = "({}) and ({})".format(self.sql, search_query_obj.sql)
        # logging.debug("sql {}".format(self.sql))
        return self

class PreExec(object):
    def order_by_desc(self, col_name):
        self.sql += " order by {} desc".format(col_name)
        return self

    def order_by_asc(self, col_name):
        self.sql += " order by {} asc".format(col_name)
        return self

    def limit(self, *nums):
        query = ""
        for item in nums:
            query += str(item) + ","
        query = query[:-1]
        self.sql += " limit {}".format(query)
        return self

    def exec(self):
        exec = Exec()
        exec.sql = self.sql
        return exec.exec()
    


class Exec(object):
    def __init__(self):
        self.sql = ""

    def exec(self):
        logging.debug("exec sql {}".format(self.sql))