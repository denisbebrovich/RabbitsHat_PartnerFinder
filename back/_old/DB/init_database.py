from sqlalchemy import create_engine, text
from DB.models import Base

def init_database(db_url):
    engine = create_engine(db_url)
    
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("Все таблицы созданы успешно!")

if __name__ == "__main__":
    init_database()