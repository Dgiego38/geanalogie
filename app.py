from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def upload():
    return render_template("upload.html")

@app.route("/menu")
def menu():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

if __name__ == "__main__":
    app.run(debug=False)