# Musify a Music Streaming Web Application

This web application allows users to upload their music, create playlists, and share them with others. Users can create an account to manage their songs and playlists, or they can listen to music without an account.

## Technology Stack

*   **Backend:** Flask
*   **Frontend:** Tailwind CSS

## Setup and Installation

### 1. Backend Configuration

**Create Environment File:**

Create a `.env` file in the `backend/` directory. This file will store your secret key.

```
SECRET_KEY='your-secret-key'
```

**Configuration Profiles:**

You can switch between different configuration profiles (e.g., development, production) by editing the `config_class` variable in the `backend/__init__.py` file. This also allows you to change the host IP and port.

### 2. Install Dependencies

**Python Packages:**

Install the required Python packages from the `requirements.txt` file using pip.

```bash
pip install -r requirements.txt
```

**Node.js Packages:**

Install the necessary Node.js packages from the `package.json` file using npm.

```bash
npm install
```

### 3. Frontend Development

To watch for changes in your CSS files and automatically update the output, run the following command:

```bash
npx @tailwindcss/cli -i ./static/src/input.css -o ./static/dist/output.css --watch
```

### 4. Database Seeding

To populate the database with test users and songs from the `tmp/` folder, use the following command:

```bash
python backend/manage.py
```

### 5. Running the Web Server

To start the web server, run the following command:

```bash
python run.py
```
