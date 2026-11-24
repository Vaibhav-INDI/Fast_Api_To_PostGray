"""connecting python to postgry without endpoints"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Float, Integer
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)  # help to create table or class

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # only for security purpose.

print(DATABASE_URL)

# next step to create engin

engin = create_engine(DATABASE_URL)

with engin.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
    print(version.split(",")[0])

    # .all() -every first row
    # .first() - only the first row
    # .scalar()-first value of first row


# declarativve base is parent calass of sql alchecmy which give you power of create table
class Base(DeclarativeBase):
    pass


class Student_db(Base):
    __tablename__ = "Student_record"
    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    marks = Column(Integer, nullable=False)
    course = Column(String(50), nullable=False)
    email = Column(String, nullable=False, unique=True)


Base.metadata.create_all(bind=engin)

# by this way we can play with db
sessionlocal = sessionmaker(bind=engin)
db = sessionlocal()

# if db.get(Student_db, "S001") is None:
# create
# if True:
#     db.add(
#         Student_db(
#             id="S002",
#             name="vaibhav",
#             age=23,
#             course="c pro",
#             email="fdsk@gmail.com",
#             marks=23,
#         )
#     )
    # db.commit()
    # print("user added")
    #read
for i in db.query(Student_db).all():
    print(i.id,i.name,i.age,i.email,i.course,i.marks)
       
   
# update 

stu1=db.get(Student_db,"S001")
print(stu1.marks)
stu1.marks=70
db.commit()
print("Field updated")
