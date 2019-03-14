#!/bin/bash

STACK_BASE="/Users/harmtemolder/stack/GitHub"
DIR_NAME="assistant-sdk-python"

cd "$STACK_BASE/$DIR_NAME"
source activate assistant-sdk-python
googlesamples-assistant-pushtotalk --device-model-id 'macbook-pro' --device-id 'run-in-terminal'
