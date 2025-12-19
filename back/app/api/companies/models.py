from sqlalchemy import Text, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from app.api.dao.database import Base

class Company(Base):
    __tablename__ = 'companies'
    external_id: Mapped[int] #Column(String, primary_key = True)
    name: Mapped[str] = mapped_column(nullable=False) #Column(String(255), nullable = False)
    is_it_company: Mapped[bool] # = Column(Boolean)
    industries: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String))) # = Column(JSON)
    region: Mapped[str] # = Column(String(100))
    tech_stack: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String))) # = Column(JSON)
    description: Mapped[str] = mapped_column(Text, nullable=True) # Column(Text)
    site_url: Mapped[str] # = Column(String(500))

    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="company", passive_deletes=True)
    emails: Mapped[list["Email"]] = relationship(back_populates="company", passive_deletes=True)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
