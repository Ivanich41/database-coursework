from flask import Flask, render_template, request, redirect, url_for, make_response, session
import hashlib
import psycopg2
import os
import secrets
from datetime import datetime, timedelta

# Локлаьное тестирование 
# DB_NAME = "datacenter"
# DB_HOST = "localhost"
# DB_USER = "postgres"
# DB_PASSWORD = "P@ssw0rd"
# DB_PORT = "54320"

DB_NAME = "datacenter"
DB_HOST = "192.168.2.31"
DB_USER = "postgres"
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]
DB_PORT = "5432"


# Класс соединения с базой данных, чтобы каждый раз вызывать его при взаимодействиях
class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()



def md5_hash_string(string):
    """
    Хэширует строку в md5 и возвращает значение
    """
    string_bytes = string.encode('utf-8')
    md5_hash = hashlib.md5()
    md5_hash.update(string_bytes)
    hashed_string = md5_hash.hexdigest()
    
    return hashed_string

def find_email_by_session_id(session_id, sessions):
    """
    Находит email по session_id в словаре sessions.

    :param session_id: Идентификатор сессии.
    :param sessions: Словарь, где ключи - это email, а значения - это session_id.
    :return: Email, соответствующий session_id, или None, если не найден.
    """
    for key, value in sessions.items():
        if value == session_id:
            return key
    return None

#app init
app = Flask(__name__)
app.secret_key = 'SUP4R_SERCRET_K4Y'

@app.route("/", methods=["GET"])
def root():
    # Поиск куки в заголовках
    session_id = request.cookies.get('session_id', None)
    email = find_email_by_session_id(session_id,sessions)
    
    if session_id:
        print("Cookie found!")
    else:
        print("No cookie")
    return render_template("index.html", email=email )


@app.route('/login', methods=['GET'])
def login():
    session_id = request.cookies.get('session_id', None)
    email = find_email_by_session_id(session_id,sessions)
    return render_template('login.html',email=email)


@app.route('/submit-login', methods=['POST'])
def submit_login():
    email = request.form.get('email')
    password = md5_hash_string(request.form.get('password'))

    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM Clients WHERE email = %s", (email,))
        result = cur.fetchone()
        cur.close()

    if result:
       stored_password_hash = result[0] 

    if str(password) == str(stored_password_hash):
        # Если пароль совпадает, создаем cookie для сессии
        session_id = secrets.token_hex(16)
        sessions[email] = session_id
        response = make_response(render_template('login.html', message="Вход выполнен"))
        response.set_cookie('session_id', session_id) 
        return response
    else:
        # Если пароль не совпадает или пользователь не найден, возвращаем сообщение об ошибке
        return render_template('login.html', message="Неверный email или пароль")

@app.route("/register",methods=["GET"])
def register():
    return render_template("register.html")


@app.route('/submit-registration', methods=['POST'])
def submit_registration():
     # Получение данных из формы
    name = request.form.get('name')
    surname = request.form.get('surname')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = md5_hash_string(request.form.get('password'))

    # Оталдка 
    print('New user registred:')
    print(f"Name: {name}")
    print(f"Surname: {surname}")
    print(f"Phone: {phone}")
    print(f"Email: {email}")
    print(f"Password: {password}")

    # Проверка на сществванеие имейла в таблице
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Clients WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        cur.close()
        if existing_user:
            return render_template('register.html', message="Пользователь с таким адресом электронной почты уже зарегистрирован.")

    # Вставка данных в таблицу 
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        # Вставка данных в таблицу Clients
        cur.execute("INSERT INTO Clients (client_name, client_surname, email, phone, password_hash) VALUES (%s, %s, %s, %s, %s)",
                    (name, surname, email, phone, password))
        conn.commit()
        cur.close()
    
    return render_template('register.html', message="Регистрация прошла успешно!")

@app.route('/servers',methods=['GET'])
def servers():
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Servers WHERE purchased = FALSE")
        servers = cur.fetchall()
    # Отдельно забираем имена серверов для вывода в выпадающем списке
    server_names = [server[1] for server in servers]
    
    session_id = request.cookies.get('session_id')
    email = find_email_by_session_id(session_id,sessions)
    return render_template('servers.html', servers=servers, email=email, server_names=server_names)

@app.route('/purchase',methods=['GET'])
def purchase():
    # Проверка наличия куки 
    session_id = request.cookies.get('session_id', None)
    if not session_id:
        return "Error, user not found"
    
    selected_server = request.args.get('selectedServer', None)
    # Проверка что такой сервер существует в базе 
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT EXISTS(SELECT 1 FROM Servers WHERE server_name = %s)", (selected_server,))
        server_exists = cur.fetchone()[0]
        # Также запрашиваю цену для сервера 
        cur.execute("SELECT rental_price FROM Servers WHERE server_name = %s", (selected_server,))
        rental_price = cur.fetchone()[0]
        cur.close()
    if not server_exists:
        return "Сервер не найден", 404
    
    return render_template('purchase.html', selected_server=selected_server, rental_price=rental_price)

@app.route('/complete-purchase')
def complete_purchase():
    # получение аргументов и куки из запроса 
    session_id = request.cookies.get('session_id', None)
    selected_server = request.args.get('selectedServer', None)
    selected_duration = request.args.get('selectedDuration', None)

    email = find_email_by_session_id(session_id,sessions)
    
    selected_duration = int(selected_duration)
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        # беерем цену сервера для вычисления конечной стоимости
        cur.execute("SELECT rental_price FROM Servers WHERE server_name = %s", (selected_server,))
        rental_price = int(cur.fetchone()[0])
        cur.execute("UPDATE Servers SET purchased = true WHERE server_name = %s", (selected_server,))
        conn.commit()
        cur.close()

    total_price = rental_price * selected_duration
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=selected_duration*30)

    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Active_Rents (client_email, server_name, start_date, end_date, total_price) VALUES (%s, %s, %s, %s, %s)",
                (email, selected_server, start_date, end_date, total_price))
        conn.commit()
    
    # DEBUG
    #print(email, selected_server, selected_duration,rental_price, total_price)
    return render_template('purchase_confirmation.html', selected_server=selected_server, selected_duration=selected_duration, total_price=total_price, email=email)

@app.route('/cabinet')
def cabinet():
    session_id = request.cookies.get('session_id', None)
    email = find_email_by_session_id(session_id,sessions)
    if not email:
        return "Пользователь не вошел в систему.", 403
    
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Active_Rents WHERE client_email = %s", (email,))
        rents = cur.fetchall()
        cur.close()
    #print(rents)
    return render_template('cabinet.html', rents=rents, email=email)

@app.route('/support')
def send_ticket():
    session_id = request.cookies.get('session_id', None)
    email = find_email_by_session_id(session_id,sessions)
    if not email:
        return "Пользователь не вошел в систему.", 403
    
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Support_tickets WHERE client_email = %s", (email,))
        tickets = cur.fetchall()
        cur.execute("SELECT server_name FROM Active_rents WHERE client_email = %s", (email,))
        user_servers = cur.fetchall()
        cur.close()
    user_servers = [server[0].replace('(', '').replace(')', '').replace(',', '') for server in user_servers]
    print(tickets)
    print(user_servers)
    return render_template('support.html', tickets=tickets, email=email, user_servers=user_servers)

@app.route('/submit-ticket', methods=['POST'])
def submit_ticket():
    session_id = request.cookies.get('session_id', None)
    email = find_email_by_session_id(session_id,sessions)

    server_name = request.form.get('server_name')
    ticket_name = request.form.get('ticket_name')
    ticket_payload = request.form.get('ticket_payload')

    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Support_tickets (client_email, server_name, ticket_name, ticket_payload, status) VALUES (%s, %s, %s, %s, %s)",
                    (email, server_name, ticket_name, ticket_payload, "OPEN"))
        conn.commit()
        cur.close()
    return redirect(url_for('ticket_submitted'))

@app.route('/ticket-submitted')
def ticket_submitted():
    return render_template('ticket_submitted.html')

@app.route('/admin')
def admin():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    return render_template('admin_login.html', id_number=id_number)

@app.route('/admin-login-submit',methods=['POST'])
def submit_admin_login():
    id = request.form.get('id')
    password = md5_hash_string(request.form.get('password'))
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM Employees WHERE employee_id = %s", (id,))
        result = cur.fetchone()
        cur.close()

    if result:
       stored_password_hash = result[0] 

    if str(password) == str(stored_password_hash):
        # Если пароль совпадает, создаем cookie для сессии
        admin_id = secrets.token_hex(16)
        admin_sessions[id] = admin_id
        response = make_response(render_template('admin_login.html', message="Вход выполнен"))
        response.set_cookie('admin_id', admin_id) 
        return response
    else:
        # Если пароль не совпадает или пользователь не найден, возвращаем сообщение об ошибке
        return render_template('admin_login.html', message="Неверный id или пароль")

@app.route('/admin-cabinet')
def admin_cabinet():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Вход администатора не выполнен", 403
    return render_template('admin_cabinet.html',id_number=id_number)

@app.route('/admin-tickets')
def admin_tickets():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Вход администатора не выполнен", 403
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        # Получаем все открытые тикеты
        cur.execute("SELECT * FROM support_tickets WHERE status = %s", ("OPEN",))
        opened_tickets = cur.fetchall()
        opened_ticket_names = [ticket[7] for ticket in opened_tickets]
        #print(opened_tickets[0][0])
        # Получаем информацию о залогиненом администраторе
        cur.execute("SELECT employee_name,employee_surname FROM employees WHERE employee_id = %s", (id_number,))
        admin_data = cur.fetchone()
        admin_name =admin_data[0]
        admin_surname = admin_data[1]
        # Получе=аем информацию об открытых тикетов для этого администратора
        cur.execute("SELECT * FROM support_tickets WHERE status = %s AND employee_name = %s AND employee_surname = %s", ("IN PROGRESS",admin_name,admin_surname))
        my_tickets = cur.fetchall()

    return render_template('admin-tickets.html',id_number = id_number, opened_tickets=opened_tickets, my_tickets = my_tickets, opened_ticket_names = opened_tickets)

@app.route('/admin-tickets-get')
def admin_tickets_get():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Адмиинистратор на вошёл", 403
    selected_ticket_id =  request.args.get('openedTicketID')
    severity = request.args.get('severity')

    with DatabaseConnection() as conn: 
        cur = conn.cursor()
        # Получаем информацию о залогиненом администраторе
        cur.execute("SELECT employee_name,employee_surname FROM employees WHERE employee_id = %s", (id_number,))
        admin_data = cur.fetchone()
        admin_name =admin_data[0]
        admin_surname = admin_data[1]
        # Выставляем статус In Progress для взятого тикета и выставляем ФИ админа, который его взял
        print(severity,admin_name,admin_surname,selected_ticket_id)
        cur.execute("""
        UPDATE Support_tickets
        SET status = 'IN PROGRESS', severity = %s, employee_name = %s, employee_surname = %s
        WHERE ticket_id = %s
        """, (severity, admin_name, admin_surname, selected_ticket_id))
        conn.commit()
        cur.close()

    return render_template('ticket_proceed.html',render_type='accepted')

@app.route('/admin-tickets-close')
def admin_tickets_close():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Адмиинистратор на вошёл", 403
    selected_ticket_id =  request.args.get('myTicketID')

    with DatabaseConnection() as conn: 
        cur = conn.cursor()
        # Выставляем статус CLOSED для выбранного тикета 
        cur.execute("""
        UPDATE Support_tickets
        SET status = 'CLOSED' 
        WHERE ticket_id = %s
        """, (selected_ticket_id,))
        conn.commit()
        cur.close
    
    return render_template('ticket_proceed.html',render_type='closed')

@app.route('/write-news')
def write_news():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Адмиинистратор на вошёл", 403
    
    return render_template("write_news.html", id_number = id_number)

@app.route('/write-news-done', methods=['POST'])
def write_news_done():
    admin_id = request.cookies.get('admin_id', None)
    id_number = find_email_by_session_id(admin_id,admin_sessions)
    if not id_number:
        return "Адмиинистратор на вошёл", 403
    news_title = request.form.get('news-title')
    news_text = request.form.get('news-text')
    news_type = request.form.get('news-type')
    if news_type == "danger":
        news_type = "Авария"
    elif news_type == "maintenance":
        news_type = "Техническое обслуживание"
    elif news_type == "info":
        news_type = "Информация"
    elif news_type == "discount":
        news_type = "Скидка"
    else:
        return "Неправильный тип новости, я чайник", 418
    news_date = datetime.now().date()
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        # Создаем новую новость с полученными параметрами
        cur.execute("""
        INSERT INTO News (news_title, news_type, news_date, news_data)
        VALUES (%s,%s,%s,%s)
        """,(news_title,news_type,news_date,news_text))
        conn.commit()
        cur.close()

    return render_template("write_news_done.html")

@app.route('/news')
def news():
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM News")
        newslist = cur.fetchall()

    return render_template('news.html', newslist=newslist)

if __name__ == "__main__":
    # Словари sessions и admin_sessions содержат списки с cookie для обычных 
    # пользователей и администраторов. Они используются чтобы матчить куки 
    # id пользователя, см функцию find_email_by_session_id.
    # В sessions ключом является email, в admin_serssions employee_id
    sessions = { "example" : "example"}
    admin_sessions = { "admin": "admin" }
    app.run(debug=True, host="0.0.0.0")
