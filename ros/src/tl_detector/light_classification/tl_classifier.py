from styx_msgs.msg import TrafficLight
import rospy


import os
import glob
import numpy as np
import cv2
import tensorflow as tf
from pathlib import Path


class TLClassifier(object):
    def __init__(self, threshold, modeltype = 'sim'):
        self.threshold = threshold

        inference_path = os.path.join(str(Path(__file__).parent.parent),
                                    "training/model_{}/inference/frozen_inference_graph.pb".format(modeltype))

        self.detection_graph = tf.Graph()

        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()

            with tf.gfile.GFile(inference_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            self.sess = tf.Session(graph=self.detection_graph, config=config)
            self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
              # Each box represents a part of the image where a particular object was detected.
            self.boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
              # Each score represent how level of confidence for each of the objects.
              # Score is shown on the result image, together with the class label.
            self.scores =self.detection_graph.get_tensor_by_name('detection_scores:0')
            self.classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
            self.num_detections =self.detection_graph.get_tensor_by_name('num_detections:0')

    def box_to_pixel(self, box, dim):

        height, width = dim[0], dim[1]
        box_pixel = [int(box[0] * height), int(box[1] * width), int(box[2] * height), int(box[3] * width)]
        return np.array(box_pixel)

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        dim = image.shape[0:2]

        with self.detection_graph.as_default():
            image_expanded = np.expand_dims(image, axis=0)

            (boxes, scores, classes, num_detections) = self.sess.run(
                [self.boxes, self.scores, self.classes, self.num_detections],
                feed_dict={self.image_tensor: image_expanded})

            boxes = np.squeeze(boxes)
            classes = np.squeeze(classes)
            scores = np.squeeze(scores)

            rospy.loginfo("[TL_Classifier] Score: {0}".format(max(scores)) )

            for box, score, class_label in zip(boxes, scores, classes):
                if score > self.threshold:
                    pixel = self.box_to_pixel(box, dim)

                    class_label = int(class_label)
                    if class_label == 1:
                        rospy.loginfo("[TL_Classifier] {RED}")
                        return TrafficLight.RED
                        return 1#TrafficLight.RED # TrafficLight.RED has to be used
                    elif class_label == 2:
                        rospy.loginfo("[TL_Classifier] {YELLOW}")
                        return TrafficLight.YELLOW
                        return 2#TrafficLight.YELLOW # TrafficLight.YELLOW has to be used
                    elif class_label == 3:
                        rospy.loginfo("[TL_Classifier] {GREEN}")
                        return TrafficLight.GREEN
                        return 3#TrafficLight.GREEN # TrafficLight.GREEN has to be used

        #TODO implement light color prediction
        return TrafficLight.UNKNOWN
        return 4#TrafficLight.UNKNOWN # TrafficLight.UNKNOWN has to be used


if __name__ == '__main__':
    tl_cls =TLClassifier(threshold=0.3)

    image_paths = os.path.join(str(Path(__file__).parent.parent),"training/Images/*.png")

    for image_path, label in zip(sorted(glob.glob(image_paths)), [3, 3, 3, 1, 1, 1, 2, 2, 2]):
        image =  cv2.imread(image_path)
        traffic_light = tl_cls.get_classification(image)

        if traffic_light != label:
            raise ValueError("Simple unit test failed by picture {0}".format(image_path))





