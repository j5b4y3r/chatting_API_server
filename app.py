from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

import json, os, datetime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Define the path to the JSON file
JSON_FILE = 'data.json'


def read_json_file():
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    return data


def write_json_file(data):
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password or not full_name:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if username in db:
        return jsonify({'success': False, 'error': 'Username already exists.'}), 400
    next_id = len(db) + 1
    user_id = f'{next_id:06d}'
    user_data = {'id': user_id, 'full_name': full_name, 'email': email, 'password': password,
                 'created': str(datetime.datetime.utcnow()), 'contacts': [], 'sent_messages': {},
                 'received_messages': {}}
    db[username] = user_data
    write_json_file(db)

    return jsonify({'success': True, 'message': 'User registered successfully.'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username_or_email')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if username not in db or db[username]['password'] != password:
        return jsonify({'success': False, 'error': 'Invalid username or password.'}), 401

    return jsonify({'success': True, 'message': 'Login successful.'}), 200


users = {}


@socketio.on('join_room')
def handle_join_room(data):
    # Store user's sid and room
    user_sid = request.sid
    user_room = data.get('room')
    users[user_sid] = user_room
    join_room(user_room)
    print(f"User {user_room} connected with SID: {user_sid}")
    print(users)


@socketio.on('disconnect')
def handle_disconnect():
    # Remove user's sid and room upon disconnection
    user_sid = request.sid
    if user_sid in users:
        user_room = users.pop(user_sid)
        leave_room(user_room)
        print(f"User {user_room} disconnected with SID: {user_sid}")


@socketio.on('send_message')
def send_message(data):
    password = data.get('password')
    sender_username = data.get('sender_username')
    recipient_username = data.get('recipient_username')
    message = data.get('message')

    if not sender_username or not recipient_username or not message:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if sender_username not in db or recipient_username not in db:
        return jsonify({'success': False, 'error': 'Sender or recipient not found.'}), 404
    if password != db[sender_username]['password']:
        return jsonify({'success': False, 'error': 'Authentication failed. Wrong user password!'}), 401

    sender_data = db[sender_username]
    recipient_data = db[recipient_username]

    # Update sent and received messages for sender and recipient
    current_time = str(datetime.datetime.utcnow())
    new_message = {"time": current_time, 'message': message, 'sender': sender_username}

    try:
        sender_data['sent_messages'][recipient_username].append(new_message)
    except KeyError:
        sender_data['sent_messages'][recipient_username] = [new_message]

    try:
        recipient_data['received_messages'][sender_username].append(new_message)
    except KeyError:
        recipient_data['received_messages'][sender_username] = [new_message]

    # Write updated data to JSON file
    db[sender_username] = sender_data
    db[recipient_username] = recipient_data
    write_json_file(db)

    try:
        # Emit message to recipient's room
        recipient_username_room = None
        for sid, room in users.items():
            if room == recipient_username:
                recipient_username_room = room
                break

        if recipient_username_room:
            socketio.emit('message', {'sender': sender_username, 'message': message, 'recipient': recipient_username},
                          room=recipient_username_room)
    except Exception as e:
        print(e)

    return jsonify({'success': True, 'message': 'Message sent successfully'}), 200


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    password = data.get('password')
    sender_username = data.get('sender_username')
    recipient_username = data.get('recipient_username')
    message = data.get('message')

    if not sender_username or not recipient_username or not message:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if sender_username not in db or recipient_username not in db:
        return jsonify({'success': False, 'error': 'Sender or recipient not found.'}), 404
    if password != db[sender_username]['password']:
        return jsonify({'success': False, 'error': 'Authentication failed. Wrong user password!'}), 401

    sender_data = db[sender_username]
    recipient_data = db[recipient_username]

    # Update sent and received messages for sender and recipient
    current_time = str(datetime.datetime.utcnow())
    new_message = {"time": current_time, 'message': message, 'sender': sender_username}

    try:
        sender_data['sent_messages'][recipient_username].append(new_message)
    except KeyError:
        sender_data['sent_messages'][recipient_username] = [new_message]

    try:
        recipient_data['received_messages'][sender_username].append(new_message)
    except KeyError:
        recipient_data['received_messages'][sender_username] = [new_message]

    # Write updated data to JSON file
    db[sender_username] = sender_data
    db[recipient_username] = recipient_data
    write_json_file(db)

    return jsonify({'success': True, 'message': 'Message sent successfully'}), 200


@app.route('/get_messages', methods=['GET'])
def get_messages():
    recipient_username = request.args.get('recipient_username')
    sender_username = request.args.get('sender_username')
    password = request.args.get('password')

    if not recipient_username:
        return jsonify({'success': False, 'error': 'Recipient parameter is missing.'}), 400

    db = read_json_file()
    if recipient_username not in db:
        return jsonify({'success': False, 'error': 'Recipient not found.'}), 404
    if password != db[sender_username]['password']:
        return jsonify({'success': False, 'error': 'Authentication Error. Wrong user password.'}), 401

    sender_data = db[sender_username]
    try:
        sent_messages = sender_data['sent_messages'][recipient_username]
    except KeyError:
        sent_messages = []

    try:
        received_messages = sender_data['received_messages'][recipient_username]
    except KeyError:
        received_messages = []

    return jsonify({'success': True, 'messages': {
        'sent_messages': sent_messages,
        'received_messages': received_messages
    }}), 200


@app.route('/delete_messages', methods=['POST'])
def delete_messages():
    data = request.get_json()
    username = data.get('username')
    message_index = data.get('message_index')
    recipient_username = data.get('recipient_username')
    password = data.get('password')

    if username is None or recipient_username is None or message_index is None:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if username not in db or recipient_username not in db:
        return jsonify({'success': False, 'error': 'User not found.'}), 404
    if db[username]['password'] != password:
        return jsonify({'success': False, 'error': 'Authentication failed. Wrong user password.'}), 401

    user_data = db[username]
    sent_messages = user_data['sent_messages']
    if recipient_username not in sent_messages:
        return jsonify({'success': False, 'error': 'No received messages found.'}), 404

    # Delete the message
    try:
        del sent_messages[recipient_username][int(message_index)]
        db[username]['sent_messages'] = sent_messages
        write_json_file(db)
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'messages': "Message index out of range."}), 404
    return jsonify({'success': True}), 200


@app.route('/add_contact', methods=['POST'])
def add_contact():
    data = request.get_json()
    own_username = data.get('own_username')
    contact_username = data.get('contact_username')

    if not own_username or not contact_username:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if own_username not in db:
        return jsonify({'success': False, 'error': 'User not found.'}), 404
    if contact_username not in db:
        return jsonify({'success': False, 'error': 'Contact not found.'}), 404

    user_data = db[own_username]
    contacts = user_data.get('contacts', [])
    if contact_username in contacts:
        return jsonify({'success': False, 'error': 'Contact already exists.'}), 400

    # Add contact
    contacts.append(contact_username)
    user_data['contacts'] = contacts
    db[own_username] = user_data
    write_json_file(db)

    return jsonify({'success': True, 'message': 'Contact added successfully'}), 200


@app.route('/get_contacts', methods=['GET'])
def get_contacts():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Required parameters is missing.'}), 400

    db = read_json_file()
    if username not in db:
        return jsonify({'success': False, 'error': 'User not found.'}), 404
    if db[username]['password'] != password:
        return jsonify({'success': False, 'error': 'Authentication failed. Wrong user password.'}), 401

    user_data = db[username]
    if 'contacts' not in user_data:
        return jsonify({'success': True, 'contacts': []}), 200

    contacts = user_data['contacts']
    return jsonify({'success': True, 'contacts': contacts}), 200


@app.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query')

    if not query:
        return jsonify({'success': False, 'error': 'Query parameter is missing.'}), 400

    db = read_json_file()
    results = []
    for username, user_data in db.items():
        if query in username or query in user_data.get('full_name', ''):
            results.append({'username': username, 'full_name': user_data.get('full_name', '')})

    return jsonify({'success': True, 'results': results}), 200


@app.route('/delete_contact', methods=['POST'])
def delete_contact():
    data = request.get_json()
    own_username = data.get('own_username')
    contact_username = data.get('contact_username')

    if not own_username or not contact_username:
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    db = read_json_file()
    if own_username not in db:
        return jsonify({'success': False, 'error': 'User not found.'}), 404
    if contact_username not in db:
        return jsonify({'success': False, 'error': 'Contact not found.'}), 404

    user_data = db[own_username]
    if 'contacts' not in user_data or contact_username not in user_data['contacts']:
        return jsonify({'success': False, 'error': 'Contact not in the contact list.'}), 400

    # Delete contact
    user_data['contacts'].remove(contact_username)
    db[own_username] = user_data
    write_json_file(db)

    return jsonify({'success': True, 'message': 'Contact deleted successfully'}), 200


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
