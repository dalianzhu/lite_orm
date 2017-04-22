from test.user import USER
from my_models.model import SQ

if __name__=="__main__":
    USER.where(
        SQ.eq(id=523).or_less(id=456)
        .and_merge(
            SQ.more(created_time='2009 09 09')
            )
            ).order_by_asc("id").limit(9).exec()

    USER.query_where("id=123 and created_time>'2009 09 09'").order_by_asc("id").limit(9).exec()