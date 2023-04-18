

create table if not exists course_group (
  name text primary key
);

create table if not exists course_group_course (
  group_name text,
  course_name text,
  primary key (group_name, course_name),
  foreign key (group_name)
    references course_group (name)
      on delete cascade
      on update cascade
);

create table if not exists tee_time_search (
  id uuid primary key,
  notification_method text,
  notification_destination text_list,
  search_params tee_time_search_params
);

create table if not exists tee_time_search_result (
  search_id uuid,
  "tee_time" tee_time,
  primary key (search_id, "tee_time"),
  foreign key (search_id)
    references tee_time_search (id)
      on delete cascade
      on update cascade
);