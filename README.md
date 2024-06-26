
# Messaging Application API Documentation

## Introduction

The Messaging Application API allows users to register, login, send and receive messages, manage contacts, and perform other related tasks. It provides both RESTful HTTP endpoints and WebSocket functionality for real-time messaging.

## Base URL

```
http://localhost:5000/
```

## Authentication

Some endpoints require authentication using the user's password. This is done to ensure secure access to sensitive operations such as sending messages and managing contacts.

## Endpoints

### 1. Register

#### URL
```
/register
```

#### Method
```
POST
```

#### Description
Registers a new user in the messaging application.

#### Request Body
- `username` (string, required): The username of the new user.
- `full_name` (string, required): The full name of the new user.
- `email` (string, required): The email address of the new user.
- `password` (string, required): The password of the new user.

#### Example Usage
```http
POST /register HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
    "username": "newuser",
    "full_name": "New User",
    "email": "newuser@example.com",
    "password": "password123"
}
```

#### Response
```json
{
    "success": true,
    "message": "User registered successfully."
}
```

#### Explanation
Registers a new user with the provided username, full name, email, and password. Upon successful registration, the server responds with a success message.

### 2. Login

#### URL
```
/login
```

#### Method
```
POST
```

#### Description
Logs in an existing user.

#### Request Body
- `username_or_email` (string, required): The username or email of the user.
- `password` (string, required): The password of the user.

#### Example Usage
```http
POST /login HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
    "username_or_email": "existinguser",
    "password": "password123"
}
```

#### Response
```json
{
    "success": true,
    "message": "Login successful."
}
```

#### Explanation
Authenticates the user with the provided username or email and password. Upon successful authentication, the server responds with a success message.

### 3. Send Message

#### URL
```
/send_message
```

#### Method
```
POST
```

#### Description
Sends a message from one user to another.

#### Request Body
- `sender_username` (string, required): The username of the sender.
- `recipient_username` (string, required): The username of the recipient.
- `password` (string, required): The password of the sender.
- `message` (string, required): The message content.

#### Example Usage
```http
POST /send_message HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
    "sender_username": "user1",
    "recipient_username": "user2",
    "password": "password123",
    "message": "Hello, how are you?"
}
```

#### Response
```json
{
    "success": true,
    "message": "Message sent successfully."
}
```

#### Explanation
Sends a message from the sender to the recipient with the provided message content. Authentication is required for the sender. Upon successful sending of the message, the server responds with a success message.

### 4. Get Messages

#### URL
```
/get_messages
```

#### Method
```
GET
```

#### Description
Gets messages between two users.

#### Query Parameters
- `sender_username` (string, required): The username of the sender.
- `recipient_username` (string, required): The username of the recipient.
- `password` (string, required): The password of the sender.

#### Example Usage
```http
GET /get_messages?sender_username=user1&recipient_username=user2&password=password123 HTTP/1.1
Host: localhost:5000
```

#### Response
```json
{
    "success": true,
    "messages": {
        "sent_messages": [],
        "received_messages": []
    }
}
```

#### Explanation
Retrieves sent and received messages between the sender and recipient. Authentication is required for the sender. The server responds with an object containing arrays of sent and received messages.
```
