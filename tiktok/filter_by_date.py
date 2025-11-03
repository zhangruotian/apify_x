import os

import pandas as pd


def filter_tiktok_posts_by_date_range(
    input_path, output_path, start_date_str, end_date_str
):
    """
    Filter TikTok posts by upload date, keeping only posts within the specified date range.

    Args:
        input_path (str): Path to the input CSV file.
        output_path (str): Path to save the filtered CSV file.
        start_date_str (str): Start date in YYYY-MM-DD format (inclusive).
        end_date_str (str): End date in YYYY-MM-DD format (inclusive).

    Returns:
        str: Path to the filtered CSV file, or None if an error occurs.
    """
    try:
        if not os.path.exists(input_path):
            print(f"Error: Input file not found at '{input_path}'")
            return None

        print(f"Reading file: {input_path}")
        df = pd.read_csv(input_path, low_memory=False)
        original_count = len(df)
        print(f"Original file contains {original_count} posts")

        # Check which date column is available and usable
        date_column = None

        # Try using uploaded_at_formatted first (ISO format string)
        if (
            "uploaded_at_formatted" in df.columns
            and df["uploaded_at_formatted"].notna().any()
        ):
            print("Using 'uploaded_at_formatted' column for date filtering")
            df["parsed_date"] = pd.to_datetime(
                df["uploaded_at_formatted"], errors="coerce"
            )
            date_column = "parsed_date"
        # Fall back to uploaded_at (Unix timestamp)
        elif "uploaded_at" in df.columns and df["uploaded_at"].notna().any():
            print("Using 'uploaded_at' column (Unix timestamp) for date filtering")
            df["parsed_date"] = pd.to_datetime(
                df["uploaded_at"], unit="s", errors="coerce"
            )
            date_column = "parsed_date"
        else:
            print("Error: No usable date columns found in the dataset")
            df.to_csv(output_path, index=False, encoding="utf-8")
            print(f"File saved without date filtering to: {output_path}")
            return output_path

        # Drop rows where date could not be parsed
        df.dropna(subset=[date_column], inplace=True)

        # Convert filter dates to datetime objects
        start_datetime = pd.to_datetime(start_date_str).tz_localize("UTC")
        end_datetime = (
            pd.to_datetime(end_date_str)
            .tz_localize("UTC")
            .replace(hour=23, minute=59, second=59)
        )

        print(f"Filtering posts from {start_date_str} to {end_date_str} (inclusive).")

        # Ensure the date column in the dataframe is timezone-aware (UTC) for correct comparison
        if df[date_column].dt.tz is None:
            df[date_column] = df[date_column].dt.tz_localize("UTC")
        else:
            df[date_column] = df[date_column].dt.tz_convert("UTC")

        # Filter posts by date range
        filtered_df = df[
            (df[date_column] >= start_datetime) & (df[date_column] <= end_datetime)
        ].copy()
        filtered_count = len(filtered_df)

        # Remove the temporary parsing column
        if "parsed_date" in filtered_df.columns:
            filtered_df.drop(columns=["parsed_date"], inplace=True)

        print(
            f"Filtered to {filtered_count} posts ({filtered_count/original_count*100:.1f}% of original)"
        )

        # Save filtered data
        filtered_df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"Filtered data saved to: {output_path}")

        return output_path

    except Exception as e:
        print(f"Error during filtering: {e}")
        return None


if __name__ == "__main__":
    # --- Configuration ---
    campaign_name = "pakistan_flood"  # <--- Change this for other campaigns
    start_date_filter = "2022-06-01"
    end_date_filter = "2023-01-01"
    # -------------------

    # Define file paths
    base_dir = os.path.join("tiktok", campaign_name, "csvs")
    input_filename = f"combined_{campaign_name}_posts.csv"
    output_filename = f"filtered_{campaign_name}_posts_{start_date_filter.replace('-', '')}_{end_date_filter.replace('-', '')}.csv"

    input_file_path = os.path.join(base_dir, input_filename)
    output_file_path = os.path.join(base_dir, output_filename)

    # Check if input file exists
    if not os.path.exists(input_file_path):
        print(f"Error: Input file {input_file_path} not found.")
        print(
            "You may need to run combine_csvs.py first to generate the combined file."
        )
    else:
        # Run the filtering function
        filter_tiktok_posts_by_date_range(
            input_file_path, output_file_path, start_date_filter, end_date_filter
        )
