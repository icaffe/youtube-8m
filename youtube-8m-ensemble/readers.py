# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provides readers configured for different datasets."""

import tensorflow as tf
import utils

from tensorflow import logging

class BaseReader(object):
  """Inherit from this class when implementing new readers."""

  def prepare_reader(self, unused_filename_queue):
    """Create a thread for generating prediction and label tensors."""
    raise NotImplementedError()


class EnsembleReader(BaseReader):

  def __init__(self,
               num_classes=4716,
               feature_sizes=[1024],
               feature_names=["mean_inc3"]):

    assert len(feature_names) == len(feature_sizes), \
        "length of feature_names (={}) != length of feature_sizes (={})".format( \
        len(feature_names), len(feature_sizes))

    self.num_classes = num_classes
    self.feature_sizes = feature_sizes
    self.feature_names = feature_names

  def prepare_reader(self, filename_queue, batch_size=1024):

    reader = tf.TFRecordReader()
    _, serialized_examples = reader.read_up_to(filename_queue, batch_size)

    # set the mapping from the fields to data types in the proto
    num_features = len(self.feature_names)
    assert num_features > 0, "self.feature_names is empty!"
    assert len(self.feature_names) == len(self.feature_sizes), \
    "length of feature_names (={}) != length of feature_sizes (={})".format( \
    len(self.feature_names), len(self.feature_sizes))

    feature_map = {"video_id": tf.FixedLenFeature([], tf.string),
                   "labels": tf.VarLenFeature(tf.int64)}
    for feature_index in range(num_features):
      feature_map[self.feature_names[feature_index]] = tf.FixedLenFeature(
          [self.feature_sizes[feature_index]], tf.float32)

    features = tf.parse_example(serialized_examples, features=feature_map)
    labels = tf.sparse_to_indicator(features["labels"], self.num_classes)
    labels.set_shape([None, self.num_classes])
    concatenated_features = tf.concat([
        features[feature_name] for feature_name in self.feature_names], 1)

    return features["video_id"], concatenated_features, labels, tf.ones([tf.shape(serialized_examples)[0]])

