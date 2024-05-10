-- ALTER USER postgres PASSWORD 'P@ssw0rd';
-- CREATE DATABASE datacenter ;
-- \c datacenter

-- Удалем старые таблицы
DROP TABLE IF EXISTS Clients;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Servers;
DROP TABLE IF EXISTS Active_Rents;
DROP TABLE IF EXISTS Support_tickets;
DROP TABLE IF EXISTS News;
CREATE TABLE Clients (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(30),
    client_surname VARCHAR(30),
    email VARCHAR(40), -- Добавить регекс проверки имейла 
    phone VARCHAR(15), -- Добавить регекс проверки телефона 
    password_hash VARCHAR(32) -- MD5
);
CREATE TABLE Employees (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(30),
    employee_surname VARCHAR(30),
    position VARCHAR(40),
    departmanet VARCHAR(25), 
    password_hash VARCHAR(32) -- MD5
);
-- Создем администратора
INSERT INTO Employees (employee_name, employee_surname, position, departmanet, password_hash)
VALUES ('Admin', 'Adminov', 'System Administrator', 'IT Department', '098f6bcd4621d373cade4e832627b4f6');
CREATE TABLE Servers (
    server_id SERIAL PRIMARY KEY,
    server_name VARCHAR(255),
    location VARCHAR(255),
    cpu INT,
    ram INT,
    disk INT,
    purchased BOOLEAN,
    rental_price INT
);
-- UPDATE Servers SET purchased = false; сделать все сервера не купленными
CREATE TABLE Active_Rents (
    rental_id SERIAL PRIMARY KEY,
    client_email VARCHAR(40) NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_price INT NOT NULL
);
-- DELETE FROM Active_Rents; Удалить все записи о рентах 
CREATE TABLE Support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    client_email VARCHAR(40) NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    employee_name VARCHAR(30),
    employee_surname VARCHAR(30),
    status VARCHAR(20),
    severity VARCHAR(20),
    ticket_name VARCHAR(50),
    ticket_payload VARCHAR(10000)
);
CREATE TABLE News (
    news_id SERIAL PRIMARY KEY,
    news_title VARCHAR(50),
    news_type VARCHAR(30),
    news_date DATE NOT NULL,
    news_data VARCHAR(10000)
);

-- Эта функция очищает таблицы  Active_Rents, Support_tickets и News и делает достуными для покупки все сервера
CREATE OR REPLACE FUNCTION Restore_mutable()
RETURNS VOID AS $$
BEGIN
    DELETE FROM Active_Rents;
    DELETE FROM Support_tickets;
    DELETE FROM News;
    UPDATE Servers SET purchased = false;
END;
$$ LANGUAGE plpgsql;

-- Вызов этой функции
-- SELECT Restore_mutable();

-- Добавление серверов 
DELETE FROM Servers;
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('MSK-1-2-20', 'Moscow', 1, 2, 20, FALSE, 300);
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('MSK-2-4-50', 'Moscow', 2, 4, 50, FALSE, 500);
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('MSK-4-8-100', 'Moscow', 4, 8, 100, FALSE, 1000);
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('NY-1-2-20', 'New York', 1, 2, 20, FALSE, 300);
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('NY-2-4-50', 'New York', 2, 4, 50, FALSE, 500);
INSERT INTO Servers (server_name, location, cpu, ram, disk, purchased, rental_price)
VALUES ('NY-4-8-100', 'New York', 4, 8, 100, FALSE, 1000);

