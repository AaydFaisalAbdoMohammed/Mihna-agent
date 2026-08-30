#!/bin/bash
echo "Checking Python code for undefined names and import errors..."
python3 -m flake8 . --select=F401,F821
