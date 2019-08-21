import asyncio
import logging

import aiomysql

from model import eq, more, execute, first_or_none
from model import set_globle_db
from test.user import User, Article


async def init():
    """
create table User(
    id bigint(20) not null primary key auto_increment,
    name varchar(64)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;

create table Article(
    id bigint(20) not null primary key auto_increment,
    uid bigint(20),
    article_name varchar(32) not null default ''
    )ENGINE=InnoDB DEFAULT CHARSET=utf8;

    """

    loop = asyncio.get_event_loop()
    db = await aiomysql.create_pool(host="127.0.0.1",
                                    port=3306,
                                    user="root",
                                    password="123456",
                                    db="test",
                                    loop=loop,
                                    charset="utf8",
                                    autocommit=True)
    set_globle_db(db)
    await execute("delete from User;", [])
    await execute("delete from Article;", [])

    u1 = User()
    u1.name = "superpig"
    uid = await u1.save()

    u2 = User()
    u2.name = "bigpig"
    await u2.save()

    a1 = Article()
    a1.uid = uid
    a1.article_name = "文章名1"
    await a1.save()

    a2 = Article()
    a2.uid = uid
    a2.article_name = "文章名2"
    await a2.save()


async def test_case_1():
    """
    测试关系
    :return:
    """
    user = await User.where(eq(name="superpig")).run()
    user = first_or_none(user)

    ret = await user.child_article.run()
    logging.debug("testcase1 sql {}".format(ret))

    assert ret[0].article_name == "文章名1"
    assert ret[1].article_name == "文章名2"

    article = await Article.where(eq(article_name="文章名1")).run()
    article = first_or_none(article)
    user = await article.parent_user.run()
    user = first_or_none(user)
    assert user.name == "superpig"


async def test_case_2():
    """
    测试查找
    :return:
    """
    user1 = await User.where(eq(name="superpig")).run()
    user1 = first_or_none(user1)
    logging.debug("user1 {}".format(user1))

    find = False
    user_all = await User.get_all().run()
    for user in user_all:
        if user.name == "superpig":
            find = True
    assert find == True

    assert len(user_all) == 2

    articles = await Article.where(more(id=0)).run()
    for article in articles:
        logging.debug("article {}".format(article.__dict__))
    assert len(articles) == 2
    assert articles[0].uid == user1.id


async def test_case_3():
    """
    测试join
    :return:
    """

    class Merge():
        def __init__(self):
            self.id = ""
            self.name = ""

            self.Article__id = ""  # 因为Article的id和User中的重复了，所以使用 表__字段 的方式表示
            self.uid = ""
            self.article_name = ""

    ret = await User.left_join('Article', "User.id=Article.uid").run(Merge)
    for item in ret:
        logging.debug("test join {}".format(item.__dict__))
    assert len(ret) == 3

    user = await User.where(eq(name="superpig")).run()
    user = first_or_none(user)

    ret = await User.left_join('Article', "User.id=Article.uid") \
        .where(more(Article__id=1)
               .and_eq(name="superpig")).run(Merge)
    for item in ret:
        logging.debug("test join {}".format(item.__dict__))
    m = first_or_none(ret)
    assert m.name == user.name

test_cases = [
    test_case_1,
    test_case_2,
    test_case_3,
]
