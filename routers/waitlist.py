from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from waitlist_model import Waitlist
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class WaitlistIn(BaseModel):
    email: EmailStr

@router.post("/", status_code=201)
def add_to_waitlist(data: WaitlistIn, db: Session = Depends(get_db)):
    if db.query(Waitlist).filter(Waitlist.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already in waitlist.")
    entry = Waitlist(email=data.email)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": str(entry.id), "email": entry.email, "created_at": entry.created_at}
