from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class Org(Base):
    __tablename__ = "orgs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="org", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="org", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="org", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    org = relationship("Org", back_populates="users")

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"), index=True)
    name: Mapped[str] = mapped_column(String(250))
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    org = relationship("Org", back_populates="accounts")
    contacts = relationship("Contact", back_populates="account", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="account", cascade="all, delete-orphan")

class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    account = relationship("Account", back_populates="contacts")

class Stage(Base):
    __tablename__ = "stages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    order: Mapped[int] = mapped_column(Integer, index=True)

    checklist_items = relationship("StageChecklistItem", back_populates="stage", cascade="all, delete-orphan")
    deliverables = relationship("StageDeliverable", back_populates="stage", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    name: Mapped[str] = mapped_column(String(250))
    package: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active / paused / done
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    org = relationship("Org", back_populates="projects")
    account = relationship("Account", back_populates="projects")
    stages = relationship("ProjectStage", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="project", cascade="all, delete-orphan")

class ProjectStage(Base):
    __tablename__ = "project_stages"
    __table_args__ = (UniqueConstraint("project_id", "stage_id", name="uq_project_stage"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo / doing / done / blocked
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("Project", back_populates="stages")
    stage = relationship("Stage")
    checklist = relationship("ProjectChecklist", back_populates="project_stage", cascade="all, delete-orphan")
    deliverables = relationship("ProjectDeliverable", back_populates="project_stage", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="project_stage", cascade="all, delete-orphan")

class StageChecklistItem(Base):
    __tablename__ = "stage_checklist_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), index=True)
    text: Mapped[str] = mapped_column(String(300))
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    stage = relationship("Stage", back_populates="checklist_items")

class ProjectChecklist(Base):
    __tablename__ = "project_checklist"
    __table_args__ = (UniqueConstraint("project_stage_id", "item_id", name="uq_stage_item"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_stage_id: Mapped[int] = mapped_column(ForeignKey("project_stages.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stage_checklist_items.id"), index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project_stage = relationship("ProjectStage", back_populates="checklist")
    item = relationship("StageChecklistItem")

class StageDeliverable(Base):
    __tablename__ = "stage_deliverables"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), index=True)
    name: Mapped[str] = mapped_column(String(220))
    dtype: Mapped[str] = mapped_column(String(40), default="doc") # doc/file/link
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    stage = relationship("Stage", back_populates="deliverables")

class ProjectDeliverable(Base):
    __tablename__ = "project_deliverables"
    __table_args__ = (UniqueConstraint("project_stage_id", "deliverable_id", name="uq_stage_deliv"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_stage_id: Mapped[int] = mapped_column(ForeignKey("project_stages.id"), index=True)
    deliverable_id: Mapped[int] = mapped_column(ForeignKey("stage_deliverables.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft/submitted/approved
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # quick notes / link
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_stage = relationship("ProjectStage", back_populates="deliverables")
    deliverable = relationship("StageDeliverable")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    project_stage_id: Mapped[int | None] = mapped_column(ForeignKey("project_stages.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(280))
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="todo") # todo/doing/done
    priority: Mapped[str] = mapped_column(String(10), default="med") # low/med/high
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")

class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(260))
    otype: Mapped[str] = mapped_column(String(40), default="partnership") # partnership/channel/deal
    value_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True) # 0-100
    stage: Mapped[str] = mapped_column(String(30), default="new") # new/qualified/pitched/won/lost
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="opportunities")

class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_stage_id: Mapped[int] = mapped_column(ForeignKey("project_stages.id"), index=True)
    decision: Mapped[str] = mapped_column(String(10)) # approve/reject
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    by_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_stage = relationship("ProjectStage", back_populates="approvals")
