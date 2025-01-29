#!/bin/bash
find ./static/assets/images -type d -exec svgo --multipass -f {} --config=./svgo.config.js 2>&1 \; | \
  grep -B2 "%" | \
  grep -v "Done in" | \
  grep -v "^--$" | \
  grep -v " 0% " | \
  paste - - | \
  awk '{if ($0 ~ /%/ && $0 !~ /0%/) print $1 $4 " " $5 " " $6 " " $7 "Kb ✔️"}'
