import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        default=('sqlite:///' + os.path.join(basedir, 'app.db'))
    )
    ISSUES_PER_PAGE = 10


if __name__ == "__main__":
    members = [getattr(Config, attr) for attr in dir(Config) if not callable(getattr(Config(), attr)) and not attr.startswith("__")]
    print(members)