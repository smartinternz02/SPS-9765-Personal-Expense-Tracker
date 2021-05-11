from flask import Flask, render_template, request, redirect, session,flash,url_for
from datetime import timedelta
from flaskext.mysql import MySQL
from dotenv import load_dotenv
import os
from sendMail import *
from datetime import datetime

load_dotenv()

mysql = MySQL()

app = Flask(__name__)


app.secret_key = os.getenv('SECRET_KEY')

app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('MYSQL_DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB')
app.config['MYSQL_DATABASE_HOST'] =os.getenv('MYSQL_DATABASE_HOST')
app.config['MYSQL_DATABASE_PORT'] = int(os.getenv('MYSQL_DATABASE_PORT'))

mysql.init_app(app)

month = datetime.now().month
# print(month)

months = {	'01':'January',
		'02':'February',
		'03':'March',
		'04':'April',
		'05':'May',
		'06':'June',
		'07':'July',
		'08':'August',
		'09':'September',
		'10':'October',
		'11':'November',
		'12':'December'		}


# utility functions
def updateCategory(cat,user_id,amount):
    cat = str(cat)
    user_id= str(user_id)
    con = mysql.connect()
    cur = con.cursor()
    cur.execute("SELECT `spent` FROM `category` WHERE `id`='"+cat+"' AND `user_id`='"+user_id+"'")
    spent = cur.fetchone()
    amount =  int(amount)
    spent = str(spent[0] +amount)
    cur.execute("UPDATE `category` SET `spent`='"+spent+"' WHERE `id`='"+cat+"' AND `user_id`='"+user_id+"'")
    con.commit()
    return

def getUserId():
    username = session.get("username")
    con = mysql.connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM `users` WHERE `name`='"+username+"'")
    user = cur.fetchone()
    user_id = str(user[0])
    return user_id


def auth():
    if not session.get("username"):
        return False
    else:
        return True


def getIncome(user_id):
    con = mysql.connect()
    cur = con.cursor()
    user_id= str(user_id)
    cur.execute("SELECT * FROM `income` WHERE `user_id`='"+user_id+"'")
    data = cur.fetchone()
    return data

def getMaxLimitCat(user_id):
    con = mysql.connect()
    cur = con.cursor()
    user_id= str(user_id)
    cur.execute("SELECT * FROM `category` WHERE `user_id`='"+user_id+"'")
    data = cur.fetchall()
    limit = [row[3] for row in data]
    maxLimitOnAllCat = sum(limit)
    return maxLimitOnAllCat



def updateExpenditure(user_id,amount,type):
    con = mysql.connect()
    cur = con.cursor()
    user_id= str(user_id)
    data = getIncome(user_id)
    if type == 'Credit':
        credit = str(data[2] + int(amount))
        cur.execute("UPDATE `income` SET `amount`='"+credit+"' WHERE `user_id`='"+user_id+"'")
        con.commit()
    elif type == 'Debit':
        debit = str(data[3] + int(amount))
        cur.execute("UPDATE `income` SET  `spent` = '"+debit+"' WHERE `user_id`='"+user_id+"'")
        con.commit()
    return

def updateIncomeOnCatDel(user_id,id):
    con = mysql.connect()
    cur = con.cursor()
    income = getIncome(user_id)
    Credit = 'Credit'
    cur.execute("SELECT `amount` FROM `expense` INNER JOIN `category` ON expense.category_id = category.id WHERE `type`='"+Credit+"' AND category.id ='"+id+"' ")
    data = cur.fetchall()
    print(data)
    data =sum(list(map(sum, list(data))))
    print(data)
    amount =str(int(income[2])- int(data))
    cur.execute("UPDATE `income` SET `amount`='"+amount+"' WHERE `user_id`='"+user_id+"'")
    con.commit()
    return

def getMonthlyCatExp(user_id,cat_id,month=datetime.now().month):
    con = mysql.connect()
    cur = con.cursor()
    user_id= str(user_id) 
    cat_id= str(cat_id) 
    month = str(month)
    Debit = 'Debit'
    cur.execute("SELECT * FROM `expense` WHERE `user_id`='"+user_id+"' AND `category_id`='"+cat_id+"' AND `type`='"+Debit+"' AND MONTH(`date`) ='"+month+"'   ORDER BY `date` ")
    data = cur.fetchall()
    limit = [row[4] for row in data]
    maxMonthlyLimit = sum(limit)
    return maxMonthlyLimit




def checkMaxLimit(user_id,id):
    global month
    con = mysql.connect()
    cur = con.cursor()
    username = session.get("username")
    cur.execute("SELECT * FROM `users` WHERE `name`='"+username+"'")
    user = cur.fetchone()
    user_mail = user[2]
    cur.execute("SELECT * FROM `category` WHERE `user_id`='"+user_id+"' AND `id` ='"+id+"'")
    data = cur.fetchall()
    limit = int(data[0][3])
    spent = getMonthlyCatExp(user_id,id,month)
    name = data[0][2]
    msg = ''
    if spent >= limit:
        msg = 'You have exceeded the max expenditure limit on category ' + name + ' for this month  '+'\nLimit: '+str(limit) +'\nSpent: '+str(spent)
        sendMail(user_mail,msg)
    elif limit - spent <=100:
        msg = 'You are reaching your max  expenditurelimit on category'+ name+ ' for this month  '+'\nLimit: '+str(limit) +'\nSpent: '+str(spent)
        sendMail(user_mail,msg)
    return 


def getTotalMonthlyExp(user_id,month=datetime.now().month):
    con = mysql.connect()
    cur = con.cursor()
    month = str(month)
    user_id = str(user_id)
    cur.execute("SELECT * FROM category WHERE `user_id`='"+user_id+"'")
    cats = cur.fetchall()
    spent = [getMonthlyCatExp(user_id,i[0],month) for i in cats]
    return sum(spent)



@app.route("/")
def index():
    return redirect('home')

@app.route("/home")
def home():
    if auth():
        user = session.get("username")
    else:
        user = ''
    return render_template('home.html',user=user)

# app name
@app.errorhandler(404)
def not_found(e):
  return render_template("errorpage.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = request.form['username']
        password = request.form['password']
        con = mysql.connect()
        cur = con.cursor()
        cur.execute(
            'SELECT `password` FROM `users` where `name`=%s', (username))
        data = cur.fetchone()
        
        if password == data[0]:
            return redirect('dashboard')
        else:
            flash(u'Incorrect usesrname or password', 'info')
            return render_template("errorpage.html")
    else:
        return render_template('login.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        password1 = request.form['password1']
        password2 = request.form['password2']
        if password1 != password2:
            flash(u'Passwords do not match', 'info')
            return render_template("errorpage.html")
        else:
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("SELECT * FROM `users` WHERE `email`='"+email+"'")
            account = cur.fetchone()
            if account:
                flash(u'Account with this mail id already exists!', 'danger')
                return render_template("errorpage.html")

            cur.execute("INSERT INTO `users`(`name`, `email`,`mobile`, `password`) VALUES(%s,%s,%s,%s)",
                        (name, email, mobile, password1))
            con.commit()
            cur.execute('SELECT `id` FROM `users` where `name`=%s', (name))
            user_id = cur.fetchone()
            amount =0
            cur.execute("INSERT INTO `income`(`user_id`,`amount`) VALUES(%s,%s)",(user_id, amount))
            con.commit()
            msg = 'Welcome to Expense Tracker App! \nThank you for using our service.'
            sendMail(email,msg)

            return redirect('login')
    else:
        return render_template('register.html')


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        global month
        if(request.args.get('month')):
            month = request.args.get('month')
        month = str(month)
        con = mysql.connect()
        cur = con.cursor()

        user = session.get("username")
        user_id = getUserId()
        
        income = getIncome(user_id)

        cur.execute("SELECT * FROM `category` WHERE `user_id`='"+user_id+"' ")
        cats = cur.fetchall()
        spent = [getMonthlyCatExp(user_id,i[0],month) for i in cats]

        c= list()
        for i in range(len(cats)):
            a = list(cats[i])
            a[4] = spent[i]
            c.append(a)
            
        cat ={cats[i][2]: spent[i] for i in range(len(cats))}
        title = {'Task':'My Expenditure'}
        ct = {**title, **cat}

        Debit = 'Debit'
        cur.execute("SELECT * FROM `expense` WHERE `user_id`='"+user_id+"' AND `type`='"+Debit+"' AND MONTH(`date`) ='"+month+"'   ORDER BY `date` ")
        line = cur.fetchall()
        labels = [row[6].strftime("%d-%m-%y") for row in line]
        values = [row[4] for row in line]
        
        
        labelsBar=[]
        valuesBar =[]
        for row in line:
            if row[5] in labelsBar:
                valuesBar[labelsBar.index(row[5])] += row[4]
            else:
                labelsBar.append(row[5])
                valuesBar.append(row[4])

        totalIncome = {'Task':'Income vs Expenditure','income':income[2],'expenditure':income[3] }

        return render_template('dashboard.html',months=months, user=user, category=c,income=income,data=ct,labels=labels,values=values,labelsBar=labelsBar,valuesBar=valuesBar,totalIncome=totalIncome)


@app.route("/addExpense", methods=['GET', 'POST'])
def addExpense():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user = session.get("username")
        con = mysql.connect()
        cur = con.cursor()
        user_id = getUserId()
        if request.method == 'POST':
            cat = request.form['cat']
            name = request.form['name']
            user_id = request.form['user_id']
            amount = request.form['amount']
            date = request.form['date']
            mode = request.form['mode']
            type = request.form['type']
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("INSERT INTO `expense`(`name`, `date`, `amount`, `mode`, `category_id`, `user_id`,`type`) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (name, date, amount, mode, cat, user_id,type))
            con.commit()
            if type == 'Debit':
                updateCategory(cat,user_id,amount)
            updateExpenditure(user_id,amount,type)
            checkMaxLimit(str(user_id),cat)
            flash(u'Added Successfully!', 'info')
            return redirect('myExpenses')
        else:
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("SELECT * FROM `category` WHERE `user_id`='"+user_id+"'")
            cat = cur.fetchall()
            return render_template('addExpense.html',category=cat,user_id=user_id,user=user)


@app.route("/editExpense", methods=['GET', 'POST'])
def editExpense():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user = session.get("username")
        user_id = getUserId()
        con = mysql.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM `category` WHERE `user_id`='"+user_id+"'")
        cat = cur.fetchall()
        if request.method == 'POST':
            cat = request.form['cat']
            name = request.form['name']
            id = request.form['id']
            date = request.form['date']
            mode = request.form['mode']
            amount = request.form['amount']
            type = request.form['type']
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("UPDATE `expense` SET `name`='"+name+"',`date`='"+date+"',`category_id`='"+cat+"',`mode`='"+mode+"',`type`='"+type+"' WHERE `id`='"+id+"'")
            con.commit()
            # updateCategory(cat,user_id,amount,type='add')
            # updateExpenditure(user_id,amount,type)
            
            if type == 'Debit':
                updateCategory(cat,user_id,amount)
            checkMaxLimit(user_id,cat)
            flash(u'Saved Successfully!', 'info')
            return redirect('myExpenses')
        else:
            id = request.args.get('id')
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("SELECT * FROM `expense` WHERE `id`='"+id+"'")
            data = cur.fetchone()
            return render_template('editExpense.html', expense=data,category=cat,user=user)


@app.route("/deleteExpense")
def deleteExpense():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        id = request.args.get('id')
        con = mysql.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM `expense` WHERE `id`='"+id+"'")
        data = cur.fetchone()
        cat = data[2]
        user_id = data[1]
        amount = - data[4]
        updateCategory(cat,user_id,amount)
        type = data[7]
        updateExpenditure(user_id,amount,type)
        cur.execute("DELETE FROM `expense` WHERE `id`='"+id+"'")
        con.commit()
        flash(u'Deleted Successfully!', 'danger')
        return redirect('myExpenses')


@app.route("/myExpenses")
def myExpenses():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        global month
        month = str(month)
        user_id = getUserId()
        user = session.get("username")
        con = mysql.connect()
        cur = con.cursor()
        con = mysql.connect()
        cur.execute("SELECT * FROM expense WHERE `user_id`='"+user_id+"' AND MONTH(`date`) ='"+month+"' ORDER BY   `date` DESC")
        data = cur.fetchall()
        cur.execute("SELECT * FROM category WHERE `user_id`='"+user_id+"'")
        cats = cur.fetchall()
        category ={cats[i][0]: cats[i][2] for i in range(len(cats))}
        return render_template('myExpenses.html', expense=data,cat=category,user=user)



@app.route("/addCategory", methods=['GET', 'POST'])
def addCategory():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user_id = getUserId()
        user = session.get("username")
        con = mysql.connect()
        cur = con.cursor()
        if request.method == 'POST':
            name = request.form['name']
            limits = request.form['amount']
            user_id = request.form['user_id']
            con = mysql.connect()
            cur = con.cursor()
            limit = getMaxLimitCat(user_id)
            income = getIncome(user_id)
            balance = int(income[2])-int(limit)
            if int(limits) >= int(income[2]) or int(limits)>= balance:
                flash(u'Limit must be less total income', 'info')
                return render_template("errorpage.html")

            cur.execute("INSERT INTO `category`(`name`, `limits`, `user_id`) VALUES (%s,%s,%s)",
                        (name, limits, user_id))
            con.commit()
            flash(u'Added Successfully!', 'info')
            return redirect('dashboard')
        else:
            return render_template('addCategory.html',user_id=user_id,user=user)

@app.route("/editCategory", methods=['GET', 'POST'])
def editCategory():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user = session.get("username")
        if request.method == 'POST':
            if request.form['submit'] =='editCategory':
                name = request.form['name']
                id = request.form['id']
                limits = request.form['amount']
                con = mysql.connect()
                cur = con.cursor()
                cur.execute("UPDATE `category` SET `name`='"+name+"',`limits`='"+limits+"' WHERE `id`='"+id+"'")
                con.commit()
                
                user_id = getUserId()
                limit = getMaxLimitCat(user_id)
                income = getIncome(user_id)
                balance = int(income[2])-int(limit)
                if int(limits) >= int(income[2]) or int(limits)>= balance:
                    flash(u'Limit must be less total income', 'info')
                    return render_template("errorpage.html")
                flash(u'Saved Successfully!', 'info')
                return redirect('dashboard')
            elif request.form['submit'] =='addIncome':
                id = request.form['user_id']
                amount = request.form['amount']
                con = mysql.connect()
                cur = con.cursor()
                cur.execute("UPDATE `income` SET `amount`='"+amount+"' WHERE `user_id`='"+id+"'")
                con.commit()
                return redirect('dashboard')

        else:
            id = request.args.get('id')
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("SELECT * FROM `category` WHERE `id`='"+id+"'")
            cat = cur.fetchone()
            return render_template('editCategory.html',cat=cat,user=user)


@app.route("/deleteCategory")
def deleteCategory():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        id = request.args.get('id')
        con = mysql.connect()
        cur = con.cursor()
        user_id = getUserId()
        updateIncomeOnCatDel(user_id,id)
        cur.execute("DELETE FROM `category` WHERE `id`='"+id+"'")
        con.commit()
        flash(u'Deleted Successfully!', 'danger')
        return redirect('dashboard')


@app.route("/editIncome", methods=['GET', 'POST'])
def editIncome():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user = session.get("username")
        if request.method == 'POST':
            id = request.form['id']
            amount = request.form['amount']
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("UPDATE `income` SET `amount`='"+amount+"' WHERE `id`='"+id+"'")
            con.commit()
            flash(u'Saved Successfully!', 'info')
            return redirect('dashboard')

        else:
            id = request.args.get('id')
            con = mysql.connect()
            cur = con.cursor()
            cur.execute("SELECT * FROM `income` WHERE `id`='"+id+"'")
            income = cur.fetchone()
            return render_template('editIncome.html',income=income,user=user)


@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect('home')


@app.route("/wallet")
def wallet():
    if not auth():
        flash(u'Login To continue', 'info')
        return render_template("errorpage.html")
    else:
        user_id = getUserId()
        income = getIncome(user_id)
        user = session.get("username")
        exp = getTotalMonthlyExp(str(user_id),month=datetime.now().month)

        return render_template('wallet.html',user=user,income=income,exp = exp)


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
