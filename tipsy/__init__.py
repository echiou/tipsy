import sqlite3
import re
from flask import Flask, Response, request, session, g, redirect, url_for, \
  abort, render_template, flash, stream_with_context
from contextlib import closing
from flask.ext.bower import Bower

DATABASE = '/tmp/tipsy.db'
DEBUG = False
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

#(name, UPC, price, full, empty)
liquor_db_prepopulate = [("Maker's Mark", '085246139431', 12.5,2.7,0.7),
                          ('Woodford Reserve', '081128031473', 8.0,0.9,0.5)]

app = Flask(__name__)
app.config.from_object(__name__)

Bower(app)

def init_db():
  with closing(connect_db()) as db:
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    for liquor in liquor_db_prepopulate:
      db.execute('insert into liquor_db (name, UPC, price, full, empty) values (?, ?, ?, ?, ?)',
                 [liquor[0], liquor[1], liquor[2], liquor[3], liquor[4]])
    db.commit()

@app.before_request
def before_request():
  g.db = connect_db()
  g.db.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

import tipsy.views

if __name__ == '__main__':
  app.run(host='0.0.0.0')
