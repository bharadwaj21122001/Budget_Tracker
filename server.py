import http.server
import socketserver
import json
import psycopg2
import datetime

# HTML template for the login and registration forms
LOGIN_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Budget Tracker - Login</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h1 class="text-center mt-5">Welcome to Budget Tracker</h1>
        <div class="row mt-5">
            <div class="col-md-6 offset-md-3">
                <h2>Login</h2>
                <form id="login-form">
                    <div class="form-group">
                        <input type="email" class="form-control" id="email" placeholder="Email">
                    </div>
                    <div class="form-group">
                        <input type="password" class="form-control" id="password" placeholder="Password">
                    </div>
                    <button type="submit" class="btn btn-primary btn-block">Login</button>
                </form>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-6 offset-md-3">
                <p id="login-message" class="text-center"></p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('login-form').addEventListener('submit', function(event) {
            event.preventDefault();
            var email = document.getElementById('email').value;
            var password = document.getElementById('password').value;
            var data = {
                'action': 'login',
                'email': email,
                'password': password
            };
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var response = JSON.parse(xhr.responseText);
                    document.getElementById('login-message').innerText = response.message;
                    if (response.success) {
                        window.location.href = '/home';
                    }
                }
            };
            xhr.send(JSON.stringify(data));
        });
    </script>
</body>
</html>
"""

HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Budget Tracker</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        /* Add your custom styles here */
        body {
            padding: 20px;
        }
        .form-container {
            max-width: 400px;
            margin: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Budget Tracker</h1>
        <div class="form-container">
            <div id="set-budget">
                <h2 class="mb-3">Set Budget</h2>
                <div class="form-group">
                    <label for="total-budget">Enter Total Budget:</label>
                    <input type="number" id="total-budget" class="form-control" placeholder="Enter Total Budget">
                </div>
                <button onclick="setBudget()" class="btn btn-primary btn-block">Set Budget</button>
            </div>
            <div id="add-expense">
                <h2 class="mb-3">Add Expense</h2>
                <div class="form-group">
                    <label for="expense-amount">Enter Expense Amount:</label>
                    <input type="number" id="expense-amount" class="form-control" placeholder="Enter Expense Amount">
                </div>
                <div class="form-group">
                    <label for="expense-category">Select Category:</label>
                    <select id="expense-category" class="form-control">
                        <option value="Food">Food</option>
                        <option value="Transportation">Transportation</option>
                        <option value="Utilities">Utilities</option>
                        <option value="Entertainment">Entertainment</option>
                        <option value="Others">Others</option>
                    </select>
                </div>
                <button onclick="addExpense()" class="btn btn-success btn-block">Add Expense</button>
            </div>
            <div id="remaining-budget" class="mt-3">Remaining Budget: $${remaining_budget}</div>
            <div id="total-budget-value" class="mt-3">Total Budget: $${total_budget}</div>
            <div id="expenses">
                <h2 class="mt-4">Expenses</h2>
                <ul id="expense-list"></ul>
            </div>
        </div>
    </div>

    <script>
        function setBudget() {
            var totalBudget = document.getElementById('total-budget').value;
            console.log('Total Budget:', totalBudget); // Debugging statement
            var data = {
                'action': 'set_budget',
                'user_id': 1,  // Assuming user ID 1 for demo purposes, replace with actual user ID
                'amount': totalBudget
            };
            sendRequest(data);
        }

        function addExpense() {
            var expenseAmount = document.getElementById('expense-amount').value;
            var expenseCategory = document.getElementById('expense-category').value;
            console.log('Expense Amount:', expenseAmount); // Debugging statement
            console.log('Expense Category:', expenseCategory); // Debugging statement
            var data = {
                'action': 'add_expense',
                'user_id': 1,  // Assuming user ID 1 for demo purposes, replace with actual user ID
                'amount': expenseAmount,
                'category': expenseCategory
            };
            sendRequest(data);
        }

        function sendRequest(data) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        updatePage(response);
                    } else {
                        alert(response.message);
                    }
                }
            };
            xhr.send(JSON.stringify(data));
        }

        function updatePage(data) {
            console.log('Received data:', data); // Debugging statement
            document.getElementById('total-budget-value').innerText = 'Total Budget: ' + data.total_budget;
            document.getElementById('remaining-budget').innerText = 'Remaining Budget: ' + data.remaining_budget;
            var expenseList = document.getElementById('expense-list');
            expenseList.innerHTML = '';
            data.expenses.forEach(function(expense) {
                var li = document.createElement('li');
                li.textContent = 'Amount: $' + expense.amount + ', Category: ' + expense.category + ', Date: ' + expense.date;
                expenseList.appendChild(li);
            });
        }
    </script>
</body>
</html>
"""

# Set up the database connection
conn = psycopg2.connect(
    dbname='wad_exam',
    user='postgres',
    password='211201',
    host='localhost'
)
cur = conn.cursor()

# Create tables if they don't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        amount NUMERIC NOT NULL,
        category VARCHAR(255) NOT NULL,
        date DATE NOT NULL
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        amount NUMERIC NOT NULL
    )
""")
conn.commit()
def calculate_budget(user_id, month, year):
    # Get user's set budget
    cur.execute("""
        SELECT amount FROM budgets WHERE user_id = %s AND month = %s AND year = %s
    """, (user_id, month, year))
    budget_row = cur.fetchone()
    if budget_row:
        total_budget = float(budget_row[0])  # Convert to float
    else:
        total_budget = 0
    
    # Get expenses for the given month and year
    expenses = get_expenses(user_id, month, year)

    # Calculate total expenses
    total_expenses = sum(expense['amount'] for expense in expenses)

    # Calculate remaining budget
    remaining_budget = total_budget - total_expenses

    print('Total Budget:', total_budget)  # Debugging statement
    print('Remaining Budget:', remaining_budget)  # Debugging statement
    print('Expenses:', expenses)  # Debugging statement

    return total_budget, remaining_budget, expenses


def get_expenses(user_id, month, year):
    # Retrieve expenses for the given user, month, and year
    cur.execute("""
        SELECT amount, category, date FROM expenses WHERE user_id = %s AND EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
    """, (user_id, month, year))
    expenses_rows = cur.fetchall()

    # Convert Decimal objects to floats and format dates
    expenses = [{'amount': float(expense[0]), 'category': expense[1], 'date': expense[2].strftime('%Y-%m-%d')} for expense in expenses_rows]

    return expenses

class BudgetTrackerServer(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)

        action = data.get('action')
        if action == 'login':
            response = self.login(data)
        elif action == 'set_budget':
            response = self.set_budget(data)
        elif action == 'add_expense':
            response = self.add_expense(data)
        else:
            response = json.dumps({'success': False, 'message': 'Invalid action'})

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def login(self, data):
        email = data['email']
        password = data['password']
        cur.execute("""
            SELECT * FROM users WHERE email = %s AND password = %s
        """, (email, password))
        user = cur.fetchone()
        if user:
            return json.dumps({'success': True, 'message': 'Login successful'})
        else:
            return json.dumps({'success': False, 'message': 'Invalid email or password'})

    def set_budget(self, data):
        print('Received data:', data)  # Debugging statement
        user_id = data['user_id']
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        amount = data['amount']
        
        # Check if a budget already exists for the current month and year
        cur.execute("""
            SELECT id FROM budgets WHERE user_id = %s AND month = %s AND year = %s
        """, (user_id, month, year))
        existing_budget = cur.fetchone()

        if existing_budget:
            # Update the existing budget
            cur.execute("""
                UPDATE budgets SET amount = %s WHERE id = %s
            """, (amount, existing_budget[0]))
        else:
            # Insert a new budget
            cur.execute("""
                INSERT INTO budgets (user_id, month, year, amount) VALUES (%s, %s, %s, %s)
            """, (user_id, month, year, amount))

        conn.commit()

        # Retrieve updated expenses
        expenses = get_expenses(user_id, month, year)

        return json.dumps({'success': True, 'total_budget': amount, 'remaining_budget': amount, 'expenses': expenses})
    def add_expense(self, data):
        print('Received data:', data)  # Debugging statement
        user_id = data['user_id']
        amount = float(data['amount'])  # Convert amount to float
        category = data['category']
        date = datetime.datetime.now().date()

        print('user_id:', user_id)  # Debugging statement
        print('amount:', amount)    # Debugging statement
        print('category:', category)  # Debugging statement

        # Insert the new expense into the database
        cur.execute("""
            INSERT INTO expenses (user_id, amount, category, date) VALUES (%s, %s, %s, %s)
        """, (user_id, amount, category, date))
        conn.commit()

        # Retrieve updated expenses
        month = date.month
        year = date.year
        total_budget, remaining_budget, expenses = calculate_budget(user_id, month, year)

        return json.dumps({'success': True, 'total_budget': total_budget, 'remaining_budget': remaining_budget, 'expenses': expenses})


    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(LOGIN_PAGE_TEMPLATE.encode('utf-8'))
        elif self.path == '/home':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Assuming user_id is provided, calculate budget
            user_id = 1  # Replace with actual user_id
            month = datetime.datetime.now().month
            year = datetime.datetime.now().year
            total_budget, remaining_budget, expenses = calculate_budget(user_id, month, year)
            self.wfile.write(HOME_PAGE_TEMPLATE.replace('${total_budget}', str(total_budget)).replace('${remaining_budget}', str(remaining_budget)).replace('${expenses}', json.dumps(expenses)).encode('utf-8'))
        else:
            self.send_error(404, 'File not found')

# Set up the HTTP server
with socketserver.TCPServer(("", 12345), BudgetTrackerServer) as httpd:
    print("Server started at http://localhost:12345")
    httpd.serve_forever()
