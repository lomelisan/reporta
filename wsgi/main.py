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
global colGen
global countLines
global countApzA1
global heirFilePath
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

@application.route('/reading')
@login_required
@check_confirmed
def reading():
	global filepath
	global colGen
	global countApzA1
	global countLines
	global ok_dpwsp
	global ok_exrpp
	
	datafile = file(filepath)
	colGen = []
	
	
	
	countLines = 0
	
	allip = False
	countApzA1 = 0
	
	calp = False
	
	dpwsp = False
	ok_dpwsp = False
	
	plldp = False
	
	exrpp= False
	count_exrpp = 0
	ok_exrpp = True
	
	exemp = False
	count_exemp = 0
	ok_exemp = True
	
	ntstp = False
	count_ntstp = 0
	ok_ntstp = False
	
	syrip = False
	
	
	apamp = False
	count_apamp = 0
	count_pas = 0
	count_act = 0
	
	m3rsp = False
	m3asp = False
	ihalp = False
	ihstp = False
	strsp = False
	blorp = False
	blurp = False
	faiap = False
	mgsvp = False
	mgarp = False
	stbsp = False
	sybfp = False
	
	for line in datafile:
		countLines += 1
		colGen.append(line)
		
		if len(line) == 10:
			continue
		
		if "END" in line:
			allip = False
			calp = False
			dpwsp = False
			plldp = False
			exrpp = False
			exemp = False
			ntstp = False
			syrip = False
			apamp = False
			m3rsp = False
			m3asp = False
			ihalp = False
			ihstp = False
			strsp = False
			blorp = False
			blurp = False
			faiap = False
			mgsvp = False
			mgarp = False
			stbsp = False
			sybfp = False
		
		#if 	'<allip;' in line:
			#allip = True
		#if allip == True and 'A1/APZ' in line:
			#countApzA1 += 1
		
		
		# Proceso alarma Allip
		if 'A1/APZ' in line:
			countApzA1 += 1
		#----------	 
			
		if '<CACLP;' in line:
			calp = True
			
		# Proceso alarma DPWSP	
		if '<DPWSP;' in line:
			dpwsp = True
		if '<DPWSP;' and 'NRM  B  WO' in line:
			ok_dpwsp = True
		#----------	
			
		if '<PLLDP;' in line:
			plldp = True
		
		# Proceso alarma EXRP
		if exrpp == True:
			count_exrpp += 1
			if count_exrpp >= 4:
				if 'WO' in line:
					ok_exrpp = True
				else :
					exrpp = False
					ok_exrpp = False
					
		
		if '<EXRPP:RP=ALL;' in line:
			exrpp = True
			count_exrpp += 1
		#----------	 
			
		# Proceso alarma EXEMP
		if 	exemp == True:
			count_exemp += 1
			if count_exrpp >= 4:
				if 'WO' in line:
					ok_exemp = True
				else:
					exemp = False
					ok_exemp = False
				
		if '<EXEMP:rp=all,em=ALL;' in line:
			exemp = True:
			count_exemp += 1
		#----------
		
			
		# Proceso alarma NTSP
		if 	ntstp == True:
			count_ntstp += 1
			if count_ntstp >= 4:
				if 'WO' in line:
					ok_ntstp = True
				else:
					ntstp = False
					ok_ntstp = False
		
		if '<NTSTP:SNT=ALL;' in line:
			ntstp = True
			count_ntstp += 1
		#----------
			 
		if '<SYRIP:SURVEY;' in line:
			syrip = True
		
		# Proceso alarma APAMP
		if apamp == True:
			count_apamp += 1
			if count_apamp += 3:
				if 'PASSIVE' in line:
					count_pas += 1
				if 'ACTIVE' in line:
					count_act += 1
			else:
				apamp = False
					
				
				
		if 'DIRECTORY ADDRESS DATA' in line:
			apamp = True
			count_apamp == 1
		#----------
		
		
		if '<M3RSP:DEST=ALL;' in line:
			m3rsp = True
			
		if '<M3ASP;' in line:
			m3asp = True
		
		if '<IHALP:EPID=ALL; ' in line:
			ihalp = True
		
		if '<IHSTP:IPPORT=ALL;' in line:
			ihstp = True
		
		if '<STRSP:R=ALL;' in line:
			strsp = True
		
		if '<BLORP;' in line:
			blorp = True
		
		if '<BLURP:R=ALL;' in line:
			blurp = True
		
		if '<FAIAP:R=ALL;' in line:
			faiap = True
			
		if '<MGSVP;' in line:
			mgsvp = True	 
		
		if '<MGARP:NLOG=10;' in line:
			mgarp = True
		
		if '<STBSP:DETY=ALL;' in line:
			stbsp = True
		
		if '<SYBFP:FILE; ' in line:
			sybfp = True
			
	os.remove(filepath)	
	
	return render_template('reading-results.html', countLines=countLines,
	page_title = 'Lectura exitosa', t = t)


@application.route('/processing')
@login_required
@check_confirmed
def processing():
	global colGen
	global countApzA1
	global heirFilePath
	global countLines
	global ok_dpwsp
	global ok_exrpp
	patternFilePath = os.path.join(application.config['UPLOAD_FOLDER'], "ModeloB.xlsx")
	heirFilePath = os.path.join(application.config['UPLOAD_FOLDER'], "reporta/reporte.xlsx")
	i = 0
	j = 0
	wb = load_workbook(patternFilePath)
	ws = wb.get_sheet_by_name("logo")
	ws2 = wb.get_sheet_by_name("MSS")
	rows = countLines
	x = "reporte.xlsx#logo!A1"
	
	for i in range(rows):
		ws.cell(row=i+1, column=1).value = colGen[i]
	
	i = 0
	rows = 56
	for i in range(rows):
		if i  == 16:
			ws2.cell(row=i+1, column=5).hyperlink = (x)
			if countApzA1 >= 1:
				ws2.cell(row=i+1, column=4).value = "NOT OK"
			else:
				ws2.cell(row=i+1, column=4).value = "OK"
			
		if i >= 22 and i <= 41:
			ws2.cell(row=i+1, column=5).hyperlink = (x)
			if i == 23:
				if ok_dpwsp == True:
					ws2.cell(row=i+1, column=4).value = "OK"
				else:
					ws2.cell(row=i+1, column=4).value = "NOT OK"
			if i == 25:
				if ok_exrpp == True:
					ws2.cell(row=i+1, column=4).value = "OK"
				else:
					ws2.cell(row=i+1, column=4).value = "NOT OK"
					
		if i == 56:
			break
		if i >= 47:
			ws2.cell(row=i+1, column=5).hyperlink = (x)
		
	
	wb.save(heirFilePath)
	
	return render_template('processing-results.html', page_title = 'Proceso exitoso')
	
@application.route('/sending')
@login_required
@check_confirmed
def sending():		
	global heirFilePath
	#File sender
	if os.environ.get('OPENSHIFT_DATA_DIR'):
		path_mail_file = heirFilePath
	else:
		path_mail_file = "static/patterns/reporta/reporte.xlsx"
	type_mail_file = "excel/xlsx"
	name_file = "reporte.xlsx"
	html = render_template('report.html')
	subject = "Has recibido un Reporte!"
	send_email_file(current_user.email, subject, html, path_mail_file, name_file, type_mail_file)
	
	os.remove(heirFilePath)
	
	return render_template('sending-results.html', 
	page_title = 'Reporte enviado' )



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





