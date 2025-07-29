from flask import Flask, render_template, request, redirect, url_for
import os
import smtplib
from email.message import EmailMessage
from flask import send_from_directory

app = Flask(__name__)

# ---------- EXPENSE CALCULATOR LOGIC ----------
def calculate_settlements(friends, amounts):
    num_people = len(friends)
    total_spent = sum(amounts)
    equal_share = round(total_spent / num_people, 2)
    balances = {name: round(paid - equal_share, 2) for name, paid in zip(friends, amounts)}
    creditors, debtors = [], []

    for name, balance in balances.items():
        if balance > 0:
            creditors.append([name, balance])
        elif balance < 0:
            debtors.append([name, -balance])

    settlements = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        payment = min(debt, credit)
        settlements.append(f"{debtor} owes {creditor} ₹{payment:.2f}")
        debtors[i][1] -= payment
        creditors[j][1] -= payment
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return settlements

@app.route("/")
def homepage():
    return render_template("test.html")

@app.route("/expense", methods=["GET", "POST"])
def expense():
    settlements, friends, amounts = [], [], []
    if request.method == "POST":
        friends = request.form.getlist("friend")
        try:
            amounts = [float(a) for a in request.form.getlist("amount")]
        except ValueError:
            return render_template("expense.html", settlements=["Invalid amount entered."], friends=friends, amounts=request.form.getlist("amount"))
        settlements = calculate_settlements(friends, amounts)
    return render_template("expense.html", settlements=settlements, friends=friends, amounts=amounts)

# ---------- INVITE LOGIC ----------
@app.route("/invite", methods=["GET", "POST"])
def invite():
    email_status = []
    if request.method == "POST":
        sender = request.form.get("sender")
        date = request.form.get("date")
        place = request.form.get("place")
        time = request.form.get("time")

        guests = zip(request.form.getlist("guest_name"), request.form.getlist("guest_email"))

        for name, email in guests:
            success = send_email(email, name, place, date, time, sender)
            if success:
                email_status.append(f"Email sent to {name} at {email}!")
            else:
                email_status.append(f"Failed to send email to {name}.")

    return render_template("invite.html", status=email_status)

def send_email(to_email, friend_name, place, date, time, sender_name):
    msg = EmailMessage()
    msg['Subject'] = "Let's Hang Out!"
    msg['From'] = "Hangout Planner <no-reply@yourapp.com>"
    msg['To'] = to_email
    body = f"""Hi {friend_name},

I hope you're doing great! I was thinking it would be fun to catch up and hang out for a bit.
How about we meet at {place} on {date} at {time}?

Looking forward to it!

Best,
{sender_name}"""
    msg.set_content(body)
    try:
        with smtplib.SMTP('in-v3.mailjet.com', 587) as server:
            server.starttls()
            server.login("29c711f3c66e5a13a2ca6537b9d35a5e", "81c012d09e3bb5ebae3f70775103eaee")
            server.send_message(msg)
            return True
    except Exception as e:
        print("Error occurred:", e)
        return False

# ---------- GALLERY IMAGE UPLOAD ----------
UPLOAD_FOLDER = 'static/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('gallery'))
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    images = [f for f in files if allowed_file(f)]
    return render_template('gallery.html', images=images)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
