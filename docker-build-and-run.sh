#!/bin/bash

docker build -t teamplan  .

docker run -p5000:5000 -it  --mount type=bind,source="$(pwd)",target=/teamplan teamplan flask run --host=0.0.0.0 --reload
