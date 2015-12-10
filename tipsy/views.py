import sqlite3
import re
from flask import Flask, Response, request, session, g, redirect, url_for, \
  abort, render_template, flash, stream_with_context
from contextlib import closing
from flask.ext.bower import Bower
from tipsy import app

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

@app.route('/confirm_updates')
def confirm_updates():
    cur = g.db.execute('select name, percent from updates order by id desc')
    updates_to_commit = {}
    for update in cur.fetchall():
      name = update['name']
      percent = update['percent']
      record = g.db.execute('select * from inventory where name= ?',
                [name]).fetchall()[0]
      if record:
        if percent < 0:
          if name in updates_to_commit:
            updates_to_commit[name][1] -= percent
          else:
            updates_to_commit[name] = [0, -percent]
        else:
          if name in updates_to_commit:
            updates_to_commit[name][0] += (1-percent)
          else:
            updates_to_commit[name] = [1-percent, 0]

    for name, update in updates_to_commit.iteritems():
      old_record = g.db.execute('select * from inventory where name=?', [name]).fetchall()[0]
      new_quantity = old_record['quantity'] - update[1]
      if new_quantity == 0:
          g.db.execute('delete from inventory where name=?', [name])
      else:
          g.db.execute('update inventory set current=?, quantity=? where name=?',
                       [old_record['current'] - update[0] - update[1], new_quantity, name])
    g.db.execute('delete from updates')
    g.db.commit()
    flash('Inventory updated.', 'success')
    return redirect(url_for('index'))

@app.route('/export.csv')
def generate_csv():
    def generate():
        for row in g.db.execute('select * from inventory').fetchall():
            new_row = []
            for member in row:
                new_row.append(str(member))
            yield ','.join(new_row) + '\n'
    return Response(stream_with_context(generate()), mimetype='text/csv')

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

@app.route('/mark_empty_bottles', methods=['POST'])
def mark_empty_bottles():
    brand = request.form['name']
    int_quantity = request.form['quantity']
    quantity = -float(int_quantity)
    g.db.execute('insert into updates(name, percent) values(?, ?)',
                 [brand, quantity])
    g.db.commit()
    flash(re.escape(str(int_quantity) + ' bottles of ' +  brand + ' marked as empty'), 'success')
    return redirect(url_for('mark_empty'))

