#!/bin/bash

ip a show dev ib0 | grep "inet "

poetry run python3 master/run.py
