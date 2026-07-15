# Modified by The Authors on July 2026 to adapt for the replication package.

#!/bin/bash

bugfix_commits_file=$1
conf_file=$2
repos_dir=$3

# use the basename of the passed bugfix commits file inside the container
bugfix_commits_basename=$(basename "$bugfix_commits_file")

echo +++ PARAMS +++
echo bugfix_commits_file=$bugfix_commits_file
echo conf_file=$conf_file
echo repos_dir=$repos_dir

docker build -t pyszz .
mkdir -p out

# replace with `docker run -d` to run the container in detached mode
docker run \
        -v $PWD/out:/usr/src/app/out \
        -v $(pwd)/$bugfix_commits_file:/usr/src/app/$bugfix_commits_basename \
        -v $(pwd)/$conf_file:/usr/src/app/conf.yml \
        -v $(pwd)/$repos_dir:/usr/src/app/cloned \
        pyszz $bugfix_commits_basename conf.yml cloned/
