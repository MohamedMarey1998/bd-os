from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from .db import Base, engine, get_db
from .models import Org, User, Account, Contact, Project, Stage, ProjectStage, StageChecklistItem, ProjectChecklist, StageDeliverable, ProjectDeliverable, Task, Opportunity, Approval
from .auth import verify_password, create_session_token, COOKIE_NAME, get_current_user_id
from .seed import seed

app = FastAPI(title="BD OS MVP")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed(db)

def require_user(request: Request, db: Session):
    uid = get_current_user_id(request)
    if not uid:
        return None
    return db.query(User).filter(User.id==uid).first()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    projects = db.query(Project).filter(Project.org_id==user.org_id).order_by(Project.created_at.desc()).limit(25).all()
    accounts = db.query(Account).filter(Account.org_id==user.org_id).order_by(Account.created_at.desc()).limit(10).all()
    # simple alerts
    overdue_tasks = db.query(Task).join(Project, Task.project_id==Project.id).filter(Project.org_id==user.org_id, Task.status!="done", Task.due_date!=None, Task.due_date < datetime.utcnow()).count()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "projects": projects, "accounts": accounts, "overdue_tasks": overdue_tasks})

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login_post(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.email==email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = create_session_token(user.id)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax")
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp

# Accounts
@app.get("/accounts", response_class=HTMLResponse)
def accounts_list(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    accounts = db.query(Account).filter(Account.org_id==user.org_id).order_by(Account.created_at.desc()).all()
    return templates.TemplateResponse("accounts.html", {"request": request, "user": user, "accounts": accounts})

@app.get("/accounts/new", response_class=HTMLResponse)
def accounts_new_get(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("account_new.html", {"request": request, "user": user})

@app.post("/accounts/new")
def accounts_new_post(request: Request, db: Session = Depends(get_db),
                      name: str = Form(...), industry: str = Form(""), size: str = Form(""), country: str = Form("")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    acc = Account(org_id=user.org_id, name=name, industry=industry or None, size=size or None, country=country or None, owner_user_id=user.id)
    db.add(acc); db.commit()
    return RedirectResponse("/accounts", status_code=302)

@app.get("/accounts/{account_id}", response_class=HTMLResponse)
def account_detail(request: Request, account_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id==account_id, Account.org_id==user.org_id).first()
    if not acc: return RedirectResponse("/accounts", status_code=302)
    projects = db.query(Project).filter(Project.account_id==acc.id).order_by(Project.created_at.desc()).all()
    return templates.TemplateResponse("account_detail.html", {"request": request, "user": user, "acc": acc, "projects": projects})

# Projects
def init_project_stages(db: Session, project: Project):
    stages = db.query(Stage).order_by(Stage.order.asc()).all()
    for st in stages:
        ps = ProjectStage(project_id=project.id, stage_id=st.id, status="todo")
        db.add(ps)
        db.commit()
        db.refresh(ps)
        # checklist
        items = db.query(StageChecklistItem).filter(StageChecklistItem.stage_id==st.id).all()
        for it in items:
            db.add(ProjectChecklist(project_stage_id=ps.id, item_id=it.id, done=False))
        # deliverables
        dels = db.query(StageDeliverable).filter(StageDeliverable.stage_id==st.id).all()
        for d in dels:
            db.add(ProjectDeliverable(project_stage_id=ps.id, deliverable_id=d.id, status="draft", version=1))
        db.commit()

@app.get("/projects/new/{account_id}", response_class=HTMLResponse)
def project_new_get(request: Request, account_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id==account_id, Account.org_id==user.org_id).first()
    if not acc: return RedirectResponse("/accounts", status_code=302)
    return templates.TemplateResponse("project_new.html", {"request": request, "user": user, "acc": acc})

@app.post("/projects/new/{account_id}")
def project_new_post(request: Request, account_id: int, db: Session = Depends(get_db),
                     name: str = Form(...), package: str = Form(""), lead_source: str = Form("")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id==account_id, Account.org_id==user.org_id).first()
    if not acc: return RedirectResponse("/accounts", status_code=302)
    pr = Project(org_id=user.org_id, account_id=acc.id, name=name, package=package or None, lead_source=lead_source or None, status="active")
    db.add(pr); db.commit(); db.refresh(pr)
    init_project_stages(db, pr)
    return RedirectResponse(f"/projects/{pr.id}", status_code=302)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    pr = db.query(Project).filter(Project.id==project_id, Project.org_id==user.org_id).first()
    if not pr: return RedirectResponse("/", status_code=302)
    stages = db.query(ProjectStage).filter(ProjectStage.project_id==pr.id).join(Stage, ProjectStage.stage_id==Stage.id).order_by(Stage.order.asc()).all()
    # progress
    done = sum(1 for s in stages if s.status=="done")
    progress = int((done/len(stages))*100) if stages else 0
    tasks = db.query(Task).filter(Task.project_id==pr.id).order_by(Task.created_at.desc()).limit(10).all()
    opps = db.query(Opportunity).filter(Opportunity.project_id==pr.id).order_by(Opportunity.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("project_detail.html", {"request": request, "user": user, "pr": pr, "stages": stages, "progress": progress, "tasks": tasks, "opps": opps})

@app.get("/projects/{project_id}/stage/{project_stage_id}", response_class=HTMLResponse)
def stage_detail(request: Request, project_id: int, project_stage_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    ps = db.query(ProjectStage).join(Project, ProjectStage.project_id==Project.id).filter(Project.id==project_id, Project.org_id==user.org_id, ProjectStage.id==project_stage_id).first()
    if not ps: return RedirectResponse(f"/projects/{project_id}", status_code=302)
    stage = db.query(Stage).filter(Stage.id==ps.stage_id).first()
    checklist = db.query(ProjectChecklist).filter(ProjectChecklist.project_stage_id==ps.id).all()
    deliverables = db.query(ProjectDeliverable).filter(ProjectDeliverable.project_stage_id==ps.id).all()
    approvals = db.query(Approval).filter(Approval.project_stage_id==ps.id).order_by(Approval.at.desc()).all()
    return templates.TemplateResponse("stage_detail.html", {"request": request, "user": user, "ps": ps, "stage": stage, "checklist": checklist, "deliverables": deliverables, "approvals": approvals, "project_id": project_id})

@app.post("/projects/{project_id}/stage/{project_stage_id}/toggle")
def checklist_toggle(request: Request, project_id: int, project_stage_id: int, db: Session = Depends(get_db), cid: int = Form(...)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    row = db.query(ProjectChecklist).join(ProjectStage, ProjectChecklist.project_stage_id==ProjectStage.id).join(Project, ProjectStage.project_id==Project.id)        .filter(Project.id==project_id, Project.org_id==user.org_id, ProjectChecklist.id==cid, ProjectStage.id==project_stage_id).first()
    if row:
        row.done = not row.done
        row.done_by = user.id if row.done else None
        row.done_at = datetime.utcnow() if row.done else None
        db.commit()
    return RedirectResponse(f"/projects/{project_id}/stage/{project_stage_id}", status_code=302)

@app.post("/projects/{project_id}/stage/{project_stage_id}/deliverable")
def deliverable_update(request: Request, project_id: int, project_stage_id: int, db: Session = Depends(get_db),
                       did: int = Form(...), content: str = Form("")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    d = db.query(ProjectDeliverable).join(ProjectStage, ProjectDeliverable.project_stage_id==ProjectStage.id).join(Project, ProjectStage.project_id==Project.id)        .filter(Project.id==project_id, Project.org_id==user.org_id, ProjectStage.id==project_stage_id, ProjectDeliverable.id==did).first()
    if d:
        d.content = content
        d.updated_at = datetime.utcnow()
        d.status = "submitted" if content.strip() else "draft"
        db.commit()
    return RedirectResponse(f"/projects/{project_id}/stage/{project_stage_id}", status_code=302)

@app.post("/projects/{project_id}/stage/{project_stage_id}/approve")
def stage_approve(request: Request, project_id: int, project_stage_id: int, db: Session = Depends(get_db),
                 decision: str = Form(...), comment: str = Form("")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    ps = db.query(ProjectStage).join(Project, ProjectStage.project_id==Project.id)        .filter(Project.id==project_id, Project.org_id==user.org_id, ProjectStage.id==project_stage_id).first()
    if ps:
        db.add(Approval(project_stage_id=ps.id, decision=decision, comment=comment or None, by_user=user.id))
        if decision == "approve":
            ps.status = "done"
            ps.completed_at = datetime.utcnow()
            ps.approved_by = user.id
            ps.approved_at = datetime.utcnow()
        else:
            ps.status = "blocked"
        db.commit()
    return RedirectResponse(f"/projects/{project_id}/stage/{project_stage_id}", status_code=302)

# Tasks
@app.get("/projects/{project_id}/tasks", response_class=HTMLResponse)
def tasks_list(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    pr = db.query(Project).filter(Project.id==project_id, Project.org_id==user.org_id).first()
    if not pr: return RedirectResponse("/", status_code=302)
    tasks = db.query(Task).filter(Task.project_id==pr.id).order_by(Task.created_at.desc()).all()
    stages = db.query(ProjectStage).filter(ProjectStage.project_id==pr.id).all()
    return templates.TemplateResponse("tasks.html", {"request": request, "user": user, "pr": pr, "tasks": tasks, "stages": stages})

@app.post("/projects/{project_id}/tasks/new")
def task_new(request: Request, project_id: int, db: Session = Depends(get_db),
             title: str = Form(...), project_stage_id: int = Form(0), priority: str = Form("med")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    pr = db.query(Project).filter(Project.id==project_id, Project.org_id==user.org_id).first()
    if not pr: return RedirectResponse("/", status_code=302)
    psid = project_stage_id if project_stage_id != 0 else None
    db.add(Task(project_id=pr.id, project_stage_id=psid, title=title, owner_user_id=user.id, priority=priority))
    db.commit()
    return RedirectResponse(f"/projects/{project_id}/tasks", status_code=302)

@app.post("/tasks/{task_id}/set")
def task_set(request: Request, task_id: int, db: Session = Depends(get_db), status: str = Form(...)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    t = db.query(Task).join(Project, Task.project_id==Project.id).filter(Task.id==task_id, Project.org_id==user.org_id).first()
    if t:
        t.status = status
        db.commit()
        return RedirectResponse(f"/projects/{t.project_id}/tasks", status_code=302)
    return RedirectResponse("/", status_code=302)

# Opportunities
@app.get("/projects/{project_id}/opportunities", response_class=HTMLResponse)
def opps_list(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    pr = db.query(Project).filter(Project.id==project_id, Project.org_id==user.org_id).first()
    if not pr: return RedirectResponse("/", status_code=302)
    opps = db.query(Opportunity).filter(Opportunity.project_id==pr.id).order_by(Opportunity.created_at.desc()).all()
    return templates.TemplateResponse("opportunities.html", {"request": request, "user": user, "pr": pr, "opps": opps})

@app.post("/projects/{project_id}/opportunities/new")
def opp_new(request: Request, project_id: int, db: Session = Depends(get_db),
            title: str = Form(...), otype: str = Form("partnership"), value_estimate: str = Form(""), probability: str = Form(""), notes: str = Form("")):
    user = require_user(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    pr = db.query(Project).filter(Project.id==project_id, Project.org_id==user.org_id).first()
    if not pr: return RedirectResponse("/", status_code=302)
    ve = int(value_estimate) if value_estimate.strip().isdigit() else None
    pb = int(probability) if probability.strip().isdigit() else None
    db.add(Opportunity(project_id=pr.id, title=title, otype=otype, value_estimate=ve, probability=pb, notes=notes or None))
    db.commit()
    return RedirectResponse(f"/projects/{project_id}/opportunities", status_code=302)
