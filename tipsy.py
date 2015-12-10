import sqlite3
import re
from flask import Flask, request, session, g, redirect, url_for, \
  abort, render_template, flash
from contextlib import closing
from flask.ext.bower import Bower

DATABASE = '/tmp/tipsy.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

liquor_db_prepopulate = [('a', '111', 12.5,13.0,2.0),
                          ('b', '222', 15.0,12.0,2.3),
                          ('c', '333', 14.5,11.2,2.3)]

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

@app.route('/')
def index():
    cur = g.db.execute('select name, percent from updates order by id desc')
    updates = [dict(name=row[0], percent=row[1]) for row in cur.fetchall()]
    return render_template('index.html', updates=updates)

@app.route('/add_inventory')
def add_inventory():
    return render_template('add_inventory.html')

@app.route('/add_liquor')
def add_liquor():
    return render_template('add_liquor.html')

@app.route('/mark_empty')
def mark_empty():
    return render_template('mark_empty.html')

@app.route('/inventory')
def show_inventory():
    cur = g.db.execute('select name, quantity, current from inventory order by id desc')
    inventory = [dict(name=row[0], quantity=row[1], current=row[2]) for row in cur.fetchall()]
    return render_template('show_inventory.html', inventory=inventory)

@app.route('/liquor')
def show_liquor():
    cur = g.db.execute('select name, UPC, price, full, empty from liquor_db order by id desc')
    liquor = [dict(name=row[0], UPC=row[1], price=row[2], full=row[3], empty=row[4]) for row in cur.fetchall()]
    return render_template('show_liquor.html', liquor=liquor)

@app.route('/add_inventory', methods=['POST'])
def add_to_inventory():
    brand = request.form['name']
    quantity = request.form['quantity']
    g.db.execute('insert into inventory (name, quantity, current) values (?, ?, ?)',
                 [brand, quantity, quantity])
    g.db.commit()
    flash(re.escape(quantity + ' bottles of ' + brand + ' added.'), 'success')
    return redirect(url_for('add_to_inventory'))

@app.route('/add_liquor', methods=['POST'])
def add_to_liquor_db():
  brand = request.form['name']
  g.db.execute('insert into liquor_db (name, UPC, price, full, empty) values (?, ?, ?, ?, ?)',
      [brand, request.form['upc'], request.form['price'], request.form['full'], request.form['empty']])
  g.db.commit()
  flash(re.escape(brand + ' added to liquor database'), 'success')
  return redirect(url_for('add_liquor'))

@app.route('/update', methods=['POST'])
def update_inventory():
    UPC, weight = request.form['UPC'], request.form['weight']
    record = g.db.execute('select * from liquor_db where UPC= ?',
                [UPC]).fetchall()[0]
    name = record['name']
    percent = (float(weight) - record['empty']) / (record['full'] - record['empty'])
    g.db.execute('insert into updates (name, percent) values (?, ?)',
                [name, percent])
    g.db.commit()
    flash('brand was successfully updated')
    return redirect(url_for('index'))
if __name__ == '__main__':
  app.run(host='0.0.0.0')
