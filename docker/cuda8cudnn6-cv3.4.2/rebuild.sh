#!/bin/bash
nvidia-docker build --rm -t adamhrv/cuda8-cudnn6-opencv:3.4.1 $(readlink -f $(dirname $0))