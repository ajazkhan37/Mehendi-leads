from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
import sqlite3
import mimetypes
import csv
import io
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Production-safe defaults; override via environment variables when deploying.
app.secret_key = os.environ.get('SECRET_KEY', 'mehendi-leads-secret-key-2024')
CORS(app)


DB_PATH = os.path.join(os.path.dirname(__file__), 'leads.db')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@mehendi.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
GALLERY_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'gallery')
ALLOWED_GALLERY_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

# Hero uploads (deploy-safe): store under uploads/ so they are available even if static asset collection is different per hosting.
HERO_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'hero')

# Backward-compat: old hero uploads may already exist under static/uploads/hero.
HERO_UPLOAD_FOLDER_LEGACY = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'hero')

os.makedirs(GALLERY_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HERO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HERO_UPLOAD_FOLDER_LEGACY, exist_ok=True)



def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-booking', methods=['POST'])
def submit_booking():
    try:
        data = request.get_json() or {}

        if not data.get('name') or not data.get('phone'):
            return jsonify({'success': False, 'message': 'Name and phone are required'}), 400

        allowed_status = {"New", "Contacted", "Booked", "Closed"}
        lead_status = data.get('lead_status', 'New') or 'New'
        if lead_status not in allowed_status:
            lead_status = 'New'

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO leads (
                name, phone, email, event_date, location, budget, additional_notes,
                pincode, whatsapp_number, full_address, event_type, lead_status, maps_link
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('phone'),
            data.get('email', ''),
            data.get('event_date', ''),
            data.get('location', ''),
            data.get('budget', ''),
            data.get('additional_notes', ''),
            data.get('pincode', ''),
            data.get('whatsapp_number', ''),
            data.get('full_address', ''),
            data.get('event_type', ''),
            lead_status,
            data.get('maps_link', '')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Booking submitted successfully!'}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin.html', page='login')

@app.route('/admin-login', methods=['POST'])
def admin_authenticate():
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin.html', page='dashboard')

@app.route('/api/leads')
@login_required
def api_leads():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leads ORDER BY created_at DESC')
        leads = cursor.fetchall()
        conn.close()

        leads_list = [dict(lead) for lead in leads]
        return jsonify(leads_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/export', methods=['POST'])
@login_required
def export_leads():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leads ORDER BY created_at DESC')
        leads = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 'Name', 'Phone', 'Email', 'Event Date', 'Location', 'Budget', 'Notes',
            'Pincode', 'WhatsApp Number', 'Full Address', 'Event Type', 'Lead Status', 'Maps Link',
            'Created At'
        ])

        for lead in leads:
            writer.writerow([
                lead['id'],
                lead['name'],
                lead['phone'],
                lead['email'] or '',
                lead['event_date'] or '',
                lead['location'] or '',
                lead['budget'] or '',
                lead['additional_notes'] or '',
                lead['pincode'] or '',
                lead['whatsapp_number'] or '',
                lead['full_address'] or '',
                lead['event_type'] or '',
                lead['lead_status'] or '',
                lead['maps_link'] or '',
                lead['created_at']
            ])

        csv_content = output.getvalue()
        output.close()

        return csv_content, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        }

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_lead_status(lead_id: int):
    try:
        data = request.get_json() or {}
        allowed_status = {"New", "Contacted", "Booked", "Closed"}

        new_status = data.get('lead_status', '')
        if new_status not in allowed_status:
            return jsonify({'success': False, 'message': 'Invalid lead_status'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE leads SET lead_status = ? WHERE id = ?',
            (new_status, lead_id)
        )
        conn.commit()

        # If id not found, cursor.rowcount may be 0
        updated = cursor.rowcount
        conn.close()

        if updated == 0:
            return jsonify({'success': False, 'message': 'Lead not found'}), 404

        return jsonify({'success': True, 'message': 'Lead status updated'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

def allowed_gallery_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in ALLOWED_GALLERY_EXTENSIONS


@app.route('/uploads/gallery/<path:filename>')
def uploaded_gallery_file(filename):
    # Serves uploaded gallery images from uploads/gallery
    return send_from_directory(GALLERY_UPLOAD_FOLDER, filename)


@app.route('/api/gallery-images', methods=['GET'])
def api_gallery_images():

    try:
        category = request.args.get('category', 'All') or 'All'
        conn = get_db_connection()
        cursor = conn.cursor()

        if category == 'All':
            cursor.execute(
                "SELECT id, image_path, category, created_at FROM gallery_images ORDER BY created_at DESC"
            )
        else:
            cursor.execute(
                "SELECT id, image_path, category, created_at FROM gallery_images WHERE category = ? ORDER BY created_at DESC",
                (category,),
            )

        rows = cursor.fetchall()
        conn.close()

        base_url = request.host_url.rstrip('/')
        images = []
        for r in rows:
            # image_path stored as filename (we generate unique names), served from /uploads/gallery/<filename>
            images.append({
                'id': r['id'],
                'image_url': f"{base_url}/uploads/gallery/{r['image_path']}",
                'category': r['category'],
                'created_at': r['created_at'],
            })

        return jsonify(images), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/gallery', methods=['GET'])
@login_required
def admin_gallery_page():
    return render_template('admin_gallery.html', page='gallery')


@app.route('/admin/hero-images', methods=['GET'])
@login_required
def admin_hero_images_page():
    return render_template('admin_hero.html', page='hero')



@app.route('/admin/gallery/upload', methods=['POST'])
@login_required
def admin_gallery_upload():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Image file missing'}), 400

        file = request.files['image']
        category = (request.form.get('category') or '').strip() or 'All'

        if not category:
            category = 'All'

        if not allowed_gallery_file(file.filename):
            return jsonify({'success': False, 'message': 'Unsupported file type'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower()
        filename = f"gallery_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}.{ext}"
        save_path = os.path.join(GALLERY_UPLOAD_FOLDER, filename)
        file.save(save_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gallery_images (image_path, category) VALUES (?, ?)",
            (filename, category),
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Image uploaded'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/gallery/delete/<int:image_id>', methods=['POST'])
@login_required
def admin_gallery_delete(image_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT image_path FROM gallery_images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': 'Image not found'}), 404

        cursor.execute("DELETE FROM gallery_images WHERE id = ?", (image_id,))
        conn.commit()
        conn.close()

        file_path = os.path.join(GALLERY_UPLOAD_FOLDER, row['image_path'])
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({'success': True, 'message': 'Image deleted'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/gallery/edit/<int:image_id>', methods=['POST'])
@login_required
def admin_gallery_edit(image_id: int):

    try:
        data = request.get_json() or {}
        category = (data.get('category') or '').strip() or 'All'
        if not category:
            return jsonify({'success': False, 'message': 'Category required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE gallery_images SET category = ? WHERE id = ?",
            (category, image_id),
        )
        conn.commit()

        updated = cursor.rowcount
        conn.close()

        if updated == 0:
            return jsonify({'success': False, 'message': 'Image not found'}), 404

        return jsonify({'success': True, 'message': 'Category updated'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# -------------------------
# Hero Banner Management
# -------------------------

def allowed_hero_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in ALLOWED_GALLERY_EXTENSIONS


@app.route('/uploads/hero/<path:filename>')
def uploaded_hero_file(filename):
    # Serve hero uploads from the deploy-safe folder first.
    file_path = os.path.join(HERO_UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_from_directory(HERO_UPLOAD_FOLDER, filename)

    # Backward-compat: serve from legacy static location if present.
    legacy_path = os.path.join(HERO_UPLOAD_FOLDER_LEGACY, filename)
    if os.path.exists(legacy_path):
        return send_from_directory(HERO_UPLOAD_FOLDER_LEGACY, filename)

    # If not found in either place, return 404.
    from flask import abort
    abort(404)


@app.route('/api/hero-image', methods=['GET'])
def api_active_hero_image():
    try:

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, image_path, created_at FROM hero_images WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'image_url': None}), 200

        base_url = request.host_url.rstrip('/')
        image_url = f"{base_url}/uploads/hero/{row['image_path']}"
        return jsonify({'image_url': image_url}), 200


    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hero-images', methods=['GET'])
@login_required
def api_hero_images_for_admin():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, image_path, is_active, created_at FROM hero_images ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        images = []
        for r in rows:
            images.append({
                'id': r['id'],
                'image_url': f"{request.host_url.rstrip('/')}/uploads/hero/{r['image_path']}",

                'is_active': int(r['is_active']),
                'created_at': r['created_at'],
            })

        return jsonify({'images': images}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/hero/upload', methods=['POST'])
@login_required
def admin_hero_upload():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Image file missing'}), 400

        file = request.files['image']
        if not allowed_hero_file(file.filename):
            return jsonify({'success': False, 'message': 'Unsupported file type'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower()
        filename = f"hero_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}.{ext}"
        save_path = os.path.join(HERO_UPLOAD_FOLDER, filename)
        file.save(save_path)


        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hero_images (image_path, is_active) VALUES (?, 0)",
            (filename,),
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Hero image uploaded'}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/hero/set-active/<int:hero_id>', methods=['POST'])
@login_required
def admin_hero_set_active(hero_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure hero exists
        cursor.execute("SELECT id FROM hero_images WHERE id = ?", (hero_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': 'Hero image not found'}), 404

        # Set selected as active and others inactive (single-active rule)
        cursor.execute("UPDATE hero_images SET is_active = 0")
        cursor.execute("UPDATE hero_images SET is_active = 1 WHERE id = ?", (hero_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Hero image set as active'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/hero/delete/<int:hero_id>', methods=['POST'])
@login_required
def admin_hero_delete(hero_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT image_path FROM hero_images WHERE id = ?", (hero_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': 'Hero image not found'}), 404

        cursor.execute("DELETE FROM hero_images WHERE id = ?", (hero_id,))
        conn.commit()
        conn.close()

        file_path = os.path.join(HERO_UPLOAD_FOLDER, row['image_path'])
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({'success': True, 'message': 'Hero image deleted'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('DEBUG', 'false').lower() in {'1','true','yes','on'}
    app.run(debug=debug, host=host, port=port)


