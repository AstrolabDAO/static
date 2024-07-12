#!/bin/bash
find ./static/assets/images -type d -exec svgo -f {} --config=./svgo.config.js \;
