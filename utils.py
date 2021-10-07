import os
import shutil
import tempfile
import time
from datetime import datetime, timezone

import cv2
import numpy as np
from PIL import Image
from GPSPhoto import gpsphoto

from skimage.transform import resize
from keras.models import load_model

from db_driver import insert_lion_data, match_lion, get_base64_str
from lion_model import LionDetection, classes


lion_model = LionDetection()
keras_model_path = os.path.join('models', 'facenet_keras.h5')
keras_model = load_model(keras_model_path)
keras_model._make_predict_function()
print("Model Init Done!")


def current_milli_time():
    return round(time.time() * 1000)


def prewhiten(x):
    if x.ndim == 4:
        axis = (1, 2, 3)
        size = x[0].size
    elif x.ndim == 3:
        axis = (0, 1, 2)
        size = x.size
    else:
        raise ValueError('Dimension should be 3 or 4')

    mean = np.mean(x, axis=axis, keepdims=True)
    std = np.std(x, axis=axis, keepdims=True)
    std_adj = np.maximum(std, 1.0/np.sqrt(size))
    y = (x - mean) / std_adj
    return y


def load_and_align_images(images):
    aligned_images = []
    for image in images:
        cropped = image
        image_size = 160

        aligned = resize(cropped, (image_size, image_size), mode='reflect')
        aligned_images.append(aligned)

    return np.array(aligned_images)


def l2_normalize(x, axis=-1, epsilon=1e-10):
    output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
    return output


def calculate_embeddings(images, batch_size=1):
    aligned_images = prewhiten(load_and_align_images(images))
    pd = list()
    for start in range(0, len(aligned_images), batch_size):
        x = aligned_images[start:start + batch_size]
        pd.append(keras_model.predict_on_batch(x))
    embeddings = l2_normalize(np.concatenate(pd))
    return embeddings


def extract_lion_data(face_cords, lion, pil_img, coordinates, tmp_dir, temp_image):
    lion_path = ''
    face_path = ''
    whisker_path = ''
    lear_path = ''
    rear_path = ''
    leye_path = ''
    reye_path = ''
    nose_path = ''
    face_embedding = ''
    whisker_embedding = ''
    for face_coord in face_cords[lion]['boxes']:
        if face_coord["conf"] > 0.7:
            _coordinates = []
            face = pil_img.copy()
            leye = pil_img.copy()
            reye = pil_img.copy()
            lear = pil_img.copy()
            rear = pil_img.copy()
            nose = pil_img.copy()
            whisker = pil_img.copy()
            for coord in coordinates['boxes']:
                if lion_model.insideface(face_coord, coord):
                    _coordinates.append(coord)
                    roi_box = coord['ROI']
                    xmin = int(roi_box[0])
                    ymin = int(roi_box[1])
                    xmax = int(roi_box[2])
                    ymax = int(roi_box[3])
                    temp_image = cv2.rectangle(temp_image,
                                               (xmin, ymin),
                                               (xmax, ymax),
                                               (36, 255, 12),
                                               4)
                    cv2.putText(temp_image,
                                classes[str(coord['class'])],
                                (xmin, ymin - 10),
                                cv2.FONT_HERSHEY_PLAIN,
                                4,
                                (36, 255, 12),
                                2)
                    if coord['class'] in [1, 2, 3, 4, 5]:
                        face = face.crop((xmin, ymin, xmax, ymax,))
                        face_path = os.path.join(tmp_dir, "face.jpg")
                        face.save(face_path)
                        face_arr = cv2.imread(face_path)
                        face_emb = calculate_embeddings([np.asarray(face_arr)], batch_size=1)
                        face_str_embedding = [str(a) for a in list(face_emb[0])]
                        face_embedding = ','.join(face_str_embedding)
                    elif coord['class'] in [27, 28, 29, 30, 31]:
                        whisker = whisker.crop((xmin, ymin, xmax, ymax,))
                        whisker_path = os.path.join(tmp_dir, "whisker.jpg")
                        whisker.save(whisker_path)
                        whisker_arr = cv2.imread(whisker_path)
                        whisker_emb = calculate_embeddings([np.asarray(whisker_arr)], batch_size=1)
                        whisker_str_embedding = [str(a) for a in list(whisker_emb[0])]
                        whisker_embedding = ','.join(whisker_str_embedding)
                    elif coord['class'] in [6, 8, 10, 12]:
                        lear = lear.crop((xmin, ymin, xmax, ymax,))
                        lear_path = os.path.join(tmp_dir, "lear.jpg")
                        lear.save(lear_path)
                    elif coord['class'] in [7, 9, 11, 13]:
                        rear = rear.crop((xmin, ymin, xmax, ymax,))
                        rear_path = os.path.join(tmp_dir, "rear.jpg")
                        rear.save(rear_path)
                    elif coord['class'] in [14, 16, 18, 20]:
                        leye = leye.crop((xmin, ymin, xmax, ymax,))
                        leye_path = os.path.join(tmp_dir, "leye.jpg")
                        leye.save(leye_path)
                    elif coord['class'] in [15, 17, 19, 21]:
                        reye = reye.crop((xmin, ymin, xmax, ymax,))
                        reye_path = os.path.join(tmp_dir, "reye.jpg")
                        reye.save(reye_path)
                    elif coord['class'] in [22, 23, 24, 25, 26]:
                        nose = nose.crop((xmin, ymin, xmax, ymax,))
                        nose_path = os.path.join(tmp_dir, "nose.jpg")
                        nose.save(nose_path)
        lion_path = os.path.join(tmp_dir, "lion.jpg")
        cv2.imwrite(lion_path, temp_image)
    return lion_path, face_path, \
           whisker_path, lear_path, \
           rear_path, leye_path, \
           reye_path, nose_path, \
           face_embedding, whisker_embedding


def check_upload(lion_image_path):
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp()
        pil_img = Image.open(lion_image_path)
        src = cv2.imread(lion_image_path)
        temp_image = src.copy()
        coordinates, whisker_cords, face_cords, status = lion_model.get_coordinates(lion_image_path, 'temp_lion')
        if status != "Success":
            print(status)
            return status
        lion_path, face_path, whisker_path, lear_path, rear_path, leye_path, reye_path, nose_path, face_embedding, whisker_embedding = \
            extract_lion_data(face_cords, 'temp_lion', pil_img, coordinates, tmp_dir, temp_image)
        ret = match_lion(face_embedding, whisker_embedding)
        return ret
    except Exception as e:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return str(e)


def dd2dms(dd):
    mnt, sec = divmod(dd * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return deg, mnt, sec


def get_click_datetime(data):
    mm, dd, yyyy = data['Date'].split('/')
    time = data['UTC-Time'].split('.')[0]
    hours, mins, secs = time.split(':')
    if len(hours) < 2:
        hours = '0' + hours
    if len(mins) < 2:
        mins = '0' + mins
    if len(secs) < 2:
        secs = '0' + secs
    new_time = hours + ':' + mins + ':' + secs
    iso_dt = yyyy + '-' + mm + '-' + dd + ' ' + new_time
    dt = datetime.fromisoformat(iso_dt)
    return dt


def upload_one_lion(lion_image_path, lion_name):
    tmp_dir = tempfile.mkdtemp()
    try:
        lat = f"{0.0}° {0.0}' {0.0}\""
        lon = f"{0.0}° {0.0}' {0.0}\""
        utc_click_datetime = datetime.now(timezone.utc)
        lion_id = str(current_milli_time())
        data = gpsphoto.getGPSData(lion_image_path)
        if len(data) > 0:
            try:
                lat_deg, lat_mnt, lat_sec = dd2dms(data['Latitude'])
                lat = f"{lat_deg}° {lat_mnt}' {lat_sec}\""
            except Exception as e:
                lat = f"{0.0}° {0.0}' {0.0}\""
            try:
                lon_deg, lon_mnt, lon_sec = dd2dms(data['Longitude'])
                lon = f"{lon_deg}° {lon_mnt}' {lon_sec}\""
            except Exception as e:
                lon = f"{0.0}° {0.0}' {0.0}\""
            try:
                utc_click_datetime = get_click_datetime(data)
            except Exception as e:
                utc_click_datetime = datetime.now(timezone.utc)
        pil_img = Image.open(lion_image_path)
        src = cv2.imread(lion_image_path)
        temp_image = src.copy()
        coordinates, whisker_cords, face_cords, status = lion_model.get_coordinates(lion_image_path, lion_name)
        if status != "Success":
            print(status)
            r = dict()
            r['lion_name'] = lion_name
            r['lion_image_file_name'] = os.path.basename(lion_image_path)
            r['status'] = status
            return r
        lion_path, face_path, whisker_path, lear_path, rear_path, leye_path, reye_path, nose_path, face_embedding, whisker_embedding = \
            extract_lion_data(face_cords, lion_name, pil_img, coordinates, tmp_dir, temp_image)
        insert_lion_data(lion_id, lion_name,
                         'U', 'A',
                         utc_click_datetime,
                         lat, lon, lion_path,
                         face_path, whisker_path,
                         lear_path, rear_path,
                         leye_path, reye_path,
                         nose_path, face_embedding,
                         whisker_embedding)
        face_bytes = get_base64_str(face_path)
        shutil.rmtree(tmp_dir)
        r = dict()
        r['lion_name'] = lion_name
        r['lion_image_file_name'] = os.path.basename(lion_image_path)
        r['image'] = face_bytes
        r['status'] = 'Success'
        return r
    except Exception as e:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        r = dict()
        r['lion_name'] = lion_name
        r['lion_image_file_name'] = os.path.basename(lion_image_path)
        r['status'] = str(e)
        return r


def on_board_new_lion(lion, lion_dir, rv):
    tmp_dir = None
    lion_images = os.listdir(lion_dir)
    for lion_image in lion_images:
        try:
            lat = f"{0.0}° {0.0}' {0.0}\""
            lon = f"{0.0}° {0.0}' {0.0}\""
            utc_click_datetime = datetime.now(timezone.utc)
            lion_id = str(current_milli_time())
            tmp_dir = tempfile.mkdtemp()
            lion_image_path = os.path.join(lion_dir, lion_image)
            data = gpsphoto.getGPSData(lion_image_path)
            if len(data) > 0:
                try:
                    lat_deg, lat_mnt, lat_sec = dd2dms(data['Latitude'])
                    lat = f"{lat_deg}° {lat_mnt}' {lat_sec}\""
                except Exception as e:
                    lat = f"{0.0}° {0.0}' {0.0}\""
                try:
                    lon_deg, lon_mnt, lon_sec = dd2dms(data['Longitude'])
                    lon = f"{lon_deg}° {lon_mnt}' {lon_sec}\""
                except Exception as e:
                    lon = f"{0.0}° {0.0}' {0.0}\""
                try:
                    utc_click_datetime = get_click_datetime(data)
                except Exception as e:
                    utc_click_datetime = datetime.now(timezone.utc)
            pil_img = Image.open(lion_image_path)
            src = cv2.imread(lion_image_path)
            temp_image = src.copy()
            coordinates, whisker_cords, face_cords, status = lion_model.get_coordinates(lion_image_path, lion)
            if status != "Success":
                print(status)
                r = dict()
                r['lion_name'] = lion
                r['lion_image_file_name'] = lion_image
                r['status'] = status
                rv['status'].append(r)
                continue
            lion_path, face_path, whisker_path, lear_path, rear_path, leye_path, reye_path, nose_path, face_embedding, whisker_embedding = \
                extract_lion_data(face_cords, lion, pil_img, coordinates, tmp_dir, temp_image)
            insert_lion_data(lion_id, lion,
                             'U', 'A',
                             utc_click_datetime,
                             lat, lon, lion_path,
                             face_path, whisker_path,
                             lear_path, rear_path,
                             leye_path, reye_path,
                             nose_path, face_embedding,
                             whisker_embedding)
            shutil.rmtree(tmp_dir)
            r = dict()
            r['lion_name'] = lion
            r['lion_image_file_name'] = lion_image
            r['status'] = 'Success'
            rv['status'].append(r)
        except Exception as e:
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            r = dict()
            r['lion_name'] = lion
            r['lion_image_file_name'] = lion_image
            r['status'] = str(e)
            rv['status'].append(r)
