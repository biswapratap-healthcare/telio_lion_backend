import os
import cv2
from PIL import Image
from lion_model import LionDetection, classes


lion_model = LionDetection()


def on_board_new_lion(lion_id, lion_name, d, lion_images):
    image_details = dict()
    for lion_image in lion_images:
        coordinates_group = dict()
        lion_image = os.path.join(d, lion_image)
        pil_img = Image.open(lion_image)
        src = cv2.imread(lion_image)
        temp_image = cv2.cvtColor(src, cv2.COLOR_RGB2BGR)
        coordinates, whisker_cords, face_cords = lion_model.get_coordinates(lion_image, lion_name)
        predictions = list()
        for face_coord in face_cords[lion_name]['boxes']:
            if face_coord["conf"] > 0.7:
                face_image = cv2.cvtColor(src, cv2.COLOR_RGB2BGR)
                coordi = []
                face = pil_img.copy()
                leye = pil_img.copy()
                reye = pil_img.copy()
                lear = pil_img.copy()
                rear = pil_img.copy()
                nose = pil_img.copy()
                whisker = pil_img.copy()
                parts_crop = dict()
                mul_cls = list()
                prediction = None
                feature = None
                for coord in coordinates['boxes']:
                    if lion_model.insideface(face_coord, coord):
                        coordi.append(coord)
                        roi_box = coord['ROI']
                        xmin = int(roi_box[0])
                        ymin = int(roi_box[1])
                        xmax = int(roi_box[2])
                        ymax = int(roi_box[3])
                        mul_cls.append(classes[str(coord['class'])])
                        temp_image = cv2.rectangle(temp_image, (xmin, ymin), (xmax, ymax), (36,255,12), 6)
                        face_image = cv2.rectangle(face_image, (xmin, ymin), (xmax, ymax), (36,255,12), 6)
                        cv2.putText(temp_image, classes[str(coord['class'])], (xmin, ymin-10), cv2.FONT_HERSHEY_PLAIN, 4, (36,255,12), 8)
                        cv2.putText(face_image, classes[str(coord['class'])], (xmin, ymin-10), cv2.FONT_HERSHEY_PLAIN, 4, (36,255,12), 8)
                        if coord['class'] in [1, 2, 3, 4, 5]:
                            face = face.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['face'] = face
                        elif coord['class'] in [27, 28, 29, 30, 31]:
                            whisker = whisker.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['whisker'] = whisker
                        elif coord['class'] in [6, 8, 10, 12]:
                            lear = lear.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['lear'] = lear
                        elif coord['class'] in [7, 9, 11, 13]:
                            rear = rear.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['rear'] = rear
                        elif coord['class'] in [14, 16, 18, 20]:
                            leye = leye.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['leye'] = leye
                        elif coord['class'] in [15, 17, 19, 21]:
                            reye = reye.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['reye'] = reye
                        elif coord['class'] in [22, 23, 24, 25, 26]:
                            nose = nose.crop((xmin, ymin, xmax, ymax, ))
                            parts_crop['nose'] = nose
                name = "lion"
                predictions.append("lion")
                key_n = f"{'lion'}__{predictions.count('lion')}"
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
                face_image = Image.fromarray(face_image)
                coordinates_group[key_n] = {'coordinates': coordi, 'prediction': {"lion_id": key_n, "probability": 0.0}, 'classes': mul_cls,
                'image_box': face_image, "feature": [],
                "parts_crop": parts_crop}
        temp_image = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
        final_img = Image.fromarray(temp_image)
        image_details[lion_image] = {'image': final_img, "coordinates": coordinates, "whisker_cords": whisker_cords, "face_cords": face_cords,
                            'coordinates_group': coordinates_group}
    return image_details

