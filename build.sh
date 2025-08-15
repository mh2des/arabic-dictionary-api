#!/bin/bash
echo "Installing git-lfs and pulling LFS files..."
apt-get update && apt-get install -y git-lfs
git lfs install
git lfs pull
echo "LFS files pulled successfully"
ls -la app/arabic_dict.db
