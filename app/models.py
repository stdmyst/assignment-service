from app import db, login

from sqlalchemy.orm import Mapped, mapped_column, WriteOnlyMapped, relationship
from sqlalchemy import String, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from typing import Optional
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    
    # reporter_of_issue: WriteOnlyMapped['Issue'] =  relationship(back_populates='reporter')
    # executor_of_issue: WriteOnlyMapped['Issue'] =  relationship(back_populates='executor')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'User: {self.username}'


class Issue(db.Model):
    __tablename__ = 'issues'

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(64), default="Assigned")
    issue_name: Mapped[str] = mapped_column(String(64))
    issue_body: Mapped[str] = mapped_column(String(120))
    date_of_issue: Mapped[datetime] = mapped_column(index=True, default=datetime.now(tz=timezone.utc))
    date_of_completion: Mapped[Optional[datetime]] = mapped_column(index=True)
    actual_date_of_completion: Mapped[Optional[datetime]] = mapped_column(index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # reporter: Mapped['User'] = relationship(back_populates='reporter_of_issue')
    # executor: Mapped['User'] = relationship(back_populates='executor_of_issue')

    def __repr__(self):
        return f'{self.issue_name}\n\n{self.body}'
    

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
