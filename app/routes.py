from app import app, db
from app.forms import (
    LoginForm,
    AddUserForm,
    CreateIssueForm,
    TaskFiltersForm,
    EditPasswordForm,
    EditProfileForm,
    EditIssueForm
    )
from app.models import User, Issue, UserRights

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from sqlalchemy import func

from urllib.parse import urlsplit
from datetime import datetime, date


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if int(current_user.user_rights) == UserRights.admin_rights:
        user_filter = True
    else:
        user_filter = (
            (Issue.reporter_id == int(current_user.id)) or
            (Issue.executor_id == int(current_user.id))
        )

    query = (
        sa.select(Issue)
        .where((func.Date(Issue.date_of_completion) == date.today()) & user_filter & (Issue.status.in_(["Assigned", "On Hold"])))
        .order_by(Issue.date_of_completion.desc()))

    page = request.args.get('page', 1, type=int)  # pagination support
    issues = db.paginate(
        query,
        page=page,
        per_page=10,
        error_out=False
    )
    req_args = request.args
    next_url = url_for('index', page=issues.next_num) \
        if issues.has_next else None
    prev_url = url_for('index', page=issues.prev_num) \
        if issues.has_prev else None
    
    filter_form = TaskFiltersForm()

    filter_query = sa.select(Issue.status).distinct()
    statuses = db.session.scalars(filter_query).all()
    statuses.append('None')
    filter_form.status_filter.choices = statuses

    if filter_form.validate_on_submit():
        if not (status := filter_form.status_filter.data):
            status = 'None'
        if status == 'None':
            status_filter = (Issue.status.in_(statuses))
        else:
            status_filter = (Issue.status == status)
            
        if dt := filter_form.date_filter.data:  # date format
            date_filter = (func.Date(Issue.date_of_completion) == dt)
        else:
            date_filter = (func.Date(Issue.date_of_completion) == date.today())

        query = (
            sa.select(Issue)
            .where(date_filter & status_filter & user_filter)
            .order_by(Issue.date_of_completion.desc())
        )
        issues = db.paginate(
            query,
            page=page,
            per_page=10,
            error_out=False
         )
    
    return render_template(
        'index.html',
        title='Home Page',
        issues=issues.items,
        find_user=find_user,
        next_url=next_url,
        prev_url=prev_url,
        format_datetime=format_datetime,
        rights_model=UserRights,
        args=req_args,
        filter_form=filter_form,
        statuses=statuses
        )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template(
        'login.html',
        title='Sign In',
        form=form
    )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.check_user_right(UserRights.can_admin_users):
        flash('You do not have rights to the specified resource.')
        return redirect(url_for('index'))
    
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            user_rights=form.user_rights.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration was successful!')
        return redirect(url_for('administration'))
    return render_template(
        'add_user.html',
        title='Add user',
        form=form,
        rights_model=UserRights
    )


@app.route('/issue_creation', methods=['GET', 'POST'])
@login_required
def issue_creation():
    form = CreateIssueForm()
    query = sa.select(User)
    users=db.session.scalars(query).all()
    form.executor.choices = [(u.id, u.username) for u in users]

    if form.validate_on_submit():
        issue = Issue(
            issue_name=form.issue_name.data,
            issue_body=form.issue_body.data,
            date_of_completion=form.date_of_completion.data,
            reporter_id=current_user.id,
            executor_id=form.executor.data
        )
        db.session.add(issue)
        db.session.commit()
        flash(f'Issue "{form.issue_name.data}" added!')
        return redirect(url_for('index'))
    return render_template(
        'issue_page.html',
        title='Create issue',
        form=form,
        rights_model=UserRights
    )


@app.route('/api/issues/<issue_id>', methods=['GET', 'POST'])
@login_required
def issue(issue_id):
    form = EditIssueForm()

    query = sa.select(User)
    users=db.session.scalars(query).all()
    form.executor.choices = [(u.id, u.username) for u in users]

    query = sa.select(Issue).where(Issue.id == int(issue_id))
    issue = db.session.scalar(query)
    executor = db.session.scalar(
        sa.select(User).where(User.id == issue.executor_id))

    if form.validate_on_submit():
        issue.issue_name=form.issue_name.data
        issue.issue_body=form.issue_body.data
        issue.date_of_completion=form.date_of_completion.data
        issue.executor_id=form.executor.data
        issue.status = form.status.data
        if issue.status == 'Resolved':
            issue.actual_date_of_completion = datetime.now()
        else:
            issue.actual_date_of_completion = None
        db.session.commit()
        flash(f'Issue "{issue.issue_name}" updated!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.issue_name.data = issue.issue_name
        form.issue_body.data = issue.issue_body
        form.date_of_completion.data = issue.date_of_completion
        form.executor.data = executor.id
        form.status.data = issue.status
        form.submit.label.text = "Edit issue"
    
    deletion_allowed = False
    if (current_user.user_rights == UserRights.admin_rights) or (issue.reporter_id == current_user.id):
        deletion_allowed = True

    return render_template(
        'edit_issue.html',
        title='Edit Issue',
        form=form,
        rights_model=UserRights,
        issue_id=issue_id,
        deletion_allowed=deletion_allowed
    )


@app.route('/api/issues/<issue_id>/delete_issue', methods=['GET', 'POST'])
@login_required
def delete_issues(issue_id):
    if not current_user.check_user_right(UserRights.can_admin_users):
            flash('You do not have rights to the specified resource.')
            return redirect(url_for('index'))
    
    query = sa.select(Issue).where(Issue.id == int(issue_id))
    issue = db.session.scalar(query)
    if issue:
        db.session.delete(issue)
        db.session.commit()
        flash(f'The issue {issue_id} has been deleted!')
    return redirect(url_for('index'))


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def administration():
    if not current_user.check_user_right(UserRights.can_admin_users):
        flash('You do not have rights to the specified resource.')
        return redirect(url_for('index'))
    query = sa.select(User).where(User.username != "admin")
    page = request.args.get('page', 1, type=int)
    users = db.paginate(
        query,
        page=page,
        per_page=10,
        error_out=False
    )
    next_url = url_for('administration', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('administration', page=users.prev_num) \
        if users.has_prev else None
    return render_template(
        'admin.html',
        title="Administration",
        users=users,
        next_url=next_url,
        prev_url=prev_url,
        rights_model=UserRights
    )
    

@app.route("/api/users/profile/<user_id>", methods=['GET', 'POST'])
@login_required
def user(user_id):
    if not current_user.check_user_right(UserRights.can_admin_users):
        flash('You do not have rights to the specified resource.')
        return redirect(url_for('index'))
    
    query = sa.select(User).where(User.id == int(user_id))
    user = db.session.scalar(query)

    form = EditProfileForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.user_rights = form.user_rights.data
        db.session.commit()
        flash('Successfully!')
        return redirect(url_for('administration'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.user_rights.data = user.user_rights
        form.submit.label.text = "Edit profile"
    
    return render_template(
        'edit_profile.html',
        title="Edit profile",
        form=form,
        rights_model=UserRights,
        flag="edit",
        user=user
    )


@app.route('/api/users/profile/<user_id>/edit_password', methods=['GET', 'POST'])
@login_required
def edit_password(user_id):
    if not current_user.check_user_right(UserRights.can_admin_users):
        flash('You do not have rights to the specified resource.')
        return redirect(url_for('index'))

    user = find_user(user_id)
    
    form = EditPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Password changed successfully!')
        return render_template(
            'edit_profile.html',
            title="Edit profile",
            form=EditProfileForm(),
            rights_model=UserRights,
            user=user
        )
    
    return render_template(
        'edit_password.html',
        title="Reset password",
        form=form,
        rights_model=UserRights
    )


@app.route('/api/users/profile/<user_id>/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_profile(user_id):
    if not current_user.check_user_right(UserRights.can_admin_users):
            flash('You do not have rights to the specified resource.')
            return redirect(url_for('index'))
    
    if user := find_user(user_id):
        db.session.delete(user)
        db.session.commit()
        flash(f'The user {user_id} has been deleted!')
    return redirect(url_for('administration'))


def find_user(id: str):
    query = sa.select(User).where(User.id == id)
    return db.session.scalar(query)


def format_datetime(dt: datetime, format="standart"):
    if format == "standart":
        return dt.strftime("%Y-%m-%d %H:%M")
    return dt
