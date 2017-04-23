# coding:utf-8
from test.user import USER, ARTICLE
from my_models.model import SQ, eq, more, less, Exec, first_or_none
import logging

def test_case_1():
    def run(self):
        return self.sql, self.values
    Exec.run = run

    user = USER()
    user.id = 123
    user.age = 26
    user.name = "yzh"

    sql = user.child_article.run()
    logging.debug("testcase1 sql {}".format(sql))
    assert sql[0]=='select * from ARTICLE where (uid=%s)'
    assert sql[1]==[123]

    sql = user.child_article.where(eq(id=1)).run()
    logging.debug("testcase1 where_sql_1 {}".format(sql))
    assert sql[0]=='select * from ARTICLE where (uid=%s) and (id=%s)'
    assert sql[1]== [123, 1]
    
def test_case_2():
    article = ARTICLE()
    article.id = 9000
    article.uid = 123
    article.article_name = "good book"

    sql = article.parent_user.run()
    logging.debug("test_case_2 exec_sql {}".format(sql))
    assert sql[0]=='select * from USER where id=%s'
    assert sql[1]== [123]

def test_case_3():
    sql = USER.where(
        more(age=10).and_less(age=30)
        ).run()
    logging.debug("test_case_3 sql {}".format(sql))
    assert sql[0]=='select * from USER where age>%s and age<%s'
    assert sql[1]== [10, 30]

    sql = USER.where(
        less(age=10).or_more(age=30).wrap.and_eq(is_admin=1)
        ).run()

    logging.debug("test_case_3 sql {}".format(sql))
    assert sql[0]=='select * from USER where (age<%s or age>%s) and is_admin=%s'
    assert sql[1]== [10, 30, 1]

def test_case_4():
    article = ARTICLE()
    article.id = 9000
    article.uid = 123
    article.article_name = "good book"
    article.article_pages = 99

    sql = article.save()
    logging.debug("test_case_4 sql {}".format(sql))
    assert sql[0]=='insert into ARTICLE(article_name,article_pages,id,uid) values(%s,%s,%s,%s)'
    assert sql[1]== ['good book', 99, 9000, 123]


def test_case_5():
    # test update
    article = ARTICLE()
    article.id = 9000
    # article.uid = 123
    article.article_name = "good book"
    article.article_pages = 199

    sql = article.update()
    logging.debug("test_case_5 sql {}".format(sql))
    assert sql[0]=="update ARTICLE set article_name=%s,article_pages=%s where id=%s)"
    assert sql[1]==  ['good book', 199,9000]

def test_case_6():
    # test inject
    sql = USER.where(eq(id=1).Or(eq(id=5).or_eq(id=6))).run()
    logging.debug("test_case_6 sql {}".format(sql))

def test_case_7():
    # 这个用例需要先插入两条数据
    # user = USER()
    # user.id = 0
    # user.age = 26
    # user.name = "yzh"
    # user.is_admin = 1
    # user.save()
    # article = ARTICLE()
    # article.article_name = "gone with the wind"
    # article.article_pages = 288
    # article.uid = 124
    # article.save()

    # user = first_or_none(USER.where(eq(id=124)).run())
    # logging.debug("test_case_7 user {}".format(user.__dict__))

    # article = first_or_none(user.child_article.where(eq(id=1)).run()) 
    # logging.debug("test_case_7 article {}".format(article.__dict__))

    # parent_user = first_or_none(article.parent_user.run())
    # logging.debug("test_case_7 parent_user {}".format(parent_user.__dict__))

    # parent_user.is_admin = 1
    # parent_user.update()


test_cases = [
    # test_case_1,
    # test_case_2,
    # test_case_3,
    # test_case_4,
    # test_case_5,
    # test_case_6,
    test_case_7,
]