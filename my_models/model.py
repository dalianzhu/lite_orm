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
            if isinstance(val, OneToMany) or isinstance(val, ManyToOne):
                continue

            names += name + ","
            if isinstance(val, int):
                values += str(val) + ","
            else:
                values += "'{}'".format(val) + ","

        names = names[:-1]
        values = values[:-1]

        pre_exec = PreExec()
        pre_exec.sql = sql.format(table_name=table_name, names=names, values=values)

        # logging.debug("sql {}".format(sql))
        return pre_exec.exec()

    def update(self):
        """
        update 表名 set id=1, name="haha" where id=1
        """
        table_name = self.__class__.__name__
        table_property = self.__dict__.items()

        sql = "update {table_name} set {query} where id={id})"
        names = []
        values = []
        for name, val in table_property:
            if isinstance(val, OneToMany) or isinstance(val, ManyToOne):
                continue
            if name=="id":
                continue
            if not val:
                continue   
            names.append(name)
            if isinstance(val, int):
                values.append(str(val))
            else:
                values.append("'{}'".format(val))

        query = ""
        for i in range(0,len(names)):
            query += "{}={},".format(names[i], values[i])
        query = query[:-1]

        pre_exec = PreExec()
        pre_exec.sql = sql.format(table_name=table_name, query=query, id=self.id)

        # logging.debug("sql {}".format(sql))
        return pre_exec.exec()
    
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

def eq(**kwargs):
    sq = SQ()
    for k in kwargs:
        if isinstance(kwargs[k], int):
            sq.sql = "{}={}".format(k,kwargs[k])
        else:
            sq.sql = "{}='{}'".format(k,kwargs[k])
        # logging.debug("sql {}".format(self.sql))
        break
    return sq

def neq(**kwargs):
    sq = SQ()
    for k in kwargs:
        if isinstance(kwargs[k], int):
            sq.sql = "{}<>{}".format(k,kwargs[k])
        else:
            sq.sql = "{}<>'{}'".format(k,kwargs[k])
        # logging.debug("sql {}".format(self.sql))
        break
    return sq

def more(**kwargs):
    sq = SQ()
    for k in kwargs:
        if isinstance(kwargs[k], int):
            sq.sql = "{}>{}".format(k,kwargs[k])
        else:
            sq.sql = "{}>'{}'".format(k,kwargs[k])
        # logging.debug("sql {}".format(self.sql))
        break
    return sq

def less(**kwargs):
    sq = SQ()
    for k in kwargs:
        if isinstance(kwargs[k], int):
            sq.sql = "{}<{}".format(k,kwargs[k])
        else:
            sq.sql = "{}<'{}'".format(k,kwargs[k])
        # logging.debug("sql {}".format(self.sql))
        break
    return sq

class SQ(object):
    def __init__(self):
        self.sql = ""    

    def or_eq(self, **kwargs):
        return self._opt("or","=", **kwargs)
    
    def and_eq(self, **kwargs):
        return self._opt("and","=", **kwargs)

    def or_neq(self, **kwargs):
        return self._opt("or","<>", **kwargs)

    def and_neq(self, **kwargs):
        return self._opt("and","<>", **kwargs)

    def and_more(self, **kwargs):
        return self._opt("and",">", **kwargs)

    def or_more(self, **kwargs):
        return self._opt("or",">", **kwargs)
 
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
    
    def And(self, search_query_obj):
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        # logging.debug("sql {}".format(self.sql))
        return self
        
    def Or(self, search_query_obj):
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        # logging.debug("sql {}".format(self.sql))
        return self

    @property
    def wrap(self):
        self.sql = "({})".format(self.sql)
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


class OneToMany(object):
    def __init__(self,parent_obj, child_class, bind_key):
        self.child_class = child_class
        self.bind_key = bind_key
        self.parent_obj = parent_obj

    def _generate(self):
        parent_key_val = self.parent_obj.__dict__[self.bind_key[0]]
        if not isinstance(parent_key_val, int):
            parent_key_val = "'{}'".format(parent_key_val)

        child_bind_key = self.bind_key[1]
        child_class = self.child_class

        input_map = {}
        input_map[child_bind_key] = parent_key_val
        return eq(**input_map).wrap

    def where(self, search_obj):
        pre_exec = self.child_class.where(self._generate().And(search_obj)) 
        # logging.debug("sql {}".format(sql))
        return pre_exec
    
    def exec(self):
        pre_exec = self.child_class.where(self._generate()) 
        # logging.debug("sql {}".format(sql))
        return pre_exec.exec()
    

class ManyToOne(object):
    def __init__(self, child_obj, parent_class, bind_key):
        self.parent_class = parent_class
        self.bind_key = bind_key
        self.child_obj = child_obj

    def exec(self):
        bind_key_val = self.child_obj.__dict__[self.bind_key[0]]
        if not isinstance(bind_key_val, int):
            bind_key_val = "'{}'".format(bind_key_val)

        bind_parent_key = self.bind_key[1]
        parent = self.parent_class
        return parent.query_where("{}={}".format(bind_parent_key, bind_key_val)).exec()
