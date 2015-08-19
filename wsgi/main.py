# -*- coding: utf-8 -*-

# Flask functionals Imports
from flask import Flask, render_template, request
from flask import redirect, url_for, session
from functools import wraps
from werkzeug import secure_filename

# DB ORM Imports
from flask_sqlalchemy import SQLAlchemy

# Form, and Form Validators Imports
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators, HiddenField, TextAreaField, BooleanField
from wtforms.validators import Required, EqualTo, Optional, Length, Email, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField

# Login Imports 
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
import os

# Mail Imports
from itsdangerous import URLSafeTimedSerializer
from flask.ext.mail import Mail, Message

# Global Vars
global filepath

# Excel File Imports
from openpyxl import load_workbook
import zipfile

mail = Mail()
application = Flask(__name__)

# upload reports config
application.config['UPLOAD_FOLDER'] = os.environ.get('OPENSHIFT_DATA_DIR') if os.environ.get('OPENSHIFT_DATA_DIR') else 'wsgi/static/patterns'

# cloud and local db
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('OPENSHIFT_POSTGRESQL_DB_URL') if os.environ.get('OPENSHIFT_POSTGRESQL_DB_URL') else 'postgres://lomelisan:6c6f6d656c69@localhost:5432/reporta'
application.config['CSRF_ENABLED'] = True
application.config['SECRET_KEY'] = 'esunsecreto'
application.config['SECURITY_PASSWORD_SALT'] = 'esunsecreto'

# login config
login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = '/signin'

# mail config
application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USE_SSL'] = True
application.config['MAIL_USERNAME'] = 'reporta.movilnet@gmail.com'
application.config['MAIL_PASSWORD'] = 'esunsecreto'
application.config['MAIL_DEFAULT_SENDER'] = 'reporta-movilnet@gmail.com'

db = SQLAlchemy(application)
mail.init_app(application)

# Global vars
global filepath
application.config['PATTERNS_FOLDER'] = 'wsgi/static/patterns'



# DB Models
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    name = db.Column(db.String(40))
    password = db.Column(db.String)
    email = db.Column(db.String(100), unique=True)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(20))
    

    active = db.Column(db.Boolean)
    
    def __init__(self, username = None, password = None, email = None,
    firstname = None, lastname = None, confirmed = None
    , role = None, active = None):
        self.username = username
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.confirmed = confirmed
        self.role = role
        self.active = active
        
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active
    
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
	


#Token Generator
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(application.config['SECRET_KEY'])
    return serializer.dumps(email, salt=application.config['SECURITY_PASSWORD_SALT'])

#Confirm Token
def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(application.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=application.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

#Send Email
def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=application.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)
    
#Send Email File
def send_email_file(to, subject, template, path_mail_file, name_file, type_mail_file):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=application.config['MAIL_DEFAULT_SENDER']
    )
    with application.open_resource(path_mail_file) as fp:
		msg.attach(name_file, type_mail_file, fp.read())
    mail.send(msg)

#Custom decorator
def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.confirmed is False:
            return redirect(url_for('unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function
    
#Custom decorator
def check_admin(func2):
    @wraps(func2)
    def decorated_admin_function(*args, **kwargs):
        if current_user.role != 'admin':
            return redirect(url_for('notadmin'))
        return func2(*args, **kwargs)

    return decorated_admin_function

#Custom lowcase Valitador
def lowcase_check(form, field):
	if field.data.isupper() or not field.data.islower():
		raise ValidationError(u'Este campo solo acepta minúsculas')

class SignupForm(Form):
    email = TextField(u'Dirección Email', validators=[
            Required(u'Introduce una dirección email válida'),
            Length(min=6, message=(u'Dirección Email muy corta')),
            Email(message=(u'Dirección Email no válida.')), lowcase_check
            ])
    password = PasswordField('Clave', validators=[
            Required(u'Campo requerido'),
            Length(min=6, message=(u'Introduce una clave mas larga'))           
            ])
    username = TextField('Usuario', validators=[Required(u'Campo Requirido'), lowcase_check])
    
			
    agree = BooleanField(u'Acepto todos los <a href="/static/tos.html">Términos del Servicio</a>', validators=[Required(u'Debes aceptar los términos del servicio')])

	
			
class SigninForm(Form):
    username = TextField('Usuario', validators=[
            Required('Campo Requirido'),
            validators.Length(min=3, message=('Nombre de usuario muy corto')),
            lowcase_check])
    password = PasswordField('Clave', validators=[
            Required('Campo Requirido'),
            validators.Length(min=6, message=('Introduce una clave mas larga'))
            ])
    remember_me = BooleanField(u'Recuérdame', default = False)
    
class UploadForm(Form):
	input_file = FileField('', validators = [
			FileRequired(message = 'No hay archivo para subir!')
			, FileAllowed(['log'], message = 'Solo introduzca archivos .log')
			])
	submit = SubmitField(label = "Subir")
	
class UploadPatternForm(Form):
	input_file = FileField('', validators = [
			FileRequired(message = 'No hay archivo para subir!')
			, FileAllowed(['xlsx', 'txt'], message = 'Solo introduzca archivos .xlsx')
			])
	submit = SubmitField(label = "Subir")
	
	
	

@login_manager.user_loader
def load_user(id):
    return Users.query.get(id)
    
    
@application.route('/')
@application.route('/<username>')
def index(username = None):
    if username is None:
        return render_template('index.html', page_title = 'Inicio', signin_form = SigninForm())
    
    

@application.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        form = SignupForm(request.form)
        if form.validate():
            user = Users()
            form.populate_obj(user)

            user_exist = Users.query.filter_by(username=form.username.data).first()
            email_exist = Users.query.filter_by(email=form.email.data).first()

            if user_exist:
                form.username.errors.append('Usuario ya registrado')

            if email_exist:
                form.email.errors.append('Email ya registrado')
   
							
            if (user_exist or email_exist):
				return render_template('signup.html',
                                       signin_form = SigninForm(),
                                       form = form,
                                       page_title = 'Registro')

            else:
				user.active = True
				user.confirmed = False
				
				db.session.add(user)
				db.session.commit()
				
				token = generate_confirmation_token(user.email)
				confirm_url = url_for('confirm_email', token=token, _external=True)
				html = render_template('activate.html', confirm_url=confirm_url)
				subject = "Por favor confirma tu dirección de correo!"
				send_email(user.email, subject, html)
				
				
				return render_template('signup-success.html',
                                       user = user,
                                       signin_form = SigninForm(),
                                       page_title = 'Registro exitoso!')

        else:
            return render_template('signup.html',
                                   form = form,
                                   signin_form = SigninForm(),
                                   page_title = 'Registro')
    return render_template('signup.html',
                           form = SignupForm(),
                           signin_form = SigninForm(),
                           page_title = 'Registro')

@application.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method=='POST':
        if current_user is not None and current_user.is_authenticated():
            return redirect(url_for('index'))
    
        form = SigninForm(request.form)
        if form.validate():
            user = Users.query.filter_by(username = form.username.data).first()
            
            if user is None:
                form.username.errors.append('Usuario no registrado')
                return render_template('signinpage.html',  signinpage_form = form,
					page_title = 'Acceso')
            if user.password != form.password.data:
                form.password.errors.append('Clave incorrecta')
                return render_template('signinpage.html',  signinpage_form = form,
					page_title = 'Acceso')          
            
            login_user(user, remember = form.remember_me.data)            

            session['signed'] = True
            session['username']= user.username
            session['email']= user.email
            session['role']= user.role
            
            if session.get('next'):                
                next_page = session.get('next') 
                session.pop('next')
                return redirect(next_page) 
            else:
                return redirect(url_for('index'))
        return render_template('signinpage.html',  signinpage_form = form,
					page_title = 'Acceso')
    else:
        session['next'] = request.args.get('next')
        return render_template('signinpage.html', signinpage_form = SigninForm(),
					page_title = 'Acceso')        


@application.route('/signout')
def signout():
    session.pop('signed')
    session.pop('username')
    session.pop('role')
    session.pop('email')
    logout_user()
    return redirect(url_for('index'))

@application.route('/profile')
@login_required
@check_confirmed
def profile():
    return render_template('profile.html', page_title='Reporta - Perfil')

@application.route('/update_pattern', methods=['GET', 'POST'])
@login_required
@check_confirmed
@check_admin
def update_pattern():
	form = UploadPatternForm()
	if request.method == 'POST' and form.validate_on_submit():
		input_file = request.files['input_file']
		if input_file:
			filename = secure_filename(input_file.filename)
			global filepath 
			filepath = os.path.join(application.config['UPLOAD_FOLDER'], filename)
			input_file.save(filepath)
			return render_template('upload-pattern-success.html', filename=filename, page_title = u'Éxito')
	else:
		return render_template('upload-pattern.html',  uploadpattern_form = form,  page_title = 'Subida')
    
    
@application.route('/adminpanel')
@login_required
@check_confirmed
@check_admin
def adminpanel():
    return render_template('adminpanel.html', page_title='Administrador')
    
@application.route('/confirm/<token>')
@login_required
def confirm_email(token):
    if current_user.confirmed:
		return render_template('already-confirm.html', page_title = 'Cuenta ya Confirmada!')
    else:
		email = confirm_token(token)
		user = Users.query.filter_by(email = current_user.email).first()
		if user.email == email:
			user.confirmed = True
			db.session.add(user)
			db.session.commit()
			return render_template('confirm-success.html', page_title = 'Confirmacion exitosa!')
    return render_template('invalid-confirm.html', page_title = 'Error')

@application.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    return render_template('unconfirmed.html')

@application.route('/notadmin')
@login_required
@check_confirmed
def notadmin():
    if current_user.role == 'admin':
        return redirect(url_for('index'))
    return render_template('notadmin.html')
    
@application.route('/upload', methods=['GET', 'POST'])
@login_required
@check_confirmed
def upload():
	form = UploadForm()
	if request.method == 'POST' and form.validate_on_submit():
		input_file = request.files['input_file']
		if input_file:
			filename = secure_filename(input_file.filename)
			global filepath 
			filepath = os.path.join(application.config['UPLOAD_FOLDER'], filename)
			input_file.save(filepath)
			return render_template('upload-success.html', filename=filename, page_title = u'Éxito')
	else:
		return render_template('upload.html', uploadfile_form = form,  page_title = 'Subida')

@application.route('/processing')
@login_required
@check_confirmed
def processing():
	global filepath
	datafile = file(filepath)
	patternFilePath = os.path.join(application.config['UPLOAD_FOLDER'], "test.xlsx")
	a1ApzPathZip = os.path.join(application.config['UPLOAD_FOLDER'], "reporta/a1Apz.txt")
	heirFilePath = os.path.join(application.config['UPLOAD_FOLDER'], "reporta/test2.xlsx")
	countApzA1 = 0
	countApzA2 = 0
	countApzA3 = 0
	colApzA1 = []
	colApzA2 = []
	colApzA3 = []
	a1ApzAux = False
	a2ApzAux = False
	a3ApzAux = False
	
	
	for line in datafile:
		if "MSSVA3_MI0313A_" in line:
			a1ApzAux = False
			a2ApzAux = False
			a3ApzAux = False
		
		if a1ApzAux == True:
			colApzA1.append(line)
			
		if 'A1/APZ' in line:
			a1ApzAux = True
			countApzA1 += 1
			colApzA1.append(line)
		
		if a2ApzAux == True:
			colApzA2.append(line)		
						 
		if 'A2/APZ' in line:
			a2ApzAux = True
			countApzA2 += 1
			colApzA2.append(line)
		
		if a3ApzAux == True:
			colApzA3.append(line)
			
		if 'A3/APZ' in line:
			a3ApzAux = True
			countApzA3 += 1
			colApzA3.append(line)
			
	os.remove(filepath)
	
	if countApzA1 >= 1:
		f = open(a1ApzPathZip, 'w')
		for i in colApzA1:
			f.write(i)
		f.close()
		
	
	wb = load_workbook(patternFilePath)
	##ws = wb.get_sheet_by_name("mss")
	##c = ws.cell(row = 5, column = 5)
	#c.hyperlink = (a1ApzPathXl)
	wb.save(heirFilePath)
	
	
	
	#zf = zipfile.ZipFile('report.zip', mode='w')
	#zf.write(heirFilePath, arcname='test.xlsx')
	#if countApzA1 >= 1:
		#zf.write(a1ApzPathZip, arcname='a1Apz.txt')
	#zf.close()
	
	

	
	#File sender
	path_mail_file = "static/patterns/reporta/test2.xlsx"
	type_mail_file = "excel/xlsx"
	name_file = "reporte.xlsx"
	html = render_template('report.html')
	subject = "Has recibido un Reporte!"
	send_email_file(current_user.email, subject, html, path_mail_file, name_file, type_mail_file)
	
	os.remove(a1ApzPathZip)
	
	return render_template('processing-results.html',countApzA1 = countApzA1,
	 colApzA1=colApzA1, countApzA2=countApzA2, colApzA2=colApzA2 , 
	 countApzA3=countApzA3, colApzA3 =colApzA3, page_title = 'Resultados',
	 a1ApzPathZip=a1ApzPathZip, heirFilePath=heirFilePath, patternFilePath=patternFilePath, current_user_email=current_user.email )







def dbinit():
	db.drop_all()
	db.create_all()
	admin = Users(username='lomelisan', firstname='Carlos', 
		lastname='Lomeli', password='esunsecreto', 
		email='lomelisan@hotmail.com', confirmed = True, 
		role='admin', active = True)
	db.session.add(admin)
	db.session.commit()




if __name__ == '__main__':
	dbinit()
	application.run(debug=True, host="0.0.0.0", port=8888)





