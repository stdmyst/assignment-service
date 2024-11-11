from app import app, db
from app import db
from app.forms import LoginForm, RegistrationForm, CreateIssueForm
from app.models import User, Issue

from flask import (render_template, flash, redirect, url_for, request)
from flask_login import (current_user, login_user, logout_user, login_required)

from urllib.parse import urlsplit

import sqlalchemy as sa


@app.route('/')
@app.route('/index')
@login_required
def index():
    query = sa.select(Issue).where(Issue.executor_id == current_user.id)
    executor_issues = db.session.scalars(query).all()
    query = sa.select(Issue).where(Issue.reporter_id == current_user.id)
    reporter_issues = db.session.scalars(query).all()
    return render_template(
        'index.html',
        title='Home Page',
        executor_issues=executor_issues,
        reporter_issues=reporter_issues,
        )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form,)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/registration', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration was successful!')
        return redirect(url_for('login'))
    return render_template('registration.html', title='Registration', form=form)


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

    return render_template('issue_creation.html', title='Create issue', form=form)


@app.route('/api/issues/<issue_id>', methods=['GET', 'POST'])
@login_required
def issue(issue_id):
    query = sa.select(Issue).where(Issue.id == int(issue_id))
    issue = db.session.scalar(query)
    executor = db.session.scalar(
        sa.select(User).where(User.id == issue.executor_id)
    )
    reporter = db.session.scalar(
        sa.select(User).where(User.id == issue.reporter_id)
    )
    return render_template(
        'issue_template.html',
        title=f'Issue: {issue.issue_name}',
        issue=issue,
        executor=executor,
        reporter=reporter,
    )
