drop table if exists statements cascade;
drop table if exists politicians cascade;
drop table if exists words_list cascade;
drop table if exists political_parties cascade;
drop table if exists political_parties_changes cascade;
drop table if exists political_meetings cascade;
drop table if exists chosen_words cascade;

CREATE TABLE if not exists politicians(
    id serial primary key not null,
    name VARCHAR(50) NOT NULL
);

create table if not exists political_meetings(
    date date not null primary key
);

CREATE table if not exists statements(
    id serial primary key not null,
    politician_id int not null references politicians(id),
    date date not null REFERENCES political_meetings(date)
);

CREATE table if not exists words_list(
    number int not null,
    base varchar(30) NOT NULL,
    variety varchar(30) NOT NULL,
    statement_id int not null references statements(id),
    primary key (statement_id, number)
);

create table if not exists political_parties(
    name varchar(20) not null primary key
);

create table if not exists political_parties_changes(
    id serial NOT NULL,
    date date not null,
    politician_id int not null references politicians(id),

    old_party varchar(20) references political_parties(name),
    new_party varchar(20) references political_parties(name)
);

create table if not exists chosen_words(
    base varchar(30) NOT NULL
);

create view full_statement as
    select statement_id, string_agg((select variety from words_list as words_list1 where wl.statement_id=words_list1.statement_id), ' ') as statement
    from words_list as wl
    group by statement_id;

create view full_base_statement as
    select statement_id, string_agg((select base from words_list as words_list1 where wl.statement_id=words_list1.statement_id), ' ') as statement
    from words_list as wl
    group by statement_id;

create index base_words_list on words_list using hash(base);
create index variety_words_list on words_list using hash(variety);