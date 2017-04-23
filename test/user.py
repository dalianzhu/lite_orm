from my_models.model import Model, OneToMany, ManyToOne


class USER(Model):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.age = 0
        self.is_admin = 0
        self.created_time = ""
        self.child_article = OneToMany(self, ARTICLE, ["id", "uid"])

class ARTICLE(Model):
    def __init__(self):
        self.id = 0
        self.article_name = ""
        self.uid = 0
        self.article_pages = 0
        self.parent_user = ManyToOne(self, USER, ["uid", "id"])