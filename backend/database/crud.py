from sqlalchemy.orm import Session


class CRUDBase:

    def create(self, db: Session, obj):
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj):
        db.delete(obj)
        db.commit()

    def update(self, db: Session):
        db.commit()