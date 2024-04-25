from flask import Flask, render_template, request
import hashlib
import psycopg2
import os

DB_NAME = "datacenter"
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "P@ssw0rd" # Заменить на Environ

#app init
app = Flask(__name__)

def md5_hash_string(string):
    string_bytes = string.encode('utf-8')
    md5_hash = hashlib.md5()
    md5_hash.update(string_bytes)
    hashed_string = md5_hash.hexdigest()
    
    return hashed_string

@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/submit-login', methods=['POST'])
def submit_login():
    email = request.form.get('email')
    password = md5_hash_string(request.form.get('password'))
    #TODO Тут сделать сравнение хэшей пароя
    return render_template('login.html', message="Вход выполнен")


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
    print(f"Name: {name}")
    print(f"Surname: {surname}")
    print(f"Phone: {phone}")
    print(f"Email: {email}")
    print(f"Password: {password}")

    #TODO Сделать запись этих данных в таблицу
    return render_template('register.html', message="Регистрация прошла успешно!")

if __name__ == "__main__":
    try:
        connection = psycopg2.connect(dbname=DB_NAME, host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port="54320")
        print(" * DB connected")
    except:
        print("PostgreSQL connection error!")
    #connection.close()
    app.run(debug=False)
