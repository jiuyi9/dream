DROP TABLE IF EXISTS t_user;

CREATE TABLE t_user (
    id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(64),
    age   INT,
    email VARCHAR(128)
);