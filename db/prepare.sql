ALTER USER postgres PASSWORD 'P@ssw0rd';
CREATE DATABASE datacenter ;
\c datacenter
-- Вначале идут таблицы с пользователями, это учётки клиентов и сотрудников 
CREATE TABLE Clients (
    client_id INT PRIMARY KEY,
    client_name VARCHAR(30),
    client_surname VARCHAR(30),
    email VARCHAR(40), -- Добавить регекс проверки имейла 
    phone VARCHAR(15), -- Добавить регекс проверки телефона 
    password_hash VARCHAR(32) -- MD5
);

