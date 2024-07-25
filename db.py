from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db
from flask import Flask
import os

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(base_dir, 'database')
database_path = os.path.join(database_dir, 'task_minder_db.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

if not os.path.exists(database_dir):
    os.makedirs(database_dir)

engine = create_engine(f'sqlite:///{database_path}')

Session = sessionmaker(bind=engine)
session = Session()

with app.app_context():
    db.create_all()

print("Tablas creadas con éxito.")
