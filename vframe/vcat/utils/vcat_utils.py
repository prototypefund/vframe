import sys
import os
from os.path import join
import json
import requests
import random
import collections
from operator import itemgetter
from collections import OrderedDict

import numpy as np

from vframe.utils import file_utils, logger_utils

log = logger_utils.Logger.getLogger()

def format_im_fn(meta):
  """Formats image filename from VCAT image meta"""
  sha256 = meta['sa_hash']  # sha256
  sha256_tree = file_utils.sha256_tree(sha256)
  if meta['uploaded'] or meta['fn'] != 'index':
    if meta['sa_hash'] is not None:
      fn = '{}_{}{}'.format(meta['sa_hash'], meta['fn'], meta['ext'])
    else:
      fn = '{}{}'.format(meta['fn'], meta['ext'])
  else:
    fn = '{}_{}{}'.format(meta['sa_hash'], meta['frame'], meta['ext'])
  return join(fn)

def format_im_url(url_base, meta, size='lg'):
  """Formats image S3 URLfrom VCAT image meta"""
  sha256 = meta['sa_hash']  # sha256
  sha256_tree = file_utils.sha256_tree(sha256)
  if meta['uploaded'] or meta['fn'] != 'index':
    fn = join(str(meta['id']), meta['fn'], '{}{}'.format(size, meta['ext']))
    url_path = join('media/images', fn)
  else:
    fn = '{}{}'.format(meta['fn'], meta['ext'])
    if meta['verified']:
      url_path = join('v1/media/keyframes', sha256_tree, sha256, meta['frame'], 'lg', fn)
    else:
      url_path = join('v1/media/keyframes/unverified', sha256_tree, sha256, meta['frame'], 'lg', fn)
  return join(url_base, url_path)


def load_annotations(fp_in, exclude_idxs=[]):

  vcat_data = file_utils.load_json(fp_in)

  # filter out exlcluded classes
  if exclude_idxs:
    vcat_data = exclude_classes(vcat_data, exclude_idxs)

  # convert keys to int and sort ordered
  hierarchy = vcat_data['hierarchy']
  hierarchy_copy = hierarchy.copy()
  hierarchy = {int(k): v for k, v in hierarchy_copy.items()}
  hierarchy = OrderedDict(sorted(hierarchy.items(), key=lambda t: t[0]))

  object_classes = vcat_data['object_classes']
  object_classes_copy = object_classes.copy()
  object_classes = {int(k): v for k, v in object_classes_copy.items()}
  object_classes = OrderedDict(sorted(object_classes.items(), key=lambda t: t[0]))

  return {'hierarchy': hierarchy, 'object_classes': object_classes}


# ----------------------------------------------------------
# Format hierarchy for display
# ----------------------------------------------------------

def hierarchy_tree(hierarchy):
  """Convert VCAT flat hierarchy to a tree sturcture"""
  global log
  
  # recursive add subclasses
  def add_subclasses(tree, hierarchy, index=0):
    global log
    # for each class ID at this level
    for tree_id, tree_meta in tree.items():
      # add hierarchy items if parent matches class
      tree_id = tree_id
      hierarchy_copy = hierarchy.copy()
      # log.debug('tree id: {}'.format(tree_id))
      for class_id, class_meta in hierarchy_copy.items():
        # add child to parent class
        parent_id = class_meta['parent']
        if parent_id == tree_id:
          # it's a child, consume hierarchy elements, appending to tree
          hierarchy.pop(class_id)
          # add attribute if exists and has regions
          
          class_meta['label_index'] = index  # set local class label index
          class_meta['attributes'] = {}  # ?
          class_meta['subclasses'] = {}  # ?

          num_regions = int(class_meta['region_count'])
          if class_meta['is_attribute'] and num_regions > 0:
            index += 1
            tree_meta['attributes'][class_id] = class_meta
            log.info('add attributes: {} {} ({} annos)'.format(index, class_meta['slug'], num_regions))
          elif num_regions > 0:
            index += 1
            tree_meta['subclasses'][class_id] = class_meta
            log.info('add subclass: {} ({} annos)'.format(class_meta['slug'], num_regions))
          if not class_meta['is_attribute']:
            tree[tree_id]['subclasses'][class_id] = class_meta

      # find all subclasses and attributes of this tree
      index, tree[tree_id]['subclasses'] = add_subclasses(tree_meta['subclasses'], hierarchy, index=index)
    return index, tree

  tree = collections.OrderedDict({})

  hierarchy_copy = collections.OrderedDict(hierarchy.copy())
  
  for class_id, class_meta in hierarchy_copy.items():
    class_id = class_id
    parent_id = class_meta['parent']

    # root level
    if parent_id is None:
      # top level
      tree[class_id] = class_meta
      tree[class_id]['subclasses'] = {}
      tree[class_id]['attributes'] = {}
      tree[class_id]['label_index'] = len(tree) - 1
      hierarchy.pop(class_id)
  

  tree_copy = tree.copy()
  index = 0
  for i, t in enumerate(tree_copy):
    tmp = collections.OrderedDict({t: tree[t]})
    index, tmp = add_subclasses(tmp, hierarchy, index=index)
    tree.update(tmp)

  return tree



def hierarchy_tree_display(tree, output=[], indent=0):
  """Returns class hierarchy in space formatted style"""
  for k,v in tree.items():
    output.append('{}+ {} (VCAT ID: {}, Training ID: {}, regions: {})'.format(indent*' ', v['slug'], v['id'], v['label_index'], v['region_count']))
    subclasses = v.get('subclasses',None)
    hierarchy_tree_display(subclasses, output=output, indent=indent +2)
    attributes = v.get('attributes',None)
    for attr_id, attr_meta in attributes.items():
     # output.append('{} - [{}] {}'.format(indent*'  ',attr_meta['label_index'],attr_meta['slug']))
     output.append('{}- {} (VCAT ID: {}, Training ID: {}, count: {})'.format(\
      indent*' '+'  ', attr_meta['slug'], attr_meta['id'], attr_meta['label_index'], attr_meta['region_count']))
  return '\n'.join(output)


def hierarchy_flat(tree):
  
  def walk_tree(tree, flat={}):
    for class_id, class_meta in tree.items():
      subclasses = class_meta.get('subclasses', None)
      if class_meta['region_count'] > 0:
        log.info('add: {}'.format(class_meta['slug']))
        flat[class_meta['label_index']] = class_meta
      flat = walk_tree(class_meta['subclasses'], flat.copy())
      for attr_id, attr_meta in class_meta['attributes'].items():
        log.info('add: {} attr_id: {}, slug: {}'.format(attr_meta['label_index'], attr_id, attr_meta['slug']))
        flat[attr_meta['label_index']] = attr_meta
    return flat

  flat = walk_tree(tree)
  return flat


def append_parents(annos_flat, hierarchy):
  # labels for existing class lookup
  anno_flat_labels = [v['slug'] for k, v in annos_flat.items()]

  # expand annos_flat with parent class at end
  for k, v in annos_flat.copy().items():
    if bool(v['is_attribute']):
      parent_id = int(v['parent'])
      parent_obj = hierarchy[parent_id]
      contains = False
      parent_label = parent_obj['slug']
      if parent_obj['slug'] not in anno_flat_labels:
        annos_flat[len(annos_flat)] = parent_obj
        anno_flat_labels.append(parent_obj['slug'])

  return annos_flat


def exclude_classes(vcat_data, exclude_idxs):
  """
  Remove classes from VCAT hierarchy and object_classes
  :param vcat_cata: full VCAT data in JSON format
  :param exclusions: integer-list of exlcluded classes
  :returns: revised VCAT data in JSON format
  """
  # NB: convert exclude_idxs to string because JSON key values are string

  log.info('excluding: {}'.format(exclude_idxs))

  # remove from hierarchy
  hierarchy = vcat_data['hierarchy']
  hierarchy_tmp = hierarchy.copy()

  for class_id, class_meta in hierarchy_tmp.items():
    if int(class_id) in exclude_idxs:
      log.info('removing hierarchy ID: {} ({})'.format(class_id, class_meta['slug']))
      del hierarchy[class_id]

  # remove from annotations
  object_classes = vcat_data['object_classes']
  object_classes_tmp = object_classes.copy()
  
  for class_id, class_meta in object_classes_tmp.items():
    if int(class_id) in exclude_idxs:
      log.info('removing annotation ID: {} ({})'.format(class_id, class_meta['slug']))
      del hierarchy[class_id]

  return {'hierarchy': hierarchy, 'object_classes': object_classes}