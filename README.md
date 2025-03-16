Below is an updated **README.md** that reflects the full scope of the project as found in the contents of **tasklist.zip**, integrating the previous explanation with new features such as real-time notifications, task sharing, and a dashboard with visual charts.

# Task Management System

This is a web-based **Task Management System** built with **Django** and **SQLite3** (configurable for PostgreSQL) that allows users to register, log in, and efficiently manage tasks. Key features include task creation, updates, deletions, sharing tasks among multiple users, real-time notifications using **Django Channels**, and a dashboard with visual charts.

---

## Features

1. **User Authentication**  
   - User registration  
   - Login/Logout functionality  
   - Only logged-in users can access their tasks  

2. **Task Management**  
   - Create new tasks (with title, description, status, due date)  
   - Edit existing tasks  
   - Delete tasks  
   - Search tasks by title or description  
   - Filter tasks by status (Pending, In Progress, Completed)  
   - Track completion progress with a dynamic progress bar  

3. **Task Sharing**  
   - Share specific tasks with other users  
   - Add or remove users from a shared task  
   - Shared users can be notified when tasks are updated or assigned to them  

4. **Real-Time Notifications**  
   - Powered by **Django Channels** and **Redis**  
   - Users receive live notifications for events such as:  
     - Being added to or removed from a shared task  
     - Task status updates  
     - New tasks assigned  
   - Notifications can be viewed in a dedicated notifications page  

5. **Dashboard with Visual Insights**  
   - Provides an overview of personal task progress  
   - Displays task completion rate and overdue tasks  
   - Renders a **pie chart** (generated with **matplotlib**) for task status distribution  
   - Designed for potential expansion (e.g., weekly trends, due date trends)  

6. **Responsive UI**  
   - Built with **HTML/CSS** and **Bootstrap** for a clean and user-friendly interface  

---

## Requirements & Installation

1. **Python** (3.10+ recommended)
2. Clone this repository or download the source code.
3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On macOS/Linux
   # or
   venv\Scripts\activate      # On Windows
   ```
4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
5. **Redis** should be running locally on port `6379` (default). If Redis is not running, real-time notifications via WebSockets will not function.

6. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   If you want to use **Daphne** (recommended for production-like testing with Channels):
   ```bash
   daphne -b 0.0.0.0 -p 8000 tasklist.asgi:application
   ```

7. Open your browser to `http://127.0.0.1:8000/` (or `http://localhost:8000/`) to use the application.

---

## Usage

1. **Home Page**  
   - After logging in, you are redirected to the **Home Page**.  
   - Here you can see all tasks you own, filter them by status, or search them by title/description.  
   - The progress bar shows the percentage of **completed** tasks.

2. **Create a Task**  
   - Navigate to the **New Task** button to create a fresh task with a due date and initial status.

3. **Edit or Delete a Task**  
   - Click on any existing task to edit.  
   - You can also delete a task entirely (only if you are the task owner).

4. **Share a Task**  
   - From the task’s detail or share interface, you can invite other users by username.  
   - Those users will see the task under their **Shared Tasks** and receive a real-time notification.

5. **Real-Time Notifications**  
   - A WebSocket connection ensures that you see new notifications instantly.  
   - View your notifications in the **Notifications** page.

6. **Dashboard**  
   - Provides an overview of your tasks, including completion percentage, overdue tasks, and a pie chart of tasks by status.

---

## File Structure

Below is an overview of the main directories and files (within the `tasklist` project folder):

```bash
tasklist/
├── authentication/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── core/
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py         # WebSocket consumers for real-time notifications
│   ├── forms.py
│   ├── migrations/
│   ├── models.py            # Task & Notification models
│   ├── routing.py           # Defines websocket_urlpatterns
│   ├── tests.py
│   ├── urls.py
│   └── views.py             # Task CRUD, sharing, and dashboard views
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── websocket.js     # Front-end WebSocket script for notifications
│
├── templates/
│   ├── authentication/
│   │   ├── login.html
│   │   └── register.html
│   ├── core/
│   │   ├── dashboard.html
│   │   ├── home.html
│   │   ├── notifications.html
│   │   ├── share_task.html
│   │   ├── task_create.html
│   │   └── task_form.html
│   └── partials/
│       └── base.html
│
├── tasklist/
│   ├── asgi.py              # ASGI config for Django Channels
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── db.sqlite3               # SQLite Database (default)
├── requirements.txt         # Python dependencies
├── manage.py
└── README.md
```

---

## Technologies Used

- **Python 3.10+**  
- **Django 4.x**  
- **Django Channels** (for real-time notifications)  
- **SQLite3** (configurable to PostgreSQL)  
- **Redis** (Channels backend)  
- **HTML/CSS & Bootstrap** (frontend layout and styling)  
- **Matplotlib** (pie chart generation on the dashboard)  
- **Daphne** / **Gunicorn** (production-ready server options)

---

## Screenshots

### **Home Page:**
![Home Page Screenshot](./screenshots/home_page.png)

### **Task Create Page:**
![Task Create Page Screenshot](./screenshots/task_create_page.png)

### **Register Page:**
![Register Page Screenshot](./screenshots/register_page.png)

*(Additional screenshots can be placed in the `screenshots/` folder.)*

---

## Deployment

For production deployment:
1. Use a production-level web server with ASGI support (e.g., Daphne or Uvicorn).
2. Configure a robust database (e.g., PostgreSQL). Update `DATABASES` in **settings.py** or use `dj-database-url` with environment variables.
3. Ensure **Redis** is installed and running for Channels.
4. Serve static files with a proper solution (e.g., **WhiteNoise** or object storage/CDN).
5. Set `DEBUG = False` and provide a secure `SECRET_KEY`.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

---

### Notable Updates & Additions
- **Task Sharing**: Grant other users access to your tasks, with real-time notifications on changes.  
- **Real-Time Notifications**: Implemented via **Django Channels** and **Redis**.  
- **Dashboard**: Visual overview of your tasks, including status distribution charts.  
- **Expanded Requirements**: Now includes `channels`, `channels-redis`, `daphne`, `redis`, `matplotlib`, and optional `psycopg2-binary` for PostgreSQL.

This updated README includes all previously documented functionality alongside newly integrated features, ensuring it is **100% accurate** to the current codebase.
