import datetime
import os

import pandas as pd


def filter_tweets_by_date(input_path, output_path, start_date_str, end_date_str):
    """
    Filters tweets in a CSV file based on a date range.

    Args:
        input_path (str): The path to the input CSV file.
        output_path (str): The path to save the filtered CSV file.
        start_date_str (str): The start date in 'YYYY-MM-DD' format.
        end_date_str (str): The end date in 'YYYY-MM-DD' format.
    """
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'")
        return

    # Load the data
    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path, low_memory=False)

    # Convert 'created_at' to datetime
    print("Converting dates...")
    df["created_at_dt"] = pd.to_datetime(
        df["created_at"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce"
    )

    # Define the date range with timezone info
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc
    )
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc
    )

    # Filter the DataFrame
    filtered_df = df[
        (df["created_at_dt"] >= start_date) & (df["created_at_dt"] <= end_date)
    ].copy()

    # Drop the temporary datetime column we added
    filtered_df.drop(columns=["created_at_dt"], inplace=True)

    # Get counts for original and filtered data
    original_count = len(df)
    filtered_count = len(filtered_df)
    print(f"Original tweet count: {original_count}")
    print(
        f"Filtered tweet count ({start_date_str} to {end_date_str}): {filtered_count}"
    )
    print(f"Removed {original_count - filtered_count} tweets outside the date range.")

    # Save to new CSV file
    print(f"Saving filtered data to {output_path}...")
    filtered_df.to_csv(output_path, index=False, encoding="utf-8")
    print("Done!")


if __name__ == "__main__":
    # --- Configuration ---
    campaign_name = "kerala_flood"  # <--- Change this for other campaigns
    start_date_filter = "2024-07-15"
    end_date_filter = "2024-09-01"
    # -------------------

    # Define file paths
    base_dir = os.path.join("twitter", campaign_name, "csvs")
    input_filename = f"combined_{campaign_name}_tweets.csv"
    output_filename = f"filtered_{campaign_name}_tweets_{start_date_filter.replace('-', '')}_{end_date_filter.replace('-', '')}.csv"

    input_file_path = os.path.join(base_dir, input_filename)
    output_file_path = os.path.join(base_dir, output_filename)

    # Run the filtering function
    filter_tweets_by_date(
        input_file_path, output_file_path, start_date_filter, end_date_filter
    )
