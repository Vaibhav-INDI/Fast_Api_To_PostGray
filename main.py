# swagger -> Pydantic -> FastApi -> Session -> Database <- revert response
"""
Part 1: Load DATABASE_URL from the .env file   -dotenv/load_env
Part 2: Create the engine (connection to PostgreSQL) -url infused
Part 3: Create SessionLocal and Base -declarative base/sessionmaker
Part 4: Create the StudentDB table -base inherited class /tablename/base.metadata.crateall(bind=engin)
Part 5: Pydantic schemas for input (StudentCreate, StudentUpdate)
Part 6: Pydantic schemas for output (StudentResponse, StudentPage, Message) -model_config = ConfigDict(from_attributes=True)/@property@computed filed/->str
Part 7: get_db() - one session per request -try finally/yield/close
Part 8: Create the FastAPI app
Part 9: GET one student -:session/depends/responce_model
Part 10: POST - create a student-- create a student -response model/session/depends/basemodel/db.get/from sqlalchemy.exc import IntegrityError/  new_student = StudentDB(**student.model_dump())/add/commit
Part 11: PUT - update a student--changes = stu.model_dump(exclude_unset=True)/for loop keyvalue /setattr(student,key,value)
Part 12: DELETE - remove a student-db.delete
Part 13: GET all students (filter + sort + paginate) - All_stu=db.query(StudentDB).all()
"""

# Part 1: Load DATABASE_URL from the .env file
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)


# Part 2: Create the engine (connection to PostgreSQL)
from sqlalchemy import create_engine, String, Integer, Column

engin = create_engine(DATABASE_URL)


# Part 3: Create SessionLocal and Base
from sqlalchemy.orm import sessionmaker, DeclarativeBase

sessionlocal = sessionmaker(bind=engin)
# db=sessionlocal()


class Base(DeclarativeBase):
    pass


# Part 4: Create the StudentDB table
class StudentDB(Base):
    __tablename__ = "Student_Rec"
    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    course = Column(String, nullable=False)
    marks = Column(Integer, nullable=False)
    email = Column(String, nullable=False, unique=True)


Base.metadata.create_all(bind=engin)
print("Teable created...")

# Part 5: Pydantic schemas for input (StudentCreate, StudentUpdate)
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    computed_field,
    ConfigDict,
)


class Student(BaseModel):
    id: str = Field(...)
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=0, le=100)
    course: str = Field(min_length=1, max_length=30)
    marks: int = Field(ge=0, le=100)
    email: EmailStr = Field(...)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):

        if value.replace(" ", "").isalpha():
            return value.title()

        else:
            raise ValueError("pls correct the name")


class Update_Stu(BaseModel):
    # id: str | None = Field(None)
    name: str | None = Field(None, min_length=2, max_length=50)
    age: int | None = Field(None, gt=0, le=100)
    course: str | None = Field(None, min_length=1, max_length=30)
    marks: int | None = Field(None, ge=0, le=100)
    email: EmailStr | None = Field(None)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        if value is None:
            return value

        if value.replace(" ", "").isalpha():
            return value.title()

        raise ValueError("Please enter a valid name")


# Part 6: Pydantic schemas for output (StudentResponse, StudentPage, Message)
from pydantic import ConfigDict


class StudentResonse(Student):
    model_config = ConfigDict(
        from_attributes=True
    )  # it changing dic to obj whatever commming inside this func

    @computed_field
    @property
    def grade(self) -> str:
        if self.marks >= 90:
            return "A+"
        elif self.marks >= 75:
            return "A"
        elif self.marks >= 60:
            return "B"
        elif self.marks >= 50:
            return "C"
        else:
            return "Fail"


# Part 7: get_db() - one session per request
# we are opning session here which will stays open till operation done than aftere it will close automatic


def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


# Part 8: Create the FastAPI app
from fastapi import FastAPI, Path, HTTPException, Depends

app = FastAPI()


# Part 9: GET one student
from sqlalchemy.orm import Session


@app.get(
    "/Get_Stu/{Student_id}", response_model=StudentResonse
)  # you can add responce model here it will carry data
def Get_Student(
    Student_id: str = Path(..., description="Enter Stu Id"),
    db: Session = Depends(get_db),
):
    stu = db.get(StudentDB, Student_id)
    if stu is None:
        raise HTTPException(status_code=404, detail="Student does not exist")
    else:
        return stu


# Part 10: POST
from sqlalchemy.exc import IntegrityError


@app.post("/Create_Stu", response_model=StudentResonse, status_code=201)
def Create_Student(student: Student, db: Session = Depends(get_db)):
    if db.get(StudentDB, student.id):
        raise HTTPException(
            status_code=409, detail="Student with given id alredy exist"
        )

    new_student = StudentDB(**student.model_dump())
    db.add(new_student)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="email alredy exist")

    db.refresh(new_student)
    return new_student


# Part 11: PUT - update a student


@app.put("/Update_Stu/{Student_id}", response_model=StudentResonse)
def Update_Stu(
    stu: Update_Stu,
    Student_id: str = Path(..., description="add student id"),
    db: Session = Depends(get_db),
):
    student = db.get(StudentDB, Student_id)

    if student is None:
        raise HTTPException(
            status_code=404, detail="Student with given ID does not exist"
        )

    changes = stu.model_dump(exclude_unset=True)

    for key, value in changes.items():
        setattr(student, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="email already exists")

    db.refresh(student)
    return student


# Part 12: DELETE - remove a student
@app.delete("/Delete_Stu/{Student_id}")
def Delete_Stu(
    Student_id: str = Path(..., description="Enter Student Id "),
    db: Session = Depends(get_db),
):
    student = db.get(StudentDB, Student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Deltails not found for given Id")

    db.delete(student)

    db.commit()

    return {"msg": "Student Deleted"}


# Part 13: GET all students (filter + sort + paginate)
@app.get('/Get_All')
def Get_All(db:Session=Depends(get_db)):
    All_stu=db.query(StudentDB).all()
    return All_stu
    
    