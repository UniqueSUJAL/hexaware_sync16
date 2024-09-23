from flask import render_template, request, redirect, url_for, flash, session
import mysql.connector
import os
from . import auth_routes  # Import the Blueprint from __init__.py

# Function to connect to MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="root",  # Replace with your MySQL password
        database="user_registration_db"
    )
    return connection

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# List all curricula for the trainer
@auth_routes.route('/curriculum', methods=['GET'])
def list_curriculum():
    if 'role' in session and session['role'] == 'Trainers':
        user_id = session['user_id']  # Assuming you store user_id in session
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Curriculum WHERE trainer_id = %s", (user_id,))
        curricula = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('curriculum.html', curricula=curricula)
    else:
        flash("Unauthorized access.", 'error')
        return redirect(url_for('auth_routes.login'))

# Upload curriculum
@auth_routes.route('/curriculum/upload', methods=['POST'])
def upload_curriculum():
    if 'role' in session and session['role'] == 'Trainers':
        file = request.files.get('file')
        if file and file.filename:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            user_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Curriculum (trainer_id, filename, file_path) VALUES (%s, %s, %s)",
                           (user_id, file.filename, file_path))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Curriculum uploaded successfully.', 'success')
        else:
            flash('No file selected.', 'error')
        return redirect(url_for('auth_routes.list_curriculum'))
    else:
        flash("Unauthorized access.", 'error')
        return redirect(url_for('auth_routes.login'))

# # Edit curriculum
# @auth_routes.route('/curriculum/edit/<int:curriculum_id>', methods=['GET', 'POST'])
# def edit_curriculum(curriculum_id):
#     if 'role' in session and session['role'] == 'Trainers':
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
        
#         if request.method == 'POST':
#             new_filename = request.form['filename']
#             cursor.execute("UPDATE Curriculum SET filename = %s WHERE id = %s", 
#                            (new_filename, curriculum_id))
#             conn.commit()
#             flash('Curriculum updated successfully.', 'success')
#             return redirect(url_for('auth_routes.list_curriculum'))
        
#         cursor.execute("SELECT * FROM Curriculum WHERE id = %s", (curriculum_id,))
#         curriculum = cursor.fetchone()
#         cursor.close()
#         conn.close()
        
#         return render_template('edit_curriculum.html', curriculum=curriculum)
#     else:
#         flash("Unauthorized access.", 'error')
#         return redirect(url_for('auth_routes.login'))

# Delete curriculum
@auth_routes.route('/curriculum/delete/<int:curriculum_id>', methods=['POST'])
def delete_curriculum(curriculum_id):
    if 'role' in session and session['role'] == 'Trainers':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)  # Use dictionary=True to return results as dictionaries
            cursor.execute("SELECT filename FROM Curriculum WHERE id = %s", (curriculum_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = os.path.join("uploads", result['filename'])  # Build the file path
                if os.path.exists(file_path):
                    os.remove(file_path)  # Remove the file from the filesystem
                else:
                    flash('File not found on server.', 'error')
                
                cursor.execute("DELETE FROM Curriculum WHERE id = %s", (curriculum_id,))
                conn.commit()
                flash('Curriculum deleted successfully.', 'success')
            else:
                flash('Curriculum not found.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('auth_routes.list_curriculum'))
    else:
        flash("Unauthorized access.", 'error')
        return redirect(url_for('auth_routes.login'))


# Login route
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in both fields.', 'error')
            return redirect(url_for('auth_routes.login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                session['name'] = user['name']
                session['role'] = user['role']
                session['user_id'] = user['id']  # Save user ID in session
                flash('Welcome to the dashboard!', 'success')
                return redirect(url_for('auth_routes.dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                return redirect(url_for('auth_routes.login'))

        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
            return redirect(url_for('auth_routes.login'))

    return render_template('login.html')

# Logout route
@auth_routes.route('/logout')
def logout():
    session.pop('name', None)
    session.pop('role', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_routes.login'))

# Dashboard route
@auth_routes.route('/dashboard')
def dashboard():
    if 'role' in session:
        user_name = session.get('name', 'User')
        user_role = session.get('role', 'Role')
        
        if user_role == 'Trainers':
            return render_template('dashboard.html', user_name=user_name, user_role=user_role, dashboard_type='Trainers')
        elif user_role == 'Admin':
            return render_template('dashboard.html', user_name=user_name, user_role=user_role, dashboard_type='Admin')
        elif user_role == 'Employee':
            return render_template('dashboard.html', user_name=user_name, user_role=user_role, dashboard_type='Employee')
        else:
            flash('Invalid role.', 'error')
            return redirect(url_for('auth_routes.login'))
    else:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('auth_routes.login'))

# Register route
@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        role = request.form.get('role')  # Assuming you select role from options (Trainer, Admin, Employee)

        if not name or not email or not password or not phone_number or not role:
            flash('All fields are required!', 'error')
            return redirect(url_for('auth_routes.register'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email already registered.', 'error')
                return redirect(url_for('auth_routes.register'))

            # Insert new user
            cursor.execute("INSERT INTO users (name, email, password, phone_number, role) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, password, phone_number, role))
            conn.commit()
            cursor.close()
            conn.close()

            flash('Successfully registered!', 'success')
            return redirect(url_for('auth_routes.login'))

        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'error')
            return redirect(url_for('auth_routes.register'))

    return render_template('register.html')


# View curriculum (PDF, CSV)
@auth_routes.route('/curriculum/view/<int:curriculum_id>', methods=['GET'])
def view_curriculum(curriculum_id):
    if 'role' in session and session['role'] == 'Trainers':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT filename FROM Curriculum WHERE id = %s", (curriculum_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            file_path = os.path.join(UPLOAD_FOLDER, result['filename'])
            file_extension = os.path.splitext(result['filename'])[1].lower()

            # Render a specific template based on file type
            if file_extension == '.pdf':
                return render_template('view_pdf.html', file_path=file_path)
            elif file_extension == '.csv':
                return render_template('view_csv.html', file_path=file_path)
            else:
                flash('Unsupported file format for viewing.', 'error')
                return redirect(url_for('auth_routes.list_curriculum'))
        else:
            flash('Curriculum not found.', 'error')
            return redirect(url_for('auth_routes.list_curriculum'))
    else:
        flash("Unauthorized access.", 'error')
        return redirect(url_for('auth_routes.login'))
# # Edit curriculum (CSV)
# @auth_routes.route('/curriculum/edit/<int:curriculum_id>', methods=['GET', 'POST'])
# def edit_curriculum(curriculum_id):
#     if 'role' in session and session['role'] == 'Trainers':
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT filename FROM Curriculum WHERE id = %s", (curriculum_id,))
#         result = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if result:
#             file_path = os.path.join(UPLOAD_FOLDER, result['filename'])
#             file_extension = os.path.splitext(result['filename'])[1].lower()

#             if request.method == 'POST':
#                 if file_extension == '.csv':
#                     # Save the edited CSV content
#                     new_content = request.form['csv_content']
#                     with open(file_path, 'w') as f:
#                         f.write(new_content)
#                     flash('Curriculum updated successfully.', 'success')
#                     return redirect(url_for('auth_routes.list_curriculum'))
#             else:
#                 if file_extension == '.csv':
#                     # Read CSV content for editing
#                     with open(file_path, 'r') as f:
#                         csv_content = f.read()
#                     return render_template('edit_csv.html', csv_content=csv_content)
#                 else:
#                     flash('Unsupported file format for editing.', 'error')
#                     return redirect(url_for('auth_routes.list_curriculum'))
#         else:
#             flash('Curriculum not found.', 'error')
#             return redirect(url_for('auth_routes.list_curriculum'))
#     else:
#         flash("Unauthorized access.", 'error')
        # return redirect(url_for('auth_routes.login'))
@auth_routes.route('/curriculum/edit/<int:curriculum_id>', methods=['GET', 'POST'])
def edit_curriculum(curriculum_id):
    if 'role' in session and session['role'] == 'Trainers':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT filename FROM Curriculum WHERE id = %s", (curriculum_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            file_path = os.path.join(UPLOAD_FOLDER, result['filename'])
            file_extension = os.path.splitext(result['filename'])[1].lower()

            if request.method == 'POST':
                if file_extension == '.csv':
                    new_content = request.form['csv_content']
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    flash('Curriculum updated successfully.', 'success')
                    return redirect(url_for('auth_routes.list_curriculum'))
            else:
                if file_extension == '.csv':
                    with open(file_path, 'r') as f:
                        csv_content = f.read()
                    return render_template('edit_csv.html', csv_content=csv_content)
                else:
                    flash('Unsupported file format for editing.', 'error')
                    return redirect(url_for('auth_routes.list_curriculum'))
        else:
            flash('Curriculum not found.', 'error')
            return redirect(url_for('auth_routes.list_curriculum'))
    else:
        flash("Unauthorized access.", 'error')
        return redirect(url_for('auth_routes.login'))






