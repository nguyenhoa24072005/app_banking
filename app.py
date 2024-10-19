from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key ="supersecretkey"
# Db Connection 
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="banking_db"
    )
@app.route('/')
def index():
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('index.html',customers=customers)

@app.route('/create_customer',methods=['GET','POST'])
def create_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        balance = float(request.form['balance'])
        
        conn = connect_db()
        cursor = conn.cursor()
        try:
            query  = "INSERT INTO Customer(name, email, balance) VALUES(%s,%s,%s)"
            cursor.execute(query,(name, email, balance))
            conn.commit()
            flash("Customer created successfully","success")
            
        except mysql.connector.Error as err: 
            flash (f"Error:{err}", "danger" )
        
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('index'))
    return render_template('create_customer.html')

# Route cho Transaction (Giao dịch)
@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy danh sách khách hàng
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        transaction_type = request.form['transaction_type']
        amount = Decimal(request.form['amount'])
        
        try:
            # Lấy số dư hiện tại của khách hàng
            cursor.execute("SELECT balance FROM Customer WHERE id = %s", (customer_id,))
            customer = cursor.fetchone()
            
            if not customer:
                flash("Customer not found!", "danger")
                return redirect(url_for('transaction'))
            
            current_balance = Decimal(customer['balance'])
            
            if transaction_type == 'deposit':
                new_balance = current_balance + amount
            elif transaction_type == 'withdraw':
                if amount > current_balance:
                    flash("Insufficient balance!", "danger")
                    return redirect(url_for('transaction'))
                new_balance = current_balance - amount
            else:
                flash("Invalid transaction type!", "danger")
                return redirect(url_for('transaction'))
            
            # Cập nhật số dư mới
            cursor.execute("UPDATE Customer SET balance = %s WHERE id = %s", (new_balance, customer_id))
            
            # Thêm bản ghi vào bảng Transaction
            cursor.execute(
                "INSERT INTO Transaction (customer_id, transaction_type, amount) VALUES (%s, %s, %s)", 
                (customer_id, transaction_type, amount)
            )
            
            conn.commit()
            flash("Transaction successful!", "success")
        
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('transaction.html', customers=customers)
@app.route('/transaction_history/<int:customer_id>')
def transaction_history(customer_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy lịch sử giao dịch của khách hàng (sử dụng transaction_time thay vì transaction_date)
    cursor.execute("SELECT * FROM Transaction WHERE customer_id = %s ORDER BY transaction_time DESC", (customer_id,))
    transactions = cursor.fetchall()
    
    # Lấy thông tin khách hàng
    cursor.execute("SELECT * FROM Customer WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()

    cursor.close()
    conn.close()

    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for('index'))

    return render_template('transaction_history.html', transactions=transactions, customer=customer)

# Chạy ứng dụng Flask 
if __name__ =='__main__':
    app.run(debug=True)