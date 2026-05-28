"""交互式数据分析系统 — Flask 应用入口。"""

from flask import Flask, session, render_template, redirect, url_for, request
import os
import secrets

from data_cleaning import clean_bp, init_rules_dir

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")

    # 注册数据清洗蓝图
    app.register_blueprint(clean_bp)

    # 确保目录存在
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "outputs", "charts"), exist_ok=True)
    init_rules_dir()

    # 首页 — 重定向到数据上传页（由后端 A 负责，这里先做占位）
    @app.route("/")
    def index():
        error = request.args.get("error")
        user = session.get("user")
        return render_template("index.html", request=request, user=user, error=error)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)
