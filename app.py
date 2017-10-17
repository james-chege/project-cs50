from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
app = Flask(__name__)


app.config['SECRET_KEY'] = 'zyxwvutsrqponmlkj'

app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#models implementation
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

    items = db.relationship('Item', backref='user', lazy='dynamic')


    def __repr__(self):
        return '<User %r>' % self.id


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(128))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    total = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __repr__(self):
    	return 'Item %s %r' % (self.item, self.user_id)
  
# get current user's  id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# forms
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    confirm = PasswordField('confirm', validators=[InputRequired(), Length(min=8, max=80)])
class PasswordForm(FlaskForm):
    oldpassword = PasswordField('old password', validators=[InputRequired(), Length(min=8, max=80)])
    newpassword = PasswordField('new password', validators=[InputRequired(), Length(min=8, max=80)])
    confirmnew = PasswordField('confirm', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

# root
@app.route('/')
def index():
    return render_template('index.html')

# login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))            

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)

# sign up new user
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
         try:
            if form.password.data !=  form.confirm.data:
                return "Password Mismatch"
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('dashboard'))
         except IntegrityError:
            db.session.rollback() 
            return '<h1>Username or Email already exists</h1>'  

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    items = Item.query.filter_by(user_id=current_user.id).all()
    cash = Item.query.with_entities(func.sum(Item.total)).filter_by(user_id=current_user.id).scalar()
    return render_template('dashboard.html', name=current_user.username, items=items, cash=cash)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():

    if request.method == "GET":
        items = Item.query.filter_by(user_id=current_user.id).all()
        return render_template('items.html', items=items)
    else:
        todoitem = request.form['todoitem']
        quantity = request.form['quantity']
        price = request.form['price']
        items = Item.query.filter_by(user_id=current_user.id).all()
        available = Item.query.with_entities(Item.item).filter(Item.item == todoitem, Item.user_id == current_user.id).first()
        if not (todoitem and quantity and price):
            return '<h1> Please provide the item name, quantity and price</h1>'
        elif available == None:
            if todoitem.isnumeric() == True:
                return "<h1>Only alpha or alphanumeric accepted for item name</h1>"
            total = float(price) * float(quantity)
            todo = Item(item=request.form['todoitem'], user_id=current_user.id, quantity=quantity, price=price, total=total)
            db.session.add(todo)
            db.session.commit()
            cash = Item.query.with_entities(func.sum(Item.total)).filter_by(user_id=current_user.id).scalar()
            items = Item.query.filter_by(user_id=current_user.id).all()
            return redirect(url_for('items'))
        elif todoitem == available.item:
            return '<h1>The Item you are adding exists try edit</h1>'
            
@app.route('/items', methods=["GET"])
def items():
    items = Item.query.filter_by(user_id=current_user.id).all()
    cash = Item.query.with_entities(func.sum(Item.total)).filter_by(user_id=current_user.id).scalar()
    return render_template('items.html', items=items, cash=cash)


@app.route('/delete/<id>')
@login_required
def delete_task(id):
    task = Item.query.get(int(id))
    if not task:
        return redirect(url_for('items'))

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('add_item'))

@app.route('/edit/<int:item_id>', methods=["GET", "POST"])
def edit(item_id):
    update = request.form.get("value")
    quantity = request.form.get("quantity")
    #no input
    if update == "" and quantity =="":
        return redirect(url_for('items'))  
    #only the quantity  
    if update == "" and int(quantity) > 0:
        ite = Item.query.filter_by(id=item_id).one()
        ite.quantity = quantity
        price = ite.price
        ite.total = float(quantity) * float(price)
        db.session.commit()
        return redirect(url_for('items'))
        #only the update
    elif update != "" and quantity == "":
        if update.isalnum() != True or update.isnumeric() == True:
                return "<h1>Only alpha or alphanumeric accepted for item name</h1>"
        available = Item.query.with_entities(Item.item).filter(Item.item == update, Item.user_id == current_user.id).first()
        if available:
            return "<h1>The item exists</h1>"
        ite = Item.query.filter_by(id=item_id).one()
        ite.item = update
        db.session.commit()
        return redirect(url_for('items'))
        #both supplied
    elif update != "" and int(quantity) >= 1:
        if update.isalnum() != True or update.isnumeric() == True:
                return "<h1>Only alpha or alphanumeric accepted for item name</h1>"
        available = Item.query.with_entities(Item.item).filter(Item.item == update, Item.user_id == current_user.id).first()
        if available:
            return "<h1>The item exists</h1>"
        ite = Item.query.filter_by(id=item_id).one()
        price = ite.price
        ite.item = update
        ite.quantity = quantity
        ite.total = float(quantity) * float(price)
        db.session.commit()
        return redirect(url_for('items'))
    

@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    form = PasswordForm()

    if request.method == 'GET':
        return render_template('profile.html', name=current_user.username, email=current_user.email, form=form)
    else:
        if form.validate_on_submit():
            old = form.oldpassword.data
            if not check_password_hash(current_user.password, old):
                return '<h1>Incorrect old password</h1>'
            elif check_password_hash:
                new = form.newpassword.data
                confirmnew = form.confirmnew.data
                if new != confirmnew:
                    return '<h1>Password Mismatch!</h1>'
                else:
                    new = form.newpassword.data
                    hashed_password = generate_password_hash(new, method='sha256')
                    password = User.query.filter(id == current_user.id).first()
                    current_user.password = hashed_password
                    db.session.commit()
                    return '<h1>Password successfully changed!</h1>'

    return render_template('profile.html', name=current_user.username, email=current_user.email, form=form)


if __name__ == '__main__':
    app.run(debug=True)