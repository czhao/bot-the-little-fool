CREATE TABLE IF NOT EXISTS task_bill (
  id integer primary key autoincrement,
  session text not null,
  category text not null,
  description text null,
  currency text not null,
  payment DECIMAL(10,2) DEFAULT 0.00,
  "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_subscription (
  id integer primary key autoincrement,
  uid text not null,
  subscription text not null,
  timing text not null,
  "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bus_stop (
  id integer primary key autoincrement,
  code text not null,
  road_name text not null,
  description text not null,
  lat float,
  lng float
);