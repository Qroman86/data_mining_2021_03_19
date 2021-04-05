from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models


table_mapper = {
    "post_data": models.Post,
    "author_data": models.Author,
}


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def _get_or_create(self, session, model, uniq_field, uniq_value, **data):
        db_instance = session.query(model).filter(uniq_field == uniq_value).first()
        if not db_instance:
            db_instance = model(**data)
            session.add(db_instance)
            try:
                session.commit()
            except Exception as exc:
                print(exc)
                session.rollback()
        return db_instance

    def _get_or_create_comment_list(self, session, data: list) -> list:
        result = []
        if data:
            for comment in data:
                comment_author = self._get_or_create(
                    session,
                    models.Author,
                    models.Author.url,
                    comment["comment"]["user"]["url"],
                    name=comment["comment"]["user"]["full_name"],
                    url=comment["comment"]["user"]["url"],
                )
                db_comment = self._get_or_create(
                    session,
                    models.Comment,
                    models.Comment.id,
                    comment["comment"]["id"],
                    **comment["comment"],
                    author=comment_author,
                )

                result.append(db_comment)
                result.extend(
                    self._get_or_create_comment_list(session, comment["comment"]["children"])
                )

        return result


    def create_post(self, data):
        session = self.maker()
        post = None

        author = self._get_or_create(
            session,
            models.Author,
            models.Author.url,
            data["author_data"]["url"],
            **data["author_data"],
        )

        post = self._get_or_create(
            session,
            models.Post,
            models.Post.id,
            data["post_data"]["id"],
            author=author,
            **data["post_data"],
        )

        post.tags.extend(
            [
                self._get_or_create(session, models.Tag, models.Tag.url, tag_data["url"], **tag_data)
                for tag_data in data["tags_data"]
            ]
        )

        post.comments.extend(
            self._get_or_create_comment_list(session, data["comments_data"])
        )
        try:
            session.add(post)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
        print(1)