from flask import Flask, render_template, request
from sstv import sstv
import random
from datetime import datetime

app = Flask(__name__)

host = 'localhost'
port = 1234
debug = True

@app.route("/convert", methods=["POST"])
def convert():
    data = request.files['file']
    if data.filename != '':
        temp_name = f"static/temp/{datetime.now()}_{str(random.randint(0, 100000))}.png"
        path = f'static/temp/{data.filename}'
        data.save(path)
        decoder = sstv(path)
        decoder.decode(temp_name, 5, cast=False)
        return {"response": "success", "filepath": temp_name}
    else:
        return {"response": "error", "msg": "file not specified"}

@app.route("/")
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host=host, port=port, debug=debug)
