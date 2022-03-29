from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import re_bf
import os


engine = create_engine(os.environ["DATABASE_URL"])
Base = declarative_base()
session = sessionmaker(bind=engine)()


class User(Base):
    __tablename__ = 'weebtable'
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, unique=True)
    date = Column(DateTime)
    sub_state = Column(Boolean)

    def __repr__(self):
        return f'{self.user_id}, {self.sub_state}'


class Chapter(Base):
    __tablename__ = 'chapter_id'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title_id = Column(String)
    chapter_name = Column(String)
    last_chapter = Column(Float)

    def __repr__(self):
        return f'{self.user_id}'


class Control:
    def __init__(self):
        Base.metadata.create_all(engine)


# Есть ли юзер в базе если нет добавить в базу
def if_user_in_db(user_id):
    if session.query(User).filter_by(user_id=user_id).first():
        return True
    else:
        request = User(user_id=user_id, date=datetime.now(), sub_state=False)   # INSERT in sql
        session.add(request)
        session.commit()
        return False


# Подписан ли юзер саб стейт == 1?
def if_sub_user(user_id):
    response = session.query(User.sub_state).filter_by(user_id=user_id).first()
    if response is not None:
        if response[0]:
            return True
        else:
            return False
    else:
        return False


# Есть ли тайтл ид в подписках
def if_url_in_db(user_id, title_id):
    response = session.query(Chapter.title_id).filter_by(user_id=user_id).all()    #SELECT
    response = [_[0] for _ in response]
    if title_id in response:
        return True
    else:
        return False


# Вновь включение подписки саб стейт = 1
def set_sub_state_on(user_id):
    response = session.query(User).filter_by(user_id=user_id).first()
    response.sub_state = True  #UPDATE
    session.commit()
    return "Вы снова будете получать уведомления!"


# подписка юзера в начале идет проверка гет запросом, затем подписан ли юзер на эту мангу, а затем подписка
def subscribe_user(user_id, title_id):
    try:
        c_chapter, chapter_name = re_bf.check(title_id)
    except:
        return "Подписаться не получилось проверьте правильность TitleID!!!"
    if not if_sub_user(user_id):
        response = session.query(User).filter_by(user_id=user_id).first()
        response.sub_state = True
    response_chapter = Chapter(user_id=user_id, chapter_name=chapter_name, title_id=title_id, last_chapter=c_chapter)
    session.add(response_chapter)
    session.commit()
    return 'Вы успешно подписались!'


# Удаляется манга из отслеживания по юзер ид и тайтл ид
def delete_sub(user_id, title_id):
    response = session.query(Chapter).filter_by(user_id=user_id, title_id=title_id).first()
    session.delete(response)
    session.commit()
    return 'Вы успешно отписались!'


# Отписка юзера саб стейт = 0
def unsubscribe(user_id):
    response = session.query(User).filter_by(user_id=user_id).first()
    response.sub_state = False
    session.commit()
    return 'Вы успешно отписались от всех россылок!!'


# Выдает список из сабов (юзеры у которых саб стейт == 1)
def get_all_subs():
    response = session.query(User.user_id).filter_by(sub_state=True).all()
    response = [i[0] for i in response]
    return response


# Возвращает словарь title_id: last_chapter
def get_all_url_chapter(user_id):
    response = session.query(Chapter.title_id, Chapter.last_chapter).filter_by(user_id=user_id).all()
    r = {}
    for title_id, last_chapter in response:
        r[title_id] = last_chapter
    return r


# Установка новой главы манги
def set_new_chapter(user_id, current_chapter, title_id):
    response = session.query(Chapter).filter_by(user_id=user_id, title_id=title_id).first()
    response.last_chapter = current_chapter
    session.commit()


# Есть у юзера хоть 1 манга в отслеж
def if_user_have_manga(user_id):
    response = session.query(Chapter.title_id).filter_by(user_id=user_id).all()
    response = [i[0] for i in response]
    if len(response) > 0:
        return True
    return False


# Возвращает все подписки юзера
def check(user_id):
    response = session.query(Chapter.chapter_name, Chapter.last_chapter).filter_by(user_id=user_id).all()
    return response
