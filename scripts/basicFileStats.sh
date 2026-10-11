#!/bin/bash

echo -e "Basic Statistics for a Directory\n"

usage() {
    echo -e "Usage: ./$0 <directory>"
}

if [ -z "$1" ]; then
    echo "Fill in a directory..."
    usage
    exit 1
fi

if [ ! -d "$1" ]; then
    echo "$1 is not a valid directory."
    usage
    exit 1
fi

fileCount=$(find "$1" -maxdepth 1 -type f | wc -l)
echo -e "Number of files: $fileCount\n"

folderSize=$(du -sb "$1" | awk '{print $1}')
echo -e "Size of directory: $(awk "BEGIN {printf \"%.2f\", $folderSize / 1073741824}") GB"
# found this to be best solution to avoid integer division and get a decimal

if [ "$fileCount" -gt 0 ]; then
    averageFileSize=$((folderSize / fileCount))
    echo -e "Average file size: $(awk "BEGIN {printf \"%.2f\", $averageFileSize / 1024}") KB\n"
fi # note, bash only expands things in double quotes

# meaning most races
largestFiles=$(find "$1" -type f -printf "%s\t%p\n" | sort -n | tail -n 10 | sort -rn)
echo -e "Largest (10) files: \n\n$largestFiles\n"