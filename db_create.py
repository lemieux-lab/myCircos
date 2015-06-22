#!flask/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
import os.path

#################################################
#						#
#	             DATABASE			#
#						#
#################################################
db.create_all()
#creating database (only once)
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
  api.create(SQLALCHEMY_MIGRATE_REPO, 'db_repository')
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

#making sure we are using the latest version of our database
else: 
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLACHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
