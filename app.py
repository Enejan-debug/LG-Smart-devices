"""
LG Store - Python/Flask rewrite.

HOW TO RUN (VS Code or any terminal, no Eclipse/Tomcat needed):
    1) pip install -r requirements.txt
    2) python app.py
    3) open http://127.0.0.1:5000 in your browser

That's it - Flask's built-in dev server hosts both the backend (routes,
database) and the frontend (HTML templates) together, so there is nothing
else to configure or deploy.
"""
from backend import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
