from flask import Flask, render_template, request, session, redirect, jsonify
import mariadb
import bcrypt

app = Flask(__name__)

# trenger for sessions
app.secret_key = "test123"

# sender bruker til errorsider hvis den ikke finner siden
@app.errorhandler(404)
def not_found(skibidi):
    return render_template("404.html")


# lager database i sqlite
def create_table():
    conn = mariadb.connect(
        host="10.2.2.11",
        username="admin",
        password="admin",
        database="users"
        )
    cursor = conn.cursor()
    sql = "CREATE TABLE IF NOT EXISTS users (username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user')"
    cursor.execute(sql)
    conn.commit()
    conn.close()

#test db er commenta ut fordi den lager brukere med uhasha passord som ikke virker fordi log in siden forventer hasha passord.
    
#def test_db():
#    conn = mariadb.connect(
#        host="10.2.2.11",
#        username="admin",
#        password="admin",
#        database="users"
#        )
#    cursor = conn.cursor()
#    sql = "INSERT INTO users (username, password) VALUES ('jadjns', 'password')"
#    cursor.execute(sql)
#    sql = "INSERT INTO users (username, password) VALUES ('hello', 'jdsnjcn')"
#    cursor.execute(sql)
#    sql = "INSERT INTO users (username, password) VALUES ('jarvis', 'hello')"
#    cursor.execute(sql)
#    sql = "INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')"
#    cursor.execute(sql)
#    conn.commit()
#    conn.close()
    
create_table()
#test_db()

# tar i mot passord og returnerer hasha passord
def hash_password(password):
    password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt())

# sender variabler til hver html side
@app.context_processor
def current_user():
    return dict(username=session.get("username"), role=session.get("role"))

@app.route('/')
def root():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

def login_user(username, password):
    conn = mariadb.connect(
        host="10.2.2.11",
        username="admin",
        password="admin",
        database="users"
        )
    cursor = conn.cursor() 
    sql = "SELECT * FROM users WHERE username = ?"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    if result:
        hash = result[1]
        if bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8')):
            session["username"]=username
            session["role"]=result[2]
            conn.close()
            return render_template("home.html", message=username)
        else:
            return render_template("home.html", message="ERROR: wrong password entered")
    else:
        conn.close()

        return render_template("home.html", message=f"Bruker med navn '{username}' ikke funnet.")
    
def registrer_user(username, password, role):
    password = hash_password(password)
    # conn = mariadb.connect(
    #     host="10.2.2.11",
    #     username="admin",
    #     password="admin",
    #     database="users"
    #     )
    # cursor = conn.cursor()
    # if role == "admin":
    #     sql = "INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')"
    # else:
    #     sql = "INSERT INTO users (username, password) VALUES (?, ?)"
    # cursor.execute(sql, (username, password))

    try:
        conn = mariadb.connect(
            host="10.2.2.11",
            username="admin",
            password="admin",
            database="users"
        )
        cursor = conn.cursor()

        if role == "admin":
            sql = "INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')"
        else:
            sql = "INSERT INTO users (username, password) VALUES (?, ?)"
        cursor.execute(sql, (username, password))
        conn.commit()
        return render_template("home.html", message=f"Bruker med navn '{username}' er registrert."), 201

    except mariadb.IntegrityError as e:
        if e.errno == 1062:  # Duplicate entry (UNIQUE constraint failed)
            return render_template("register.html", message = "Brukernavnet er i bruk. Prøv ett anent ett."), 500



    finally:
        cursor.close()
        conn.close()
    
    # message = f"Brukeren {username} ble registrert."
    # try:
    #     conn.commit()
    # except mariadb.IntegrityError as e:
    #     message = "funka ikke"
    # except mariadb.Error as e:
    #     message = "funka ikke"
    # finally:
    #     try:
    #         conn.close()
    #         return render_template("home.html", message=message)
    #     except:
    #         pass



# get requests, bruker ber om side. post request bruker sender data
@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        return login_user(username, password)

@app.route('/register', methods=['POST', 'GET'])
def register_page():
    if request.method == "GET":
        return render_template('register.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        return registrer_user(username, password, role)

@app.route("/admin")
def admin_page():
    if session["role"] == "admin":
        conn = mariadb.connect(
        host="10.2.2.11",
        username="admin",
        password="admin",
        database="users"
        )
        cursor = conn.cursor() 
        sql = "SELECT * FROM users"
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return render_template("admin.html", users = result)
    else:
        return render_template('home.html',
        message="ERROR: har ikke tillatesle til å se siden."), 401	

@app.route("/profile")
def profile():
    if session["username"]:
        return render_template("profile.html", username = session["username"])
    else:
        return render_template('home.html', message="ERROR: er ikke logget in.")

@app.route("/logout")
def logout_user():
    session.pop("username")
    session.pop("role")
    return redirect("/login")

if __name__ == '__main__':
    app.run(debug=True, port=2000, host='0.0.0.0')