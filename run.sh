#!/usr/bin/env bash

source venv/bin/activate
if test -f .env; then
    source .env
fi
python run.py
