"""Cloud storage; the local CLI's private files are never read or imported."""
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (JSON, Column, ForeignKey, Integer, MetaData, String,
                        Table, Text, UniqueConstraint, create_engine, event, text)

ROOT = Path(__file__).resolve().parents[2]
metadata = MetaData()
users = Table('users', metadata, Column('id', String(64), primary_key=True),
              Column('identity', String(128), unique=True, nullable=False))
sessions = Table('sessions', metadata, Column('token_hash', String(64), primary_key=True),
                 Column('user_id', ForeignKey('users.id'), nullable=False),
                 Column('expires_at', Integer, nullable=False))
packs = Table('exam_releases', metadata, Column('id', String(80), primary_key=True),
              Column('exam_id', String(100), nullable=False), Column('payload', JSON, nullable=False))
questions = Table('questions', metadata,
                  Column('key', String(150), primary_key=True),
                  Column('release_id', ForeignKey('exam_releases.id'), nullable=False),
                  Column('item_id', String(80), nullable=False),
                  Column('payload', JSON, nullable=False))
goals = Table('learning_goals', metadata, Column('id', String(64), primary_key=True),
              Column('user_id', ForeignKey('users.id'), nullable=False),
              Column('release_id', ForeignKey('exam_releases.id'), nullable=False),
              Column('profile', JSON, nullable=False), Column('state', JSON, nullable=False),
              UniqueConstraint('user_id', 'release_id'))
issues = Table('question_issues', metadata, Column('id', String(64), primary_key=True),
               Column('goal_id', ForeignKey('learning_goals.id'), nullable=False),
               Column('question_key', ForeignKey('questions.key'), nullable=False),
               Column('issued_at', Integer, nullable=False))
attempts = Table('learning_attempts', metadata, Column('id', String(64), primary_key=True),
                 Column('issue_id', ForeignKey('question_issues.id'), unique=True, nullable=False),
                 Column('goal_id', ForeignKey('learning_goals.id'), nullable=False),
                 Column('request', JSON, nullable=False), Column('event', JSON, nullable=False),
                 Column('report', JSON, nullable=False))


def make_engine(url=None):
    url = url or os.getenv('DATABASE_URL')
    if not url:
        directory = ROOT / '.study' / 'cloud-dev'
        directory.mkdir(parents=True, exist_ok=True)
        url = f'sqlite:///{directory / "app.db"}'
    engine = create_engine(url, pool_pre_ping=True,
                           connect_args={'check_same_thread': False, 'timeout': 30}
                           if url.startswith('sqlite') else {})
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def sqlite_pragmas(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
    else:
        engine = engine.execution_options(schema_translate_map={None: 'coach'})
    return engine


@contextmanager
def transaction(engine):
    with engine.connect() as connection:
        if engine.dialect.name == 'sqlite':
            connection.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            connection.begin()
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise


def migrate(engine):
    # Initial additive migration. Subsequent changes must use versioned migrations.
    if engine.dialect.name == 'postgresql':
        with engine.begin() as connection:
            connection.execute(text('CREATE SCHEMA IF NOT EXISTS coach'))
            connection.execute(text('REVOKE ALL ON SCHEMA coach FROM PUBLIC'))
    metadata.create_all(engine)


if __name__ == '__main__':
    migrate(make_engine())
    print('Initial database schema ready; no learner files imported.')
