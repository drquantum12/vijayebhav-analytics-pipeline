#!/bin/bash

gcloud run jobs create analytics-pipeline \
  --image asia-south1-docker.pkg.dev/nyaaysakha/ollama-repo/analytics-pipeline \
  --region asia-south1 \
  --memory=2Gi \
  --cpu=1 \
  --execute-now