from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

task_dependency = Table(
    'task_dependency',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id'), primary_key=True),
    Column('depends_on_id', String, ForeignKey('tasks.id'), primary_key=True)
)

class Project(Base):
    __tablename__ = 'projects'

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="To Do")
    assigned_agent = Column(String)
    priority = Column(String, default="medium")

    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="tasks")

    dependencies = relationship(
        "Task",
        secondary=task_dependency,
        primaryjoin=id == task_dependency.c.task_id,
        secondaryjoin=id == task_dependency.c.depends_on_id,
        backref="dependents"
    )

class Risk(Base):
    __tablename__ = 'risks'

    id = Column(String, primary_key=True, default=generate_uuid)
    description = Column(Text, nullable=False)
    severity = Column(String, default="Medium")

    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="risks")
