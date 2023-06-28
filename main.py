from datetime import date, datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Date, Integer, String, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Параметри підключення до бази даних 
DATABASE_URL = "sqlite:///./contacts.sql"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модель контакту
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    birthday = Column(Date)
    extra_data = Column(String, nullable=True)

# Модель для створення контакту


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    extra_data: str = None

# Модель для оновлення контакту


class ContactUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    phone_number: str = None
    birthday: date = None
    extra_data: str = None

# Модель для відображення контакту


class ContactDisplay(ContactCreate):
    id: int


# Схема контакту для валідації даних
class ContactSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_data: str = None


# З'єднання до бази даних
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown():
    pass


# Ендпоінт для створення нового контакту
@app.post("/contacts/")
async def create_contact(contact: ContactCreate):
    db = SessionLocal()
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


# Ендпоінт для отримання списку всіх контактів
@app.get("/contacts/")
async def get_all_contacts():
    db = SessionLocal()
    contacts = db.query(Contact).all()
    return contacts

# Ендпоінт для отримання інформації про контакт


@app.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    db = SessionLocal()
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

# Ендпоінт для оновлення існуючого контакту


@app.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, contact_update: ContactUpdate):
    db = SessionLocal()
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in contact_update.dict(exclude_unset=True).items():
        setattr(db_contact, field, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact

# Ендпоінт для видалення контакту


@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    db = SessionLocal()
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted successfully"}


# Ендпоінт для пошуку контактів за ім'ям, прізвищем або адресою електронної пошти
@app.get("/contacts/search/")
async def search_contacts(query: str):
    db = SessionLocal()
    contacts = db.query(Contact).filter(
        (Contact.first_name.ilike(f"%{query}%")) |
        (Contact.last_name.ilike(f"%{query}%")) |
        (Contact.email.ilike(f"%{query}%"))
    ).all()
    return contacts


# Ендпоінт для отримання контактів з днями народження на найближчі 7 днів
@app.get("/contacts/birthdays/")
async def get_upcoming_birthdays():
    db = SessionLocal()
    today = datetime.now().date()
    upcoming_date = today + timedelta(days=7)
    year_of_birth = func.strftime("%Y", Contact.birthday)
    contacts = db.query(Contact).filter(
        (func.strftime("%m-%d", Contact.birthday) >= today.strftime("%m-%d")) &
        (func.strftime("%m-%d", Contact.birthday) < upcoming_date.strftime("%m-%d"))
    ).all()

    return contacts

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



