
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from pydantic import BaseModel
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
    type = Column(Enum(QuestionType))
    options = Column(ARRAY(String))
    form_id = Column(Integer, ForeignKey("forms.id"))
    form = relationship("Form", back_populates="questions")

# Подключение к PostgreSQL
DATABASE_URL = "postgresql://admin:admin@localhost/forms_db"
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

def create_form(form: FormCreate, db: Session = Depends(SessionLocal)):
    db_form = Form(title=form.title)
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    for q in form.questions:
        db_question = Question(**q.dict(), form_id=db_form.id)
        db.add(db_question)
    db.commit()
    return db_form

@app.post("/forms/", response_model=Form)
def create_form_endpoint(form: FormCreate):
    return create_form(form)

@app.get("/forms/{form_id}/", response_model=Form)
def read_form(form_id: int, db: Session = Depends(SessionLocal)):
    form = db.query(Form).filter(Form.id == form_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return form
