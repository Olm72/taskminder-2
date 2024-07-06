from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Creamos la DB "task_minder_db.db" que se encuentra en la carpeta "database"
engine = create_engine('sqlite:///database/task_minder_db.db',
                       connect_args={"check_same_thread": False})

# Ahora creamos la sesión, lo que nos permite realizar transacciones dentro de nuestra DB
Session = sessionmaker(bind=engine)
session = Session()

# Ahora vamos al fichero "models.py" - modelos (clases) donde queremos que se transformen en tablas, le añadiremos
# esta variable y esto se encargará de mapear y vincular cada clase a cada tabla
Base = declarative_base()

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)
