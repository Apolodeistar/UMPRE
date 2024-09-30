from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://usuario:contraseña@localhost/examenes_db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # doctor o paciente

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
        new_doctor = User(cedula='123456789', password='contraseña123', role='doctor')
        new_paciente = User(cedula='987654321', password='contraseña456', role='paciente')
        db.session.add(new_doctor)
        db.session.add(new_paciente)
        db.session.commit()

# Rutas
@app.route('/')
def home():
    return render_template('index.html')
#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form['cedula']
        password = request.form['password']
        user = User.query.filter_by(cedula=cedula).first()

        if user and user.password == password:
            login_user(user)  # Autentica al usuario

            # Verifica el rol y redirige según el rol del usuario
            if user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.role == 'paciente':
                return redirect(url_for('paciente_dashboard'))

        flash('Credenciales incorrectas.')
    
    return render_template('login.html')
#dashboard de doctores
@app.route('/dashboard/doctor')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('403'))
    return render_template('dashboard_doctor.html')
#dashboard de pacientes
@app.route('/dashboard/paciente')
@login_required
def paciente_dashboard():
    if current_user.role != 'paciente':
        return redirect(url_for('403'))
    return render_template('dashboard_paciente.html')



# Solo los doctores pueden subir resultados
@app.route('/subir_resultado', methods=['GET', 'POST'])
@login_required
def subir_resultado():
    if current_user.role != 'doctor':
        return redirect(url_for('403'))  

    if request.method == 'POST':
        cedula = request.form['cedula']
        archivo = request.files['archivo']
        archivo.save(f'static/resultados/{archivo.filename}')
        resultado = Resultado(cedula=cedula, archivo=archivo.filename)
        db.session.add(resultado)
        db.session.commit()
        flash('Resultado subido exitosamente.')
        return redirect(url_for('subir_resultado'))

    return render_template('subir_resultado.html')

@app.route('/ver_resultados', methods=['GET', 'POST'])
@login_required
def ver_resultados():
    resultados = None
    if request.method == 'POST':
        cedula = request.form['cedula']
        resultados = Resultado.query.filter_by(cedula=cedula).all()
        if not resultados:
            flash('No se encontraron resultados para esta cédula.')
    return render_template('ver_resultados.html', resultados=resultados)
#solo los doctores pueden editar los resultados
@app.route('/editar_resultado/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_resultado(id):
    if current_user.role != 'doctor':
        return redirect(url_for('403'))  # Solo los doctores pueden editar resultados
    
    resultado = Resultado.query.get_or_404(id)
    
    if request.method == 'POST':
        archivo = request.files['archivo']
        archivo.save(f'static/resultados/{archivo.filename}')
        resultado.archivo = archivo.filename  # Actualiza el archivo en la base de datos
        db.session.commit()
        flash('Resultado actualizado exitosamente.')
        return redirect(url_for('ver.resultados.html'))

    return render_template('editar_resultado.html', resultado=resultado)
#solo los doctores pueden eliminar los documentos 
@app.route('/eliminar_resultado/<int:id>', methods=['POST'])
@login_required
def eliminar_resultado(id):
    if current_user.role != 'doctor':
        return redirect(url_for('403'))  # Solo los doctores pueden eliminar
    
    resultado = Resultado.query.get_or_404(id)
    db.session.delete(resultado)
    db.session.commit()
    flash('Resultado eliminado exitosamente.')
    return redirect(url_for('ver_resultados'))
#cierre de sesion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index.html'))

@app.route('/403')
def acceso_denegado():
    return render_template('403.html')

if __name__ == '__main__':
    app.run(debug=True)
