create table timer (
  id int NOT NULL auto_increment,
  user_id bigint NOT NULL,
  server_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  end_date datetime NOT NULL,
  duration int(5) NOT NULL,
  break_duration int(5) NOT NULL,
  timer_type varchar(15) NOT NULL,
  status boolean NOT NULL,
  constraint timer_pk primary key (id),
  foreign key (user_id) references user(id),
  unique key(id)
);


create table user(
  id bigint NOT NULL,
  role varchar(10),
  total_studied_time int(7),
  total_worked_time int(7),

  constraint user_pk primary key (id),
  unique key(id)

);

create table servers ( /*the name has to be server but, "server" is a reserved word :) */
  id bigint NOT NULL,
  prefix varchar(5) NOT NULL default '&',
  sw_roles_settings boolean NOT NULL default 0,
  auto_reset boolean NOT NULL default 0,
  next_reset datetime ,
  reset_period int,
  time_zone int default 0,
  logs_channel_id bigint ,
  total_studied_time bigint NOT NULL DEFAULT 0,
  total_worked_time bigint NOT NULL DEFAULT 0,
  leveling tinyint(1) default 0,
  level_1 int,
  level_2 int,
  level_3 int,
  level_4 int,


  constraint servers_pk primary key (id),
  unique key(id)
);




create table user_servers(
  user_id bigint NOT NULL,
  server_id bigint NOT NULL,
  server_studied_time int(7) NULL DEFAULT 0,
  server_worked_time int(7) NULL DEFAULT 0,
  goal int(7),


  foreign key (server_id) references servers(id),
  foreign key (user_id) references user(id)
);
