# JudgeX — Secure Online Judge System

JudgeX is a secure online judge platform that executes user-submitted code safely inside isolated environments.

It simulates real coding platforms by evaluating submissions against test cases while enforcing strict security and resource limits.

---

## 🚀 Features

### 🔐 Secure Code Execution
- Docker container sandboxing
- Process isolation
- Prevents host system access
- Safe execution of untrusted code

### ⚙️ Resource Control & Abuse Protection
- CPU usage limits
- Memory limits
- Execution timeouts
- Infinite loop protection

### 🧠 Asynchronous Job Processing
- Worker-based execution pipeline
- Queue-based submission handling
- Scalable architecture for concurrent submissions

### 👩‍💻 Platform Capabilities
- User authentication & role management
- Problem management system
- Code submission & verdict engine
- Admin controls

---

## 🏗️ How It Works

1. User submits code  
2. Submission enters processing queue  
3. Worker picks the job  
4. Code runs inside a Docker sandbox  
5. Output is validated against test cases  
6. Verdict is stored and returned  

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask

### Execution & Isolation
- Docker sandboxing

### Job Processing
- Worker-based execution pipeline

### Database & Migrations
- SQLAlchemy  
- Alembic  

---

## 📂 Project Structure

```text
app/
│
├── judge/        # sandbox execution & worker logic
├── routes/       # API routes
├── utils/        # helpers & state handling
├── models.py     # database models
├── extensions.py
│
migrations/       # database migrations
run.py            # application entry point
```
---

## 🧪 Future Improvements

- Multi-language code execution support  
- Kubernetes-based scaling  
- Web-based code editor  
- Real-time submission tracking  
- Plagiarism detection  
- Judge analytics dashboard  

---

## 🎯 Learning Outcomes

This project demonstrates:

- Secure sandboxed execution  
- Safe handling of untrusted code  
- Backend system design  
- Scalable job processing  
- Resource control & isolation  
- Real-world platform architecture  

---

## 👩‍💻 Author

**Shreya Baboota**

---

## ⭐ Support

If you found this project interesting, consider giving it a star ⭐