import logging
import aiomysql
db = None
"""
db可以需要这么初始化，loop = asyncio.get_event_loop()
db = await aiomysql.create_pool(host=srvconf.mysql_host, 
                                port=srvconf.mysql_port,
                                user=srvconf.mysql_user,
                                password=srvconf.mysql_password,
                                db=srvconf.database, 
                                loop=loop, 
                                charset='utf8', autocommit=True)
"""

def first_or_none(objs):
    if objs:
        return objs[0]
    return None


class Model(object):
    def __init__(self):
        pass

    async def save(self):
        """
        insert into 表名(id,name) values(0,'XX')
        """
        table_name = self.__class__.__name__
        table_property = self.__dict__.items()

        sql = "insert into {table_name}({names}) values({values})"
        names = ""
        values = ""
        true_values = []
        for name, val in table_property:
            if isinstance(val, OneToMany) or isinstance(val, ManyToOne):
                continue

            if val == None:
                continue
            names += name + ","
            values += "%s" + ","
            true_values.append(val)

        names = names[:-1]
        values = values[:-1]

        pre_exec = PreExec()
        pre_exec.sql = sql.format(table_name=table_name, names=names, values=values)
        pre_exec.values = true_values

        # logging.debug("sql {}".format(sql))
        return await pre_exec.run()

    async def update(self):
        """
        update 表名 set id=1, name="haha" where id=1
        """
        table_name = self.__class__.__name__
        table_property = self.__dict__.items()

        sql = "update {table_name} set {query} where id={id}"
        names = []
        values = []
        true_values = []
        for name, val in table_property:
            if isinstance(val, OneToMany) or isinstance(val, ManyToOne):
                continue
            if name == "id":
                continue
            if val == None:
                continue

            names.append(name)
            values.append("%s")
            true_values.append(val)

        query = ""
        for i in range(0, len(names)):
            query += "{}={},".format(names[i], values[i])
        query = query[:-1]

        pre_exec = PreExec()
        pre_exec.sql = sql.format(table_name=table_name, query=query, id="%s")
        true_values.append(self.id)
        pre_exec.values = true_values
        # logging.debug("sql {}".format(sql))
        return await pre_exec.run()

    async def delete(self):
        """
        update 表名 set id=1, name="haha" where id=1
        """
        if self.id:
            table_name = self.__class__.__name__
            table_property = self.__dict__.items()

            sql = "delete from {table_name} where id=%s"
            true_values = []

            pre_exec = PreExec()
            true_values.append(self.id)
            pre_exec.values = true_values
            pre_exec.sql = sql.format(table_name=table_name)
            # logging.debug("sql {}".format(sql))
            return await pre_exec.run()
        else:
            return None

    @classmethod
    def get_all(cls):
        sql = "select * from {table_name}"
        table_name = cls.__name__

        sql = sql.format(table_name=table_name)
        # logging.debug("sql {}".format(sql))
        pre_exec = PreExec()
        pre_exec.sql = sql
        pre_exec.target_class = cls
        return pre_exec

    @classmethod
    def get_count(cls, search_obj=None):
        pre_exec = PreExec()
        table_name = cls.__name__

        if search_obj:
            sql = "select count(id) from {table_name} where {query}"
            query = search_obj.sql
            sql = sql.format(table_name=table_name, query=query)
            pre_exec.values = search_obj.values
        else:
            sql = "select count(id) from {table_name}"
            sql = sql.format(table_name=table_name)

        # logging.debug("sql {}".format(sql))
        pre_exec.sql = sql
        pre_exec.target_class = cls
        return pre_exec

    @classmethod
    def where(cls, search_obj, only_get=[]):
        sql = "select * from {table_name} where {query}"
        if only_get:
            only_get = ",".join(only_get)
            sql = 'select '+only_get+" from {table_name} where {query}"

        table_name = cls.__name__

        query = search_obj.sql
        sql = sql.format(table_name=table_name, query=query)
        # logging.debug("sql {}".format(sql))
        pre_exec = PreExec()
        pre_exec.sql = sql
        pre_exec.values = search_obj.values
        pre_exec.target_class = cls
        return pre_exec


def _opt(opt, kwargs):
    sql = ""
    values = []
    for k in kwargs:
        val = kwargs[k]
        values.append(val)
        sql = "{}{}{}".format(k, opt, "%s")
    return sql, values


def eq(**kwargs):
    sq = SQ()
    sq.sql, sq.values = _opt("=", kwargs)
    return sq


def neq(**kwargs):
    sq = SQ()
    sq.sql, sq.values = _opt("<>", kwargs)
    return sq


def more(**kwargs):
    sq = SQ()
    sq.sql, sq.values = _opt(">", kwargs)
    return sq


def less(**kwargs):
    sq = SQ()
    sq.sql, sq.values = _opt("<", kwargs)
    return sq


def in_it(**kwargs):
    sq = SQ()
    for k in kwargs:
        val_arr = kwargs[k]
        mask_arr = ['%s' for var in val_arr]
        mask_arr_str = ",".join(mask_arr)
        mask_arr_str = "({})".format(mask_arr_str)
        sq.sql = "{} in {}".format(k, mask_arr_str)
        sq.values.extend(val_arr)
    return sq


class SQ(object):
    def __init__(self):
        self.sql = ""
        self.values = []

    def or_eq(self, **kwargs):
        return self._opt("or", "=", **kwargs)

    def and_eq(self, **kwargs):
        return self._opt("and", "=", **kwargs)

    def or_neq(self, **kwargs):
        return self._opt("or", "<>", **kwargs)

    def and_neq(self, **kwargs):
        return self._opt("and", "<>", **kwargs)

    def and_more(self, **kwargs):
        return self._opt("and", ">", **kwargs)

    def or_more(self, **kwargs):
        return self._opt("or", ">", **kwargs)

    def or_less(self, **kwargs):
        return self._opt("or", "<", **kwargs)

    def and_less(self, **kwargs):
        return self._opt("and", "<", **kwargs)

    def _opt(self, relation, op, **kwargs):
        for k in kwargs:
            val = kwargs[k]
            self.values.append(val)
            self.sql += " {} {}{}{}".format(relation, k, op, "%s")
            # logging.debug("sql {}".format(self.sql))
            break
        return self

    def and_in(self, **kwargs):
        for k in kwargs:
            val_arr = kwargs[k]
            mask_arr = ['%s' for var in val_arr]
            mask_arr_str = ",".join(mask_arr)
            mask_arr_str = "({})".format(mask_arr_str)
            self.sql += " and {} in {}".format(k, mask_arr_str)
            self.values.extend(val_arr)
            return self

    def or_in(self, **kwargs):
        for k in kwargs:
            val_arr = kwargs[k]
            mask_arr = ['%s' for var in val_arr]
            mask_arr_str = ",".join(mask_arr)
            mask_arr_str = "({})".format(mask_arr_str)
            self.sql += " or {} in {}".format(k, mask_arr_str)
            self.values.extend(val_arr)
            return self

    def And(self, search_query_obj):
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        self.values += search_query_obj.values
        # logging.debug("sql {}".format(self.sql))
        return self

    def Or(self, search_query_obj):
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        self.values += search_query_obj.values
        # logging.debug("sql {}".format(self.sql))
        return self

    @property
    def wrap(self):
        self.sql = "({})".format(self.sql)
        # logging.debug("sql {}".format(self.sql))
        return self


class PreExec(object):
    def __init__(self):
        self.sql = ""
        self.values = []
        self.target_class = None

    def order_by_desc(self, col_name):
        if 'order by' not in self.sql:
            self.sql += " order by {} desc".format(col_name)
        else:
            self.sql += ",{} desc".format(col_name)
        return self

    def order_by_asc(self, col_name):
        if 'order by' not in self.sql:
            self.sql += " order by {} asc".format(col_name)
        else:
            self.sql += ",{} asc".format(col_name)
        return self

    def limit(self, *nums):
        query = ""
        for item in nums:
            query += str(item) + ","
        query = query[:-1]
        self.sql += " limit {}".format(query)
        return self

    async def run(self):
        exec_obj = Exec()
        exec_obj.sql = self.sql
        exec_obj.values = self.values
        exec_obj.target_class = self.target_class
        return await exec_obj.run()


class Exec(object):
    def __init__(self):
        self.sql = ""
        self.values = []
        self.target_class = None

    async def run(self):
        logging.debug("exec sql {} {}".format(self.sql, self.values))
        if "insert" in self.sql:
            async with db.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(self.sql, self.values)
                    await conn.commit()
                    ret = cur.lastrowid
                    return ret
        elif 'count(id)' in self.sql:
            async with db.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    ret = await cur.execute(self.sql, self.values)
                    r = await cur.fetchall()
                    return r[0]['count(id)']
        elif "select" in self.sql:
            async with db.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    if self.values:
                        ret = await cur.execute(self.sql, self.values)
                    else:
                        ret = await cur.execute(self.sql)
                    r = await cur.fetchall()
            obj_list = []
            for dbdata in r:
                obj = self.target_class()
                for dbdata_key in dbdata:
                    obj.__dict__[dbdata_key] = dbdata[dbdata_key]
                obj_list.append(obj)
            return obj_list
        elif 'update' in self.sql:
            async with db.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(self.sql, self.values)
                    ret = await conn.commit()
                    return ret
        else:
            async with db.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(self.sql, self.values)
                    ret = await conn.commit()
                    return ret


class OneToMany(object):
    def __init__(self, parent_obj, child_class, bind_key):
        self.child_class = child_class
        self.bind_key = bind_key
        self.parent_obj = parent_obj

    def _generate(self):
        parent_key_val = self.parent_obj.__dict__[self.bind_key[0]]

        child_bind_key = self.bind_key[1]
        child_class = self.child_class

        input_map = {}
        input_map[child_bind_key] = parent_key_val
        return eq(**input_map).wrap

    def where(self, search_obj):
        pre_exec = self.child_class.where(self._generate().And(search_obj))
        # logging.debug("sql {}".format(sql))
        return pre_exec

    def run(self):
        pre_exec = self.child_class.where(self._generate())
        # logging.debug("sql {}".format(sql))
        return pre_exec.run()


class ManyToOne(object):
    def __init__(self, child_obj, parent_class, bind_key):
        self.parent_class = parent_class
        self.bind_key = bind_key
        self.child_obj = child_obj

    def run(self):
        bind_key_val = self.child_obj.__dict__[self.bind_key[0]]

        bind_parent_key = self.bind_key[1]
        parent = self.parent_class
        input_map = {}
        input_map[bind_parent_key] = bind_key_val
        return parent.where(eq(**input_map)).run()
