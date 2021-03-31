import sqlalchemy as sa
#функциональность orm
import sqlalchemy.orm as orm
#  соединение с базой данных
from sqlalchemy.orm import Session
# объявление БД
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

# получение сессий подключения к нашей базе данных
__factory = None

def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # строка подключения - тип БД, адрес до БД, многопоточное
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    # функция create_engine() -
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()