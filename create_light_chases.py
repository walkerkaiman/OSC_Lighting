import csv
import os
import random

# Output directory
output_dir = "test_chases"
os.makedirs(output_dir, exist_ok=True)

# Create 5 test files with varying lengths
for i in range(1, 6):
    filename = f"chase_{i}.csv"
    filepath = os.path.join(output_dir, filename)

    # Random number of rows between 60 and 1000
    num_rows = random.randint(60, 1000)
    # Random number of channels per row (max 512)
    num_channels = random.randint(50, 512)

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for _ in range(num_rows):
            # Write a row with random values (0-255) for each channel
            row = [random.randint(0, 255) for _ in range(num_channels)]
            writer.writerow(row)

filepath_list = os.listdir(output_dir)
filepath_list
