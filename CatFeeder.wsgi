import os, sys
 
activate_this = '/var/www/CatFeeder/catenv/bin/activate_this.py'
#execfile(activate_this, dict(__file__=activate_this))
exec(compile(open(activate_this, "rb").read(), activate_this, 'exec'))

sys.path.append('/var/www/CatFeeder')
 
from app import app as application

home='/var/www/CatFeeder'
