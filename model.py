# coding:utf-8
import datetime
import logging

import aiomysql

db = None

primary = 'id'


def set_globle_db(input_db):
    global db
    db = input_db


def set_primary(key):
    global primary
    primary = key


"""
哈哈哈，这是一个很简单的orm。我花了大概一个上午把它写出来，只为了不再写讨厌的sql。
它使用了大量的字符串拼接，有人会说这性能很差，但这是python，性能能差到哪去呢。
使用指南：
1. 首先，你需要在某个地方初始化公用的db对象。就像这样。
import orm
db = await aiomysql.create_pool(host=srvconf.mysql_host, 
                                port=srvconf.mysql_port,
                                user=srvconf.mysql_user,
                                password=srvconf.mysql_password,
                                db=srvconf.database,
                                loop=loop,
                                charset=db_charset,
                                autocommit=True)
orm.set_global_db(db)
                                
2. 然后，确保对应的数据库中有表，比如创建两个表：
create table User(
    id bigint(20) not null primary key auto_increment,
    name bigint(20)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;
    
create table Article(
    id bigint(20) not null primary key auto_increment,
    uid bigint(20),
    article_name varchar(32) not null default ''
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;

3. 最后，创建对应的实体，并继承orm.Model。
确保类名就是表名，类的属性就是表的列。确实很简单，不是吗。
class User(Model):
        def __init__(self):
            self.id = 0
            self.name = ""
            self.child_article = OneToMany(self, Article, ["id", "uid"])

class Article(Model):
    def __init__(self):
        self.id = 0
        self.article_name = ""
        self.uid = 0
        self.parent_user = ManyToOne(self, User, ["uid", "id"])
        
然后，就是开心的玩了：
简单查询：
user = await User.where(eq(id=1).and_eq(name='yzh')).run() # 返回 [User...]
user_count = await User.get_count(eq(id=1)).run() # 返回 int

user = await User.where(more(id=1).and_eq(name='yzh')).run() # 返回 [User...]

where()中要放入SQ (search query)对象。提供了
eq, neq, less, more, in_it等几个初始SQ。它们可以链式调用，也能用 sqobj.And(sqobj2)
将多个SQ 对象链接起来。

插入:
表的id最好设置为自增。
user = User()
user.name = 'yzh'
await user.insert()

删除：
user = await User.where(eq(id=1)).run()
user = user[0]
await user.delete()
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

            if not isinstance(val, (int, str, datetime.datetime)):
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
        update 表名 set name="haha" where `primary`=1
        """
        table_name = self.__class__.__name__
        table_property = self.__dict__.items()

        sql = "update {table_name} set {query} where " + primary + "={id}"
        names = []
        values = []
        true_values = []
        for name, val in table_property:
            if isinstance(val, OneToMany) or isinstance(val, ManyToOne):
                continue
            if name == primary:
                continue
            if val == None:
                continue
            if not isinstance(val, (int, str, datetime.datetime)):
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
        true_values.append(self.__dict__[primary])
        pre_exec.values = true_values
        # logging.debug("sql {}".format(sql))
        return await pre_exec.run()

    async def delete(self):
        """
        update 表名 set name="haha" where `primary`=1
        """
        if self.__dict__[primary]:
            table_name = self.__class__.__name__
            table_property = self.__dict__.items()

            sql = "delete from {table_name} where " + primary + "=%s"
            true_values = []

            pre_exec = PreExec()
            true_values.append(self.__dict__[primary])
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
            sql = "select count(" + primary + ") from {table_name} where {query}"
            query = search_obj.sql
            sql = sql.format(table_name=table_name, query=query)
            pre_exec.values = search_obj.values
        else:
            sql = "select count(" + primary + ") from {table_name}"
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
            sql = 'select ' + only_get + " from {table_name} where {query}"

        table_name = cls.__name__

        query = search_obj.sql
        sql = sql.format(table_name=table_name, query=query)
        # logging.debug("sql {}".format(sql))
        pre_exec = PreExec()
        pre_exec.sql = sql
        pre_exec.values = search_obj.values
        pre_exec.target_class = cls
        return pre_exec

    @classmethod
    def left_join(cls, table, on):
        j = _joinObj()
        j.join_sql = " left join {} on {} ".format(table.__name__, on)
        j.main_table = cls.__name__
        return j

    @classmethod
    def right_join(cls, table, on):
        j = _joinObj()
        j.join_sql = " right join {} on {} ".format(table.__name__, on)
        j.main_table = cls.__name__
        return j


class _joinObj():
    def __init__(self):
        self.main_table = ""
        self.join_sql = ""

    def left_join(self, table, on):
        self.join_sql += " left join {table} on {on} ".format(table=table.__name__, on=on)
        return self

    def right_join(self, table, on):
        self.join_sql += " right join {table} on {on} ".format(table=table.__name__, on=on)
        return self

    def where(self, search_obj):
        sql = "select * from {main_table} {join_sql} where {where}" \
            .format(main_table=self.main_table,
                    join_sql=self.join_sql, where=search_obj.sql)

        pre_exec = PreExec()
        pre_exec.sql = sql
        pre_exec.target_class = None
        pre_exec.values = search_obj.values
        return pre_exec

    async def run(self, target_class):
        pre_exec = PreExec()
        pre_exec.sql = "select * from {main_table} {join_sql}" \
            .format(main_table=self.main_table,
                    join_sql=self.join_sql)
        pre_exec.target_class = target_class
        return await pre_exec.run()

    # select * from User left join Article on Article.uid=User.id


def _opt(opt, kwargs):
    # kwargs 是SearchQuery包装传入的参数，比如 ID=1
    # 但有时 more(ID=1) 代表的意思是 where ID>1
    # 所有需要按opt（操作）来决定返回的sql，就酱
    values = []
    k, val = next(iter(kwargs.items()))
    # 处理 join __
    k = k.replace("__", ".")
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
    k, val_arr = next(iter(kwargs.items()))
    # 处理 join __
    k = k.replace("__", ".")

    mask_arr = ['%s' for var in val_arr]
    mask_arr_str = ",".join(mask_arr)
    mask_arr_str = "({})".format(mask_arr_str)
    sq.sql = "{} in {}".format(k, mask_arr_str)
    sq.values.extend(val_arr)
    return sq


class SQ(object):
    # 传说中的search query对象。用在where()中。
    # 有eq, neq等几个初始方法。
    # 每调用一次self._opt都会在自身拼接一个“操作”
    # 这样就能很容易的使用
    # where(eq(ID=1).and_eq(Name='yzh')) 链式用法。
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
        k, val = next(iter(kwargs.items()))
        self.values.append(val)
        self.sql += " {} {}{}{}".format(relation, k, op, "%s")
        # logging.debug("sql {}".format(self.sql))
        return self

    def and_in(self, **kwargs):
        k, val_arr = next(iter(kwargs.items()))
        mask_arr = ['%s' for var in val_arr]
        mask_arr_str = ",".join(mask_arr)
        mask_arr_str = "({})".format(mask_arr_str)
        self.sql += " and {} in {}".format(k, mask_arr_str)
        self.values.extend(val_arr)
        return self

    def or_in(self, **kwargs):
        k, val_arr = next(iter(kwargs.items()))
        mask_arr = ['%s' for var in val_arr]
        mask_arr_str = ",".join(mask_arr)
        mask_arr_str = "({})".format(mask_arr_str)
        self.sql += " or {} in {}".format(k, mask_arr_str)
        self.values.extend(val_arr)
        return self

    def And(self, search_query_obj):
        # 无论何时，调用And都能将两个search query用and的方式拼在一起
        # 是不是很棒？
        # eq(ID=1).or_eq(Name='yzh').And(eq(Status='admin'))
        # 等同于 ID=1 or Name='yzh' and (status='admin')
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        self.values += search_query_obj.values
        # logging.debug("sql {}".format(self.sql))
        return self

    def Or(self, search_query_obj):
        # 类似And，只是这次用的是or 来连接两个search query
        self.sql = "{} and ({})".format(self.sql, search_query_obj.sql)
        self.values += search_query_obj.values
        # logging.debug("sql {}".format(self.sql))
        return self

    @property
    def wrap(self):
        # 把自己打个括号，建议少用。太复杂的orm不如直接使用query方法
        self.sql = "({})".format(self.sql)
        # logging.debug("sql {}".format(self.sql))
        return self


class PreExec(object):
    """
    在真正执行sql前，还需要插入几个操作，比如limit, order by之类的
    没有实现group by，因为这个句子会破坏orm映射实体。
    """

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

    async def run(self, target_class=None):
        exec_obj = Exec()
        exec_obj.sql = self.sql
        exec_obj.values = self.values
        if not target_class:
            exec_obj.target_class = self.target_class
        else:
            exec_obj.target_class = target_class
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
        elif 'count({})'.format(primary) in self.sql:
            async with db.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    ret = await cur.execute(self.sql, self.values)
                    r = await cur.fetchall()
                    return r[0]['count({})'.format(primary)]
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
                    # 处理join
                    class_key = dbdata_key
                    if "." in dbdata_key:
                        class_key = dbdata_key.replace(".", "__")

                    if class_key not in obj.__dict__:
                        continue
                    obj.__dict__[class_key] = dbdata[dbdata_key]
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
    """
    关系式数据库，当然需要有关系。这真的很复杂，我反正没在项目里用过。
    如上面的两个实体
    OneToMany(self, ARTICLE, ["id", "uid"]) 代表，一个User.id 对应多个Article.uid
    可以使用这样的句子查询：
    user = await User.where(eq(id=1)).run()|first_or_none
    articles = await user.child_article.run()
    """

    def __init__(self, parent_obj, child_class, bind_key):
        self.child_class = child_class
        self.bind_key = bind_key
        self.parent_obj = parent_obj

    def _generate(self):
        parent_key_val = self.parent_obj.__dict__[self.bind_key[0]]

        child_bind_key = self.bind_key[1]

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
    """
    就像上面：
    article = await Article.where(eq(id=1)).run()|first_or_none
    user = await article.parent_user.run()|first_or_none
    """

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


def get_conn():
    return db.acquire()


async def query(sql, conn=None):
    """
    当上面都不能解决你的需求，那返璞归真吧。没有什么是一个query不能解决的，
    如果还有，那就execute一下。
    你可以使用已用的conn，如果不传入，我们会给你创建一个。
    """
    logging.debug('orm query: sql {}'.format(sql))
    if not conn:
        async with db.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql)
                r = await cur.fetchall()
                return r
    else:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql)
            r = await cur.fetchall()
            return r


async def execute(sql, values):
    logging.debug('orm execute: sql {}'.format(sql))
    async with db.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, values)
            ret = await conn.commit()
            return ret
