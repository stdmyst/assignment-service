from app import db, login

from sqlalchemy.orm import Mapped, mapped_column, WriteOnlyMapped, relationship
from sqlalchemy import String, Integer, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from typing import Optional
from datetime import datetime, timezone


class UserRights():
    ''' User permissions '''

    can_admin_users = 1 << 0  # 00000001
    can_create_issues = 1 << 1  # 00000010
    can_see_all_issues = 1 << 2  # 00000100
    can_change_issues_status = 1 << 3  # 00001000
    
    # Basic user: 00001100
    basic_rights = (can_see_all_issues | can_change_issues_status)
    # Leaders group: 00001110
    lid_rights = (can_create_issues | can_see_all_issues | can_change_issues_status)
    # Administrators: 00001111
    admin_rights = (can_admin_users | can_create_issues | can_see_all_issues | can_change_issues_status)
    

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    user_rights: Mapped[int] = mapped_column(Integer, default=(UserRights.basic_rights))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_user_rights(self, group, *args):
        if group and hasattr(UserRights, group):
            self.user_rights = getattr(UserRights, group)
            return
        for right in args:
            if hasattr(UserRights, right):
                self.user_rights |= getattr(UserRights, right)

    def check_user_right(self, right: int):
        return bool(self.user_rights & right)

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

    def __repr__(self):
        return f'{self.issue_name}\n\n{self.body}'


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
