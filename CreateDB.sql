drop table if exists "User" cascade;
drop table if exists "Order" cascade;
drop table if exists "Address" cascade;
drop table if exists "Goods" cascade;
drop table if exists "Comment" cascade;

create table "User"
(
    id        serial4 primary key not null,
    username  varchar(255)        not null unique,
    password  varchar(255)        not null,
    create_at timestamp default current_timestamp
);

create table "Address"
(
    id       serial4 primary key not null,
    user_id  int4,
    name     varchar(255),
    phone    varchar(255),
    location varchar(255),
    foreign key (user_id) references "User" (id) on delete restrict
);

create table "Goods"
(
    id             serial4 primary key not null,
    name           varchar(255),
    description    varchar(255),
    img            varchar(255),
    price          decimal(10, 2),
    owner          int4,
    exempt_postage boolean,
    foreign key (owner) references "User" (id) on delete restrict
);

create table "Comment"
(
    id        serial4 primary key not null,
    user_id   int4,
    goods_id  int4,
    content   varchar(1024),
    create_at timestamp default current_timestamp,
    foreign key (user_id) references "User" (id) on delete restrict,
    foreign key (goods_id) references "Goods" (id) on delete restrict
);

create table "Order"
(
    id              serial4 primary key not null,
    user_id         int4,
    goods_id        int4,
    state           int4,
    address_id      int4,
    express_code    varchar(255),
    express_company varchar(255),
    foreign key (user_id) references "User" (id) on delete restrict,
    foreign key (goods_id) references "Goods" (id) on delete restrict,
    foreign key (address_id) references "Address" (id) on delete restrict
);