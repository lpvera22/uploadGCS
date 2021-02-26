from flask import Flask, request, json, Response, jsonify, abort, flash, request, redirect, url_for, send_file, \
    make_response, send_from_directory
import pandas as pd
from scripts.storage import upload_to_bucket
from flask_cors import CORS, cross_origin
from datetime import datetime
import ntpath
import os
from zipfile import ZipFile
from datetime import datetime
from werkzeug.utils import secure_filename
import requests
from firebase_admin import credentials, firestore, initialize_app

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Initialize Firestore DB
# cred = credentials.Certificate('key.json')
# default_app = initialize_app(cred)
# db = firestore.client()
# todo_ref = db.collection('todos')


UPLOAD_FOLDER = "upload/"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/api/', methods=['GET'])
@cross_origin()
def helloAPI():
    return " <h1 style='color:blue'>API ROOT!</h1>"


@app.route('/api/upload/files', methods=['POST'])
@cross_origin()
def uploaded():
    if 'files' not in request.files:
        flash('No file part')
        return jsonify('no')

    # user = request.form['user']
    files = request.files.getlist('files')
    if len(files) == 1:
        file = files[0]

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            path_to_file = os.path.join(UPLOAD_FOLDER + '/' + filename)

        url = upload_to_bucket(filename, path_to_file, 'gcs_project')
        # urlSend = 'https://webhook.site/846f3158-3205-4f03-9f87-9411b1f3b8f7'
        # myobj = {'url': url,'user':user}

        # x = requests.post(urlSend, data = myobj)
        return jsonify({'url': url})
    else:
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        zipObj = ZipFile(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '.zip', 'w')
        for f in files:
            filename = secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER + 'to_zip/', filename))
            path = os.path.join(UPLOAD_FOLDER + '/to_zip/', filename)
            zipObj.write(path)
        zipObj.close()
        url = upload_to_bucket(str(timestamp) + '.zip', UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '.zip',
                               'gcs_project')
        # urlSend = 'https://webhook.site/846f3158-3205-4f03-9f87-9411b1f3b8f7'
        # myobj = {'url':url,'user':user}

        # x = requests.post(urlSend, data = myobj)
        return jsonify({'url': url})


@app.route('/api/upload/', methods=['POST'])
@cross_origin()
def u():
    toDownload = request.get_json()['url']
    r = requests.get(toDownload, allow_redirects=True)
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    firstpos = toDownload.rfind("/")
    lastpos = len(toDownload)

    filename = toDownload[firstpos + 1:lastpos]
    os.mkdir(UPLOAD_FOLDER + str(timestamp) + '/')
    open(UPLOAD_FOLDER + str(timestamp) + '/' + filename, 'wb').write(r.content)
    url = upload_to_bucket(filename, UPLOAD_FOLDER + str(timestamp) + '/' + filename, 'gcs_project')

    return jsonify({'url': url})

    # return jsonify(toDownload)


@app.route('/api/to_zip', methods=['POST'])
@cross_origin()
def to_zip():
    files = request.files.getlist('files')
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    zipObj = ZipFile(str(timestamp) + '.zip', 'w')
    for f in files:
        filename = secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER + 'to_zip/', filename))
        path = os.path.join(UPLOAD_FOLDER + '/to_zip/', filename)
        zipObj.write(path)
    zipObj.close()
    return send_from_directory(UPLOAD_FOLDER + 'to_zip/', str(timestamp) + '.zip', as_attachment=True)


@app.route('/api/upload/files_text', methods=['POST'])
@cross_origin()
def upload():
    files = request.get_json()['files']
    files = files.split(",")
    if len(files) > 1:
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        os.mkdir(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/')
        # zipObj = ZipFile(UPLOAD_FOLDER+'to_zip/'+str(timestamp)+'/'+str(timestamp)+'.zip', 'w')
        zipObj = ZipFile(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/' + str(timestamp) + '.zip', 'w')
        for url in files:
            r = requests.get(url, allow_redirects=True)

            firstpos = url.rfind("/")
            lastpos = len(url)
            filename = url[firstpos + 1:lastpos]

            open(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/' + filename, 'wb').write(r.content)
            absname = os.path.abspath(os.path.join(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/', filename))
            abs_src = os.path.abspath(UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/')
            arcname = absname[len(abs_src) + 1:]
            zipObj.write(absname, arcname)
        zipObj.close()
        url = upload_to_bucket(str(timestamp) + '.zip',
                               UPLOAD_FOLDER + 'to_zip/' + str(timestamp) + '/' + str(timestamp) + '.zip',
                               'gcs_project')
        return jsonify({'url': url})
    else:
        file = files[0]
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        r = requests.get(file, allow_redirects=True)

        firstpos = file.rfind("/")
        lastpos = len(file)
        filename = file[firstpos + 1:lastpos]
        os.mkdir(UPLOAD_FOLDER + str(timestamp) + '/')
        open(UPLOAD_FOLDER + str(timestamp) + '/' + filename, 'wb').write(r.content)
        url = upload_to_bucket(filename, UPLOAD_FOLDER + str(timestamp) + '/' + filename, 'gcs_project')
        return jsonify({'url': url})


if __name__ == '__main__':
    app.secret_key = os.urandom(24)

    # host='0.0.0.0',debug=True,ssl_context=('cert.pem', 'key.pem')

    app.run(host='0.0.0.0', debug=True, port=int(os.environ.get('PORT', 8080)))
