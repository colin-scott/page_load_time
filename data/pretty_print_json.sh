#!/bin/bash

python -m json.tool $1 > /tmp/t && mv /tmp/t $1
