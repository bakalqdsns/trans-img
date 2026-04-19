# -*- coding: utf-8 -*-
"""
ComicTextDetector inpainting module.
"""

import numpy as np
import cv2
import torch
from PIL import Image

from collections import OrderedDict
from functools import partial
from typing import Optional, List

import os
import sys
import argparse
from tqdm import tqdm
import time
import re

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

# ComicTextDetector is defined in comictextdetector.py
from .comictextdetector import ComicTextDetector

# INPAINTERS registry - defined in this file
class _InpainterRegistry:
    """Registry for inpainting implementations."""
    def __init__(self):
        self._registry = {}
    
    def register(self, key, cls):
        self._registry[key] = cls
    
    def get(self, key):
        return self._registry.get(key)
    
    def __iter__(self):
        return iter(self._registry)
    
    def keys(self):
        return self._registry.keys()

INPAINTERS = _InpainterRegistry()

__all__ = ['ComicTextDetector', 'INPAINTERS']
