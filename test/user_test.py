from test.user import USER, ARTICLE
from my_models.model import SQ, eq, more, less, Exec
import logging

def test_case_1():
    def exec(self):
        return self.sql
    
    Exec.exec = exec

    user = USER()
    user.id = 123
    user.age = 26
    user.name = "yzh"

    sql = user.child_article.exec()
    logging.debug("testcase1 sql {}".format(sql))
    assert sql=="select * from ARTICLE where (uid=123)"
  
    sql = user.child_article.where(eq(id=1)).exec()
    logging.debug("testcase1 where_sql_1 {}".format(sql))
    assert sql == "select * from ARTICLE where (uid=123) and (id=1)"

    
def test_case_2():
    article = ARTICLE()
    article.id = 9000
    article.uid = 123
    article.article_name = "good book"

    def exec(self):
        return self.sql
    Exec.exec = exec

    exec_sql = article.parent_user.exec()
    logging.debug("test_case_2 exec_sql {}".format(exec_sql))
    assert exec_sql == 'select * from USER where id=123'

def test_case_3():
    def exec(self):
        return self.sql
    Exec.exec = exec

    sql = USER.where(
        more(age=10).and_less(age=30)
        ).exec()
    logging.debug("test_case_3 sql {}".format(sql))
    assert sql == "select * from USER where age>10 and age<30"

    sql = USER.where(
        less(age=10).or_more(age=30).wrap.and_eq(is_admin=1)
        ).exec()

    logging.debug("test_case_3 sql {}".format(sql))
    assert sql == "select * from USER where (age<10 or age>30) and is_admin=1"

def test_case_4():
    def exec(self):
        return self.sql
    Exec.exec = exec

    article = ARTICLE()
    article.id = 9000
    article.uid = 123
    article.article_name = "good book"
    article.article_pages = 99

    sql = article.save()
    logging.debug("test_case_4 sql {}".format(sql))
    assert sql == "insert into ARTICLE(id,article_name,uid,article_pages) values(9000,'good book',123,99)"

def test_case_5():
    def exec(self):
        return self.sql
    Exec.exec = exec

    # test update
    article = ARTICLE()
    article.id = 9000
    # article.uid = 123
    article.article_name = "good book"
    article.article_pages = 199

    sql = article.update()
    logging.debug("test_case_5 sql {}".format(sql))

test_cases = [
    test_case_1,
    test_case_2,
    test_case_3,
    test_case_4,
    test_case_5,
]