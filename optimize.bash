#!/bin/bash
find ./static/assets/images -type d -exec svgo --multipass -f {} --config=./svgo.config.js \;
