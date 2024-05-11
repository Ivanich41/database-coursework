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
DROP TABLE IF EXISTS audit_log;

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
    ticket_payload VARCHAR(10000),
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE News (
    news_id SERIAL PRIMARY KEY,
    news_title VARCHAR(50),
    news_type VARCHAR(30),
    news_date DATE NOT NULL,
    news_data VARCHAR(10000)
);
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(255),
    action_type VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Этот триггер обнолвяет знаечние поля last_modified при изменении значения
DELIMITER //
CREATE TRIGGER update_last_modified_on_status_change
AFTER UPDATE ON Support_tickets
FOR EACH ROW
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        UPDATE Support_tickets SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END IF;
END; //
DELIMITER ;

-- Следующие 5 триггеров записывают информациии об изменениях в таблицах Clients, Employees, 
-- Servers, Active_rents и Support_tickets в отдельную таблицу audit_log
CREATE TRIGGER log_client_changes
AFTER INSERT OR UPDATE OR DELETE ON Clients
FOR EACH ROW
BEGIN
    IF OLD.id IS NOT NULL THEN
        INSERT INTO audit_log (table_name, action_type, old_value, new_value)
        VALUES ('Clients', 'UPDATE', OLD.name, NEW.name);
    ELSE
        INSERT INTO audit_log (table_name, action_type, new_value)
        VALUES ('Clients', 'INSERT', NEW.name);
    END IF;
END;

CREATE TRIGGER log_employee_changes
AFTER INSERT OR UPDATE OR DELETE ON Employees
FOR EACH ROW
BEGIN
    IF OLD.id IS NOT NULL THEN
        INSERT INTO audit_log (table_name, action_type, old_value, new_value)
        VALUES ('Employees', 'UPDATE', OLD.name, NEW.name);
    ELSE
        INSERT INTO audit_log (table_name, action_type, new_value)
        VALUES ('Employees', 'INSERT', NEW.name);
    END IF;
END;

CREATE TRIGGER log_servers_changes
AFTER INSERT OR UPDATE OR DELETE ON Servers
FOR EACH ROW
BEGIN
    IF OLD.id IS NOT NULL THEN
        INSERT INTO audit_log (table_name, action_type, old_value, new_value)
        VALUES ('Servers', 'UPDATE', OLD.name, NEW.name);
    ELSE
        INSERT INTO audit_log (table_name, action_type, new_value)
        VALUES ('Servers', 'INSERT', NEW.name);
    END IF;
END;

CREATE TRIGGER log_rents_changes
AFTER INSERT OR UPDATE OR DELETE ON Active_rents
FOR EACH ROW
BEGIN
    IF OLD.id IS NOT NULL THEN
        INSERT INTO audit_log (table_name, action_type, old_value, new_value)
        VALUES ('Active rents', 'UPDATE', OLD.name, NEW.name);
    ELSE
        INSERT INTO audit_log (table_name, action_type, new_value)
        VALUES ('Active rents', 'INSERT', NEW.name);
    END IF;
END;

CREATE TRIGGER log_tickets_changes
AFTER INSERT OR UPDATE OR DELETE ON Support_tickets
FOR EACH ROW
BEGIN
    IF OLD.id IS NOT NULL THEN
        INSERT INTO audit_log (table_name, action_type, old_value, new_value)
        VALUES ('Support tickets', 'UPDATE', OLD.name, NEW.name);
    ELSE
        INSERT INTO audit_log (table_name, action_type, new_value)
        VALUES ('Support tickets', 'INSERT', NEW.name);
    END IF;
END;

-- Этот триггер предотвращает создание пользователей с одинаковыми имейлами 
CREATE TRIGGER check_user_email_uniqueness
BEFORE INSERT ON Clients
FOR EACH ROW
BEGIN
    DECLARE email_exists BOOLEAN;
    SELECT EXISTS(SELECT 1 FROM Clients WHERE email = NEW.email) INTO email_exists;
    IF email_exists THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email must be unique.';
    END IF;
END;