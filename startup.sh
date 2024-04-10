#!/bin/sh
# startup.sh

cd ~/potentiostat-io || exit
git pull
source env/bin/activate
pip install -r requirements.txt
python app/main.py
