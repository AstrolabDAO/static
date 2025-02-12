#!/bin/bash

# Check if svgo is installed
if ! command -v svgo &> /dev/null
then
    echo "Error: svgo is not installed. Please install it globally."
    exit 1
fi

echo "SVGO is installed. Starting optimization process..."
# Find directories and optimize SVG files
find ./static/assets/images -type d | while read -r dir
do
    echo "Processing directory: $dir"
    svgo --multipass -f "$dir" --config=./svgo.config.js | \
    awk '
        # Store filename when we see it
        /:$/ {
            filename = substr($1, 1, length($1)-1)
            next
        }
        
        # Skip "Done in" lines
        /Done in/ {
            next
        }
        
        # Process size lines
        /KiB/ {
            # Extract initial size
            initial_size = $1
            
            # Extract percentage if present
            if ($3 == "-" && $4 ~ /%/) {
                percentage = $4
                final_size = $6
            } else {
                percentage = "0%"
                final_size = initial_size
            }
            
            # Convert KiB to KB
            initial_kb = sprintf("%.3f", substr(initial_size, 1, length(initial_size)-3) * 1.024)
            final_kb = sprintf("%.3f", substr(final_size, 1, length(final_size)-3) * 1.024)
            
            # Print result
            if (filename != "") {
                printf "%s - %s = %sKB ✔️\n", filename, percentage, final_kb
                filename = ""  # Reset filename for next entry
            } else {
                printf "%s %s = %sKB ✔️\n", initial_kb, percentage, final_kb
            }
        }
    '
done

