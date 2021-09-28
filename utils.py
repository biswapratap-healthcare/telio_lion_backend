import os
import shutil
import tempfile
import time

import cv2
from PIL import Image

from db_driver import insert_lion_data
from lion_model import LionDetection, classes


lion_model = LionDetection()


def current_milli_time():
    return round(time.time() * 1000)


def on_board_new_lion(lion_name, d, lion_images):
    for lion_image in lion_images:
        face_path = ''
        whisker_path = ''
        lear_path = ''
        rear_path = ''
        leye_path = ''
        reye_path = ''
        nose_path = ''
        lion_id = str(current_milli_time())
        tmp_dir = tempfile.mkdtemp()
        lion_image = os.path.join(d, lion_image)
        pil_img = Image.open(lion_image)
        src = cv2.imread(lion_image)
        temp_image = src.copy()
        coordinates, whisker_cords, face_cords, status = lion_model.get_coordinates(lion_image, lion_name)
        if status != "Success":
            print(status)
            continue
        for face_coord in face_cords[lion_name]['boxes']:
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
                        elif coord['class'] in [27, 28, 29, 30, 31]:
                            whisker = whisker.crop((xmin, ymin, xmax, ymax, ))
                            whisker_path = os.path.join(tmp_dir, "whisker.jpg")
                            whisker.save(whisker_path)
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
            insert_lion_data(lion_id, lion_name,
                             '0.0.0', lion_path,
                             face_path, whisker_path,
                             lear_path, rear_path,
                             leye_path, reye_path,
                             nose_path)
            shutil.rmtree(tmp_dir)
