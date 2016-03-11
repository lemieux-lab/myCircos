#!flask/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import User
import os.path

#################################################
#						
#	             DATABASE			
#						
#################################################

# Creating all the tables for the described classes in models
db.create_all()

# Adding the Guest user
guest = User.query.filter_by(email='Guest').first()
if not guest : 
	user = User(email='Guest', password='')
	db.session.add(user)
	db.session.commit()


# Creating database (only once)
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
  api.create(SQLALCHEMY_MIGRATE_REPO, 'db_repository')
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

#making sure we are using the latest version of our database
else: 
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))


