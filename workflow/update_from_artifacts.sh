#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

# update hashes in db from artifacts
for artifact in $DIR/../output/matches/*.txt
do
    slug=$(basename $artifact .jsonl)
    $DIR/update_count.py -d $DIR/website.db -s $slug
done

# update error_counts in db from artifacts
for artifact in $DIR/../output/error_counts/*.txt
do
    error_slug=$(basename $artifact .txt)
    $DIR/increase_error_count.py -d $DIR/website.db --slug="${error_slug}"
done
