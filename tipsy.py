import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
  abort, render_template, flash
from contextlib import closing

DATABASE = '/tmp/tipsy.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def init_db():
  with closing(connect_db()) as db:
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

@app.before_request
def before_request():
  g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_inventory')
def add_inventory():
    cur = g.db.execute('select name from brands order by id desc')
    brands = [dict(name=row[0]) for row in cur.fetchall()]
    return render_template('add_inventory.html', brands=brands)

@app.route('/inventory')
def show_inventory():
    cur = g.db.execute('select name from brands order by id desc')
    brands = [dict(name=row[0]) for row in cur.fetchall()]
    return render_template('show_inventory.html', brands=brands)

@app.route('/add', methods=['POST'])
def add_brand():
    g.db.execute('insert into brands (name) values (?)',
                 [request.form['name']])
    g.db.commit()
    flash('New brand was successfully posted')
    return redirect(url_for('add_inventory'))

if __name__ == '__main__':
  app.run()
