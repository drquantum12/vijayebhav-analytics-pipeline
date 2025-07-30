#!/bin/bash

sudo docker buildx build --platform linux/amd64 -t gcr.io/nyaaysakha/analytics-pipeline .

sudo docker tag gcr.io/nyaaysakha/analytics-pipeline asia-south1-docker.pkg.dev/nyaaysakha/ollama-repo/analytics-pipeline

sudo docker push asia-south1-docker.pkg.dev/nyaaysakha/ollama-repo/analytics-pipeline
