import os
from flask import Flask, render_template, flash, request, redirect
from werkzeug.utils import secure_filename
import ocr
import lineSweep
import svm


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
OCR_RESULTS_FOLDER = os.path.join(BASE_DIR, "static", "OCR_Results")
LINESWEEP_RESULTS_FOLDER = os.path.join(BASE_DIR, "static", "LineSweep_Results")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_runtime_dirs():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(OCR_RESULTS_FOLDER, exist_ok=True)
    os.makedirs(LINESWEEP_RESULTS_FOLDER, exist_ok=True)


def clear_directory(path):
    if not os.path.isdir(path):
        return
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if os.path.isfile(file_path):
            os.remove(file_path)


ensure_runtime_dirs()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/reload")
def reload_page():
    clear_directory(app.config["UPLOAD_FOLDER"])
    clear_directory(OCR_RESULTS_FOLDER)
    clear_directory(LINESWEEP_RESULTS_FOLDER)
    return redirect("/")


@app.route("/process_ocr", methods=["POST"])
def process_image():
    # Run full pipeline before verification so fresh clones work end-to-end.
    ocr.ocr_algo()
    lineSweep.lineSweep_algo()
    result = svm.svm_algo()

    if result == "No test images":
        return render_template("home.html", result="No processed signature found")
    if result == "Genuine":
        return render_template("home.html", result="Genuine Signature")
    return render_template("home.html", result="Forged Signature")


@app.route("/predict", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)
    if file and allowed_file(file.filename):
        ensure_runtime_dirs()
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        flash("Image successfully uploaded")
        return render_template("home.html", filename=filename)
    flash("Allowed image types are - png, jpg, jpeg, gif")
    return redirect(request.url)


if __name__ == "__main__":
    app.run(debug=True)
