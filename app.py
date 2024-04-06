from enum import Enum
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import JSON
from pydantic import BaseModel, Field
from typing import List



Base = declarative_base()

class QuestionType(str, Enum):
    text = "text"
    radio = "radio"
    checkbox = "checkbox"

class Form(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    questions = relationship("Question", back_populates="form")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    type = Column(String)  
    options = Column(JSON)
    form_id = Column(Integer, ForeignKey("forms.id"))
    form = relationship("Form", back_populates="questions")


DATABASE_URL = "mysql+mysqlconnector://root:qwerty@localhost/forms"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

class QuestionBase(BaseModel):
    text: str
    type: QuestionType
    options: List[str] = []

class QuestionCreate(QuestionBase):
    pass

class FormBase(BaseModel):
    title: str

class FormCreate(FormBase):
    questions: List[QuestionCreate]

class Form(FormBase):
    # __tablename__ = "forms"
    # __table_args__ = {'extend_existing': True}
    # id = Column(Integer, primary_key=True, index=True)
    # title = Column(String, index=True)
    # questions = relationship("Question", back_populates="form")
    questions: List[QuestionBase] = []

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_form(form: FormCreate, db: Session = Depends(get_db)):
    db_form = Form(title=form.title)

    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    for q in form.questions:
        db_question = Question(**q.dict(), form_id=db_form.id, type=q.type.value)
        db.add(db_question)
    db.commit()
    return db_form

@app.post("/forms/", response_model=Form)
def create_form_endpoint(form: FormCreate, db: Session = Depends(get_db)):
    return create_form(form, db)

@app.get("/forms/{form_id}/", response_model=Form)
def read_form(form_id: int, db: Session = Depends(SessionLocal)):
    form = db.query('forms').filter('forms'.id == form_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return form



