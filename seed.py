from sqlalchemy.orm import Session
from .models import Org, User, Stage, StageChecklistItem, StageDeliverable
from .auth import hash_password

STAGES = [{"code": "INTAKE", "name": "Intake & Contract", "order": 1}, {"code": "DIAG", "name": "Diagnosis & Discovery", "order": 2}, {"code": "MI", "name": "Market Intelligence", "order": 3}, {"code": "ICP", "name": "Customer & ICP", "order": 4}, {"code": "COMP", "name": "Competitor & Positioning", "order": 5}, {"code": "ECO", "name": "Ecosystem Mapping", "order": 6}, {"code": "STRAT", "name": "Strategy & Direction", "order": 7}, {"code": "BDPLAN", "name": "BD Plan & Operating Model", "order": 8}, {"code": "OFFER", "name": "Offer & Pricing", "order": 9}, {"code": "GTM", "name": "GTM & Sales Motion", "order": 10}, {"code": "OPPS", "name": "Opportunity & Partnerships Pipeline", "order": 11}, {"code": "KPIS", "name": "KPIs, Dashboard & Iteration", "order": 12}]
CHECKLISTS = {"INTAKE": ["Scope defined", "Goals agreed", "Stakeholders identified", "Contract signed"], "DIAG": ["Interviews completed", "Data collected", "Pain points prioritized", "Root causes drafted"], "MI": ["TAM/SAM/SOM estimated", "Segments mapped", "Demand signals captured"], "ICP": ["ICP drafted", "Personas created", "Buying committee mapped"], "COMP": ["Competitor set defined", "Positioning map created", "Differentiation points validated"], "ECO": ["Partners list", "Regulators list", "Alternatives list", "Ecosystem map exported"], "STRAT": ["Strategic options listed", "Priorities set", "Targets defined"], "BDPLAN": ["BD playbook drafted", "Operating model roles", "Process cadence"], "OFFER": ["Value proposition finalized", "Packaging tiers", "Pricing logic"], "GTM": ["Acquisition channels selected", "Funnel defined", "Sales motion documented"], "OPPS": ["Opportunity list created", "Scoring model applied", "Next actions assigned"], "KPIS": ["KPI set defined", "Dashboard live", "Iteration cadence scheduled"]}

DEFAULT_DELIVERABLES = {
"INTAKE": ["Scope & Goals","Stakeholder list"],
"DIAG": ["Diagnosis report","Priority problems list"],
"MI": ["Market intelligence brief"],
"ICP": ["ICP & Personas pack"],
"COMP": ["Competitor/Positioning sheet"],
"ECO": ["Ecosystem map"],
"STRAT": ["Strategy choices + priorities"],
"BDPLAN": ["BD operating model"],
"OFFER": ["Offer + pricing sheet"],
"GTM": ["GTM plan"],
"OPPS": ["Opportunity pipeline"],
"KPIS": ["KPI dashboard definition"],
}

def seed(db: Session):
    # Org + admin user
    org = db.query(Org).filter(Org.name=="Mohamed Marey BD OS").first()
    if not org:
        org = Org(name="Mohamed Marey BD OS")
        db.add(org)
        db.commit()
        db.refresh(org)
    admin = db.query(User).filter(User.email=="admin@local").first()
    if not admin:
        admin = User(org_id=org.id, name="Admin", email="admin@local", password_hash=hash_password("admin1234"), is_admin=True)
        db.add(admin)
        db.commit()

    # Stages
    for s in STAGES:
        st = db.query(Stage).filter(Stage.code==s["code"]).first()
        if not st:
            st = Stage(code=s["code"], name=s["name"], order=s["order"])
            db.add(st)
            db.commit()
            db.refresh(st)
        # checklist items
        for item_text in CHECKLISTS.get(s["code"], []):
            existing = db.query(StageChecklistItem).filter(StageChecklistItem.stage_id==st.id, StageChecklistItem.text==item_text).first()
            if not existing:
                db.add(StageChecklistItem(stage_id=st.id, text=item_text, required=True))
        # deliverables
        for dname in DEFAULT_DELIVERABLES.get(s["code"], []):
            exd = db.query(StageDeliverable).filter(StageDeliverable.stage_id==st.id, StageDeliverable.name==dname).first()
            if not exd:
                db.add(StageDeliverable(stage_id=st.id, name=dname, dtype="doc", required=True))
        db.commit()
