from sqlalchemy import create_engine, text
engine = create_engine("postgresql://admin:password@localhost:5432/partner_finder")
with engine.connect() as conn:
    conn.execute(text("DELETE FROM emails"))
    conn.commit()
print("База писем очищена.")

# ВРЕМЕННЫЙ СКРИПТ, ОН НЕ БУДЕТ ПОТОМ ИСПОЛЬЗОВАТЬСЯ