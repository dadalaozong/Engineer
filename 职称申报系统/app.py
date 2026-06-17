"""Flask entry point — 职称申报系统 Web版"""
from flask import Flask
from database.db import init_db

app = Flask(__name__)
app.secret_key = "zcsbxt-local-secret-2024"

from routes.dashboard  import bp as dashboard_bp
from routes.applicants import bp as applicants_bp
from routes.projects   import bp as projects_bp
from routes.batches    import bp as batches_bp
from routes.fees       import bp as fees_bp
from routes.docs       import bp as docs_bp
from routes.ocr        import bp as ocr_bp
from routes.ai_writer  import bp as ai_writer_bp
from routes.img_proc   import bp as img_proc_bp
from routes.auto_fill  import bp as auto_fill_bp
from routes.settings   import bp as settings_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(applicants_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(batches_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(docs_bp)
app.register_blueprint(ocr_bp)
app.register_blueprint(ai_writer_bp)
app.register_blueprint(img_proc_bp)
app.register_blueprint(auto_fill_bp)
app.register_blueprint(settings_bp)

if __name__ == "__main__":
    init_db()
    print("职称申报系统已启动，请访问 http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
