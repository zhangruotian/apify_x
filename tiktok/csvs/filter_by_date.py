import os

import pandas as pd


def filter_tiktok_posts_by_date_range(
    input_file, output_file=None, start_date="2024-07-01", end_date="2024-08-31"
):
    """
    Filter TikTok posts by upload date, keeping only posts within the specified date range.

    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to save the filtered CSV file (default: auto-generated)
        start_date (str): Start date in YYYY-MM-DD format (inclusive)
        end_date (str): End date in YYYY-MM-DD format (inclusive)

    Returns:
        str: Path to the filtered CSV file, or None if an error occurs
    """
    try:
        # Generate default output filename if not specified
        if output_file is None:
            start_date_str = start_date.replace("-", "")
            end_date_str = end_date.replace("-", "")
            output_file = f"tiktok_posts_{start_date_str}_to_{end_date_str}.csv"

        print(f"Reading file: {input_file}")
        df = pd.read_csv(input_file)
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

            # Convert string dates to datetime objects for comparison
            df["parsed_date"] = pd.to_datetime(
                df["uploaded_at_formatted"], errors="coerce"
            )
            date_column = "parsed_date"

        # Fall back to uploaded_at (Unix timestamp) if formatted date is not available
        elif "uploaded_at" in df.columns and df["uploaded_at"].notna().any():
            print("Using 'uploaded_at' column (Unix timestamp) for date filtering")

            # Convert Unix timestamps to datetime objects
            df["parsed_date"] = pd.to_datetime(
                df["uploaded_at"], unit="s", errors="coerce"
            )
            date_column = "parsed_date"

        else:
            print("Error: No usable date columns found in the dataset")
            return None

        # Convert dates to datetime for comparison
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        # Add one day to end_date to make it inclusive
        end_datetime = end_datetime + pd.Timedelta(days=1)

        print(
            f"Filtering to keep only posts from {start_date} to {end_date} (inclusive)"
        )

        # Handle timezone-aware dates if needed
        if df[date_column].dt.tz is not None:
            # Make datetime timezone-aware to match the data
            import pytz

            start_datetime = start_datetime.replace(tzinfo=pytz.UTC)
            end_datetime = end_datetime.replace(tzinfo=pytz.UTC)
            print("Using timezone-aware comparison (UTC)")

        # Filter posts by date range
        filtered_df = df[
            (df[date_column] >= start_datetime) & (df[date_column] < end_datetime)
        ].copy()
        filtered_count = len(filtered_df)

        # Remove the temporary parsing column
        if "parsed_date" in filtered_df.columns:
            filtered_df = filtered_df.drop(columns=["parsed_date"])

        print(
            f"Filtered to {filtered_count} posts ({filtered_count/original_count*100:.1f}% of original)"
        )

        # Save filtered data
        filtered_df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Filtered data saved to: {output_file}")

        return output_file

    except Exception as e:
        print(f"Error during filtering: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Filter TikTok posts by date range")
    parser.add_argument(
        "--input",
        "-i",
        required=False,
        help="Input CSV file (defaults to combined_tiktok_posts.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=False,
        help="Output CSV filename (defaults to auto-generated based on date range)",
    )
    parser.add_argument(
        "--start-date",
        "-s",
        required=False,
        default="2024-08-01",
        help="Start date in YYYY-MM-DD format (default: 2024-08-01)",
    )
    parser.add_argument(
        "--end-date",
        "-e",
        required=False,
        default="2024-10-31",
        help="End date in YYYY-MM-DD format (default: 2024-09-31)",
    )

    args = parser.parse_args()

    # Use default input file if not specified
    input_file = args.input or os.path.join(
        os.path.dirname(__file__), "combined_tiktok_posts.csv"
    )

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        print(
            "You may need to run combine_csvs.py first to generate the combined file."
        )
        return

    filter_tiktok_posts_by_date_range(
        input_file, args.output, args.start_date, args.end_date
    )


if __name__ == "__main__":
    main()
