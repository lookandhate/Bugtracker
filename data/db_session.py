import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

import logging

SqlAlchemyBase = dec.declarative_base()

__factory = None

#logging.basicConfig(filename=f'{__name__}.log', format='%(levelname)s:%(module)s:%(asctime)s; %(message)s',
                    #level=logging.INFO)


def global_init(db_file):
    global __factory

#    logger = logging.getLogger('[DB_SESSION, GLOBAL INIT]')

    if __factory:
        #logger.info('Factory exist, return')
        return

    if not db_file or not db_file.strip():
        #logger.error('No database file')
        raise Exception("No database file")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    logging.info(f"connecting to database on address{conn_str}")
    print(f"connecting to database on address{conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
