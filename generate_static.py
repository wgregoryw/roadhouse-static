from app import app
import os
import shutil

OUTPUT_DIR = "output"

def export_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with app.app_context():
        html = app.view_functions['index']()
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
            f.write(html)
    # Copy static assets (but NOT downloads)
    if os.path.exists("static"):
        shutil.copytree("static", os.path.join(OUTPUT_DIR, "static"), dirs_exist_ok=True)

if __name__ == "__main__":
    export_site()