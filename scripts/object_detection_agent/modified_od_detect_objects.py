'''
Copyright (C) 2018 Saif Alabachi

Based on TensorFlow object detection API

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

# Object detection imports
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

if tf.__version__ < '1.4.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')


'''Path to object detection folder'''
sys.path.append("/home/saif/catkin_ws/src/ucf_ardrone_ros/scripts/object_detection_agent/tensorflow/models/research")
sys.path.append("/home/saif/catkin_ws/src/ucf_ardrone_ros/scripts/object_detection_agent/tensorflow/models/research")






# Variables
# What model to download.
MODEL_NAME = 'faster_rcnn_inception_resnet_v2_atrous_oid_2018_01_28'







OBJECT_DETECTION_PATH = 'object_detection'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = os.path.join(OBJECT_DETECTION_PATH, 'model_zoo', MODEL_NAME + '/frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(OBJECT_DETECTION_PATH, 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90


# Load a (frozen) Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)



def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)




# Detection
# For the sake of simplicity we will use only 2 images:
# image1.jpg
# image2.jpg
# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
PATH_TO_TEST_IMAGES_DIR = os.path.join(OBJECT_DETECTION_PATH, 'test_images')
TEST_IMAGE_PATHS = [os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 3)]

# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)




# class DetectImage(object):
#     detection_graph = 'graph'
#     sess = 'sess'
#     image_tensor = 'Tensor'
#     # Each box represents a part of the image where a particular object was detected.
#     detection_boxes = 'Tensor'
#     # Each score represent how level of confidence for each of the objects.
#     # Score is shown on the result image, together with the class label.
#     detection_scores = 'Tensor'
#     detection_classes = 'Tensor'
#     num_detections = 'Tensor'
#
#     def __init__(self):
#         # Definite and open graph and sess
#         self.detection_graph = detection_graph
#         self.sess = tf.Session(graph=detection_graph)
#         # Definite input and output Tensors for detection_graph
#         self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
#         # Each box represents a part of the image where a particular object was detected.
#         self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
#         # Each score represent how level of confidence for each of the objects.
#         # Score is shown on the result image, together with the class label.
#         self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
#         self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
#         self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')
#
#     def __del__(self):
#         self.sess.close()
#
#     def run_detect(self, image_np):
#         # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
#         image_np_expanded = np.expand_dims(image_np, axis=0)
#
#         # Actual detection.
#         (boxes, scores, classes, num) = self.sess.run(
#             [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
#             feed_dict={self.image_tensor: image_np_expanded})
#         # Visualization of the results of a detection.
#         vis_util.visualize_boxes_and_labels_on_image_array(
#             image_np,
#             np.squeeze(boxes),
#             np.squeeze(classes).astype(np.int32),
#             np.squeeze(scores),
#             category_index,
#             use_normalized_coordinates=True,
#             line_thickness=8)
#         return image_np



def run_inference_for_single_image(image, graph):
  with graph.as_default():
    with tf.Session() as sess:
      # Get handles to input and output tensors
      ops = tf.get_default_graph().get_operations()
      all_tensor_names = {output.name for op in ops for output in op.outputs}
      tensor_dict = {}
      for key in [
          'num_detections', 'detection_boxes', 'detection_scores',
          'detection_classes', 'detection_masks'
      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
              tensor_name)
      if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

      # Run inference
      output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: np.expand_dims(image, 0)})

      # all outputs are float32 numpy arrays, so convert types as appropriate
      output_dict['num_detections'] = int(output_dict['num_detections'][0])
      output_dict['detection_classes'] = output_dict[
          'detection_classes'][0].astype(np.uint8)
      output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
      output_dict['detection_scores'] = output_dict['detection_scores'][0]
      if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
  return output_dict





if __name__ == '__main__':
    # di = DetectImage()
    #
    # PATH_TO_TEST_IMAGES_DIR = os.path.join(OBJECT_DETECTION_PATH, 'test_images')
    # TEST_IMAGE_PATHS = [os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 3)]
    # for image_path in TEST_IMAGE_PATHS:
    #     # image = Image.open(image_path)
    #     # the array based representation of the image will be used later in order to prepare the
    #     # result image with boxes and labels on it.
    #     # image_np = load_image_into_numpy_array(image)
    #     image_np = skimage.io.imread(image_path)
    #     image_np = di.run_detect(image_np)
    #
    #     plt.figure(figsize=IMAGE_SIZE)
    #     plt.imshow(image_np)
    #     plt.show()



    for image_path in TEST_IMAGE_PATHS:
      image = Image.open(image_path)
      # the array based representation of the image will be used later in order to prepare the
      # result image with boxes and labels on it.
      image_np = load_image_into_numpy_array(image)
      # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
      image_np_expanded = np.expand_dims(image_np, axis=0)
      # Actual detection.
      output_dict = run_inference_for_single_image(image_np, detection_graph)
      # Visualization of the results of a detection.
      vis_util.visualize_boxes_and_labels_on_image_array(
          image_np,
          output_dict['detection_boxes'],
          output_dict['detection_classes'],
          output_dict['detection_scores'],
          category_index,
          instance_masks=output_dict.get('detection_masks'),
          use_normalized_coordinates=True,
          line_thickness=8)
      plt.figure(figsize=IMAGE_SIZE)
      plt.imshow(image_np)
      plt.show()