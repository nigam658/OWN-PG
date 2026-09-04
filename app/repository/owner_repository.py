from sqlalchemy.orm import Session
from app.models.owner_model import Owner


# for auth
def get_owner_by_email(db: Session, email: str):
    return db.query(Owner).filter(Owner.email == email).first()


# for auth
def get_owner_by_phone(db: Session, phone: str):
    return db.query(Owner).filter(Owner.phone == phone).first()


# for auth
def create_owner(db: Session, name: str, email: str, phone: str, password: str):

    owner = Owner(name=name, email=email, phone=phone, password=password)

    db.add(owner)
    db.commit()
    db.refresh(owner)

    return owner