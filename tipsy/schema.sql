drop table if exists inventory;
create table inventory (
  id integer primary key autoincrement,
  name text unique not null,
  quantity integer not null,
  current real not null
);

drop table if exists liquor_db;
create table liquor_db (
  id integer primary key autoincrement,
  name text unique not null,
  UPC text unique not null,
  price real not null,
  full real not null,
  empty real not null
);

drop table if exists updates;
create table updates (
  id integer primary key autoincrement,
  name text not null,
  percent real not null
);
