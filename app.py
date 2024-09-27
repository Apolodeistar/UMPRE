from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://usuario:contraseña@localhost/examenes_db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Resultado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), db.ForeignKey('user.cedula'), nullable=False)
    archivo = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inicializa la base de datos
@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(cedula='123456789').first():
        new_user = User(cedula='123456789', password='contraseña123')
        db.session.add(new_user)
        db.session.commit()

# Rutas
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form['cedula']
        password = request.form['password']
        user = User.query.filter_by(cedula=cedula).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('subir_resultado'))  # Redirige a subir resultados
        flash('Credenciales incorrectas.')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/subir_resultado', methods=['GET', 'POST'])
@login_required
def subir_resultado():
    if request.method == 'POST':
        cedula = request.form['cedula']
        archivo = request.files['archivo']
        archivo.save(f'static/resultados/{archivo.filename}')
        resultado = Resultado(cedula=cedula, archivo=archivo.filename)
        db.session.add(resultado)
        db.session.commit()
        flash('Resultado subido exitosamente.')
        return redirect(url_for('subir_resultado'))  # Redirige nuevamente a la misma página
    return render_template('subir_resultado.html')

@app.route('/ver_resultados', methods=['GET', 'POST'])
def ver_resultados():
    resultados = None
    if request.method == 'POST':
        cedula = request.form['cedula']
        resultados = Resultado.query.filter_by(cedula=cedula).all()
        if not resultados:
            flash('No se encontraron resultados para esta cédula.')
    return render_template('ver_resultados.html', resultados=resultados)

@app.route('/resultados/<cedula>')
def resultados(cedula):
    resultados = Resultado.query.filter_by(cedula=cedula).all()
    return render_template('resultados.html', resultados=resultados)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)











#mysql para xampp


-- Crear tabla User
CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

-- Crear tabla Resultado
CREATE TABLE Resultado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL,
    archivo VARCHAR(100) NOT NULL,
    FOREIGN KEY (cedula) REFERENCES User(cedula)
);
