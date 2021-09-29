import os
import shutil
import tempfile
import time

import cv2
import numpy as np
from PIL import Image

from skimage.transform import resize
from keras.models import load_model

from db_driver import insert_lion_data
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


def on_board_new_lion(lion, lion_dir, rv):
    lion_images = os.listdir(lion_dir)
    for lion_image in lion_images:
        try:
            face_path = ''
            whisker_path = ''
            lear_path = ''
            rear_path = ''
            leye_path = ''
            reye_path = ''
            nose_path = ''
            face_embedding = ''
            whisker_embedding = ''
            lion_id = str(current_milli_time())
            tmp_dir = tempfile.mkdtemp()
            lion_image_path = os.path.join(lion_dir, lion_image)
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
                                        (xmin, ymin-10),
                                        cv2.FONT_HERSHEY_PLAIN,
                                        4,
                                        (36, 255, 12),
                                        2)
                            if coord['class'] in [1, 2, 3, 4, 5]:
                                face = face.crop((xmin, ymin, xmax, ymax, ))
                                face_path = os.path.join(tmp_dir, "face.jpg")
                                face.save(face_path)
                                face_arr = cv2.imread(face_path)
                                face_emb = calculate_embeddings([np.asarray(face_arr)], batch_size=1)
                                face_str_embedding = [str(a) for a in list(face_emb[0])]
                                face_embedding = ','.join(face_str_embedding)
                                print('c')
                            elif coord['class'] in [27, 28, 29, 30, 31]:
                                whisker = whisker.crop((xmin, ymin, xmax, ymax, ))
                                whisker_path = os.path.join(tmp_dir, "whisker.jpg")
                                whisker.save(whisker_path)
                                whisker_arr = cv2.imread(whisker_path)
                                whisker_emb = calculate_embeddings([np.asarray(whisker_arr)], batch_size=1)
                                whisker_str_embedding = [str(a) for a in list(whisker_emb[0])]
                                whisker_embedding = ','.join(whisker_str_embedding)
                                print('c')
                            elif coord['class'] in [6, 8, 10, 12]:
                                lear = lear.crop((xmin, ymin, xmax, ymax, ))
                                lear_path = os.path.join(tmp_dir, "lear.jpg")
                                lear.save(lear_path)
                            elif coord['class'] in [7, 9, 11, 13]:
                                rear = rear.crop((xmin, ymin, xmax, ymax, ))
                                rear_path = os.path.join(tmp_dir, "rear.jpg")
                                rear.save(rear_path)
                            elif coord['class'] in [14, 16, 18, 20]:
                                leye = leye.crop((xmin, ymin, xmax, ymax, ))
                                leye_path = os.path.join(tmp_dir, "leye.jpg")
                                leye.save(leye_path)
                            elif coord['class'] in [15, 17, 19, 21]:
                                reye = reye.crop((xmin, ymin, xmax, ymax, ))
                                reye_path = os.path.join(tmp_dir, "reye.jpg")
                                reye.save(reye_path)
                            elif coord['class'] in [22, 23, 24, 25, 26]:
                                nose = nose.crop((xmin, ymin, xmax, ymax, ))
                                nose_path = os.path.join(tmp_dir, "nose.jpg")
                                nose.save(nose_path)
                lion_path = os.path.join(tmp_dir, "lion.jpg")
                cv2.imwrite(lion_path, temp_image)
                insert_lion_data(lion_id, lion,
                                 '', lion_path,
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
            r = dict()
            r['lion_name'] = lion
            r['lion_image_file_name'] = lion_image
            r['status'] = str(e)
            rv['status'].append(r)
