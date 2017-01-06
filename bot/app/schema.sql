drop table if exists task_bill;
create table task_bill (
  id integer primary key autoincrement,
  session text not null,
  category text not null,
  description text null,
  currency text not null,
  payment DECIMAL(10,2) DEFAULT 0.00,
  "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);