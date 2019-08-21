from model import Model, OneToMany, ManyToOne


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