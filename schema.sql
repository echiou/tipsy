drop table if exists brands;
create table brands (
  id integer primary key autoincrement,
  name text not null
);

drop table if exists updates;
create table updates (
  id integer primary key autoincrement,
  UPC text not null,
  weight text not null
);
