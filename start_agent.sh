#!/bin/bash

cd ~/PizzaAgent
source venv/bin/activate

# Suppress ALSA errors completely
exec 2> >(grep -v "ALSA lib" >&2)

python3 main1.py
