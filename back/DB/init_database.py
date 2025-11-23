from sqlalchemy import create_engine
from models import Base

def init_database():
    engine = create_engine('postgresql://admin:password@localhost:5432/partner_finder')
    Base.metadata.create_all(bind = engine)
    print("Таблицы созданы успешно")

if __name__ == "__main__":
    init_database()