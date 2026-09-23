#!/bin/bash

echo -e "Checking JSON structures\n"

usage() {
    echo -e "Usage: ./$0 [options]\n\n"

    echo -e "Options:\n"

    echo -e "-d Directory\t\tDestination to check"
    echo -e "-b Batch Size\tAmount of JSON files to search at a time"
    echo -e "-h HELP\tShows this menu"
}

while getopts ":d:b:h" option; do
    if [ "$option" = "d" ]; then
        directory="$OPTARG"
    elif [ "$option" = "b" ]; then
        batchSize="$OPTARG"
    elif [ "$option" = "h" ]; then
        usage
        exit 0
    else
        echo "Invalid option or missing argument"
        exit 1
    fi
done

if [ -z "$directory" ] || [ -z "$batchSize" ]; then
    echo "Need to fill out the directory and batch size..."
    exit 0
fi

echo "Invalid JSON files (will print file names): "

# uses all CPU to process (faster)
# prints file name if invalid
# btw, numzero is a placeholder so filename becomes $1

total=$(find "$directory" -name "*.json" | wc -l)
find "$directory" -name "*.json" -print0 | pv -0 -l -s "$total" | xargs -0 -n "$batchSize" -P "$(nproc)" bash -c \
    'for file do
        jq -e . "$file" > /dev/null 2>&1 || echo "$file"
    done'

echo "Others are valid..."
echo "Done"