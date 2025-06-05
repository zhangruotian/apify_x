import datetime

import pandas as pd

# Read the CSV file
input_file = "combined_tweets.csv"
output_file = "filtered_tweets_aug_to_oct_2024.csv"

# Load the data
print(f"Reading data from {input_file}...")
df = pd.read_csv(input_file)

# Convert 'created_at' to datetime
# Example format: 'Tue Aug 20 20:57:00 +0000 2024'
print("Converting dates...")
df["created_at_dt"] = pd.to_datetime(df["created_at"], format="%a %b %d %H:%M:%S %z %Y")

# Filter for tweets from July 1, 2024 to October 31, 2024
start_date = datetime.datetime(2024, 8, 1, tzinfo=datetime.timezone.utc)
end_date = datetime.datetime(2024, 10, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
filtered_df = df[
    (df["created_at_dt"] >= start_date) & (df["created_at_dt"] <= end_date)
]

# Drop the temporary datetime column we added
filtered_df = filtered_df.drop(columns=["created_at_dt"])

# Get counts for original and filtered data
original_count = len(df)
filtered_count = len(filtered_df)
print(f"Original tweet count: {original_count}")
print(f"Filtered tweet count (July 2024 to October 31, 2024): {filtered_count}")
print(f"Removed {original_count - filtered_count} tweets outside the date range")

# Save to new CSV file
print(f"Saving filtered data to {output_file}...")
filtered_df.to_csv(output_file, index=False)
print("Done!")
