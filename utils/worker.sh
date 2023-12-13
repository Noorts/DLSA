#!/bin/bash

ip a show dev ib0 | grep "inet "

go run cmd/worker/main.go "$1:8000"
