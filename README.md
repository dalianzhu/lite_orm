# 限制

这是仅仅是一个数据库辅助类，它的功能特别的简单。

- 仅支持最新的python3 asyncio `async/await`语法。使用 aiomysql，需要先安装。`pip3 install aiomysql`
- 默认主键字段`id`。最好配置自增。否则请使用`set_primary("my_id")`设置自己的id字段。这是全局设置，如果所有的表各有各的主键字段，本工具将不太好用。
- 表名 与 模型类名 必须对应。模型类必须继承`Model`
- `表列名`与`类字段名`必须对应。

比如：

如果有表如下：

```sql
CREATE TABLE `t_filter_rules` ( 
    `id` bigint(20) NOT NULL AUTO_INCREMENT, 
    `business` varchar(128) NOT NULL COMMENT '业务类型', 
    `attr_id` int(11) NOT NULL DEFAULT '0', 
    `create_time` datetime NOT NULL COMMENT '创建时间', 
    `enable` tinyint(1) NOT NULL DEFAULT '0', 
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8 COMMENT='规则表'
```

则需要创建一个类，并继承orm.Model

类字段名与表列名相同

```python
class t_filter_rules(Model):
    def _init_(self):
        self.id = 0
        self.business = ""
        self.attr_id = 0
        self.create_time = datetime.datetime.now()
        self.enable = 0
```

# 简单使用

把orm.py**复制到你的项目中**，没做成pip安装方式，方便用户魔改和debug

## 创建数据库连接

```python
from orm import eq, more, execute, first_or_none, in_it
from orm import set_globle_db, Model

loop = asyncio.get_event_loop()
db = await aiomysql.create_pool(host=mysql_host, 
                                port=mysql_port,
                                user=mysql_user,
                                password=mysql_password,
                                db=database,
                                loop=loop,
                                charset=db_charset,
                                autocommit=True)

# 将默认的db设置为创建好的db连接对象
set_global_db(db)
```

## 查询

返回一条数据或None

```python
rule = first_or_none(await t_filter_rules.where(eq(attr_id=item.attr_id)).run())
```

查询返回数据列表
where 内的查询条件可连接

```python
rule = await t_filter_rules.where(eq(attr_id=attr_id)).run() # 返回 [rule1 rule2 ...]

rules = await t_filter_rules.where(eq(id=1).and_eq(attr_id=123)).run() # 返回 [rule1...]

rules = await t_filter_rules.where(in_it(attr_id=[1,2,3,4])).run() # 返回 [rule1...]
```

### 查询left join(right join同理)

新建新的join结果类用来接收条件结果

```
class t_attr_join(Model):
    def __init__(self):
        self.id = 0
        self.attr_id = 0
        self.tag = 0
```

```python
attr_lines = await t_filter_rules.left_join( # 标注执行left join
    t_attr_tag, "t_filter_rules.attr_id=t_attr_tag.attr_id").where( # on里面写相关的条件
    in_it(t_filter_rules__attr_id=attr_id_list)).run( #  双下划线 __ 代表. 这里传入where条件的是 t_filter_rules.attr_id
        target_class=t_attr_join) # 显式的标记返回的结果类型
```

## 插入新行

```python
new_rule = t_filter_rules()
new_rule.business = "tcs"
new_rule.attr_id = 123
new_rule.create_time = datetime.datetime.now()
new_rule.enable = 1
await new_rule.save() # 如果id配置为自增，此时id会自动递增
```

## 修改删除

修改内容要求模型类*必须包含id主键*

```python
rule = first_or_none(await t_filter_rules.where(eq(attr_id=item.attr_id)).run())
if rule:
    rule.enable = 1
    # 修改
    await rule.update()

    # 删除这一行
    # await rule.delete()
```
