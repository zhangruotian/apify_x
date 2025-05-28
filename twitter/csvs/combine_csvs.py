import os

import pandas as pd


def combine_csv_files(csv_directory, output_filename="combined_tweets.csv"):
    """
    Combines all CSV files in a specified directory into a single CSV file,
    removing duplicate records.

    Args:
        csv_directory (str): The directory containing the CSV files.
        output_filename (str): The name of the output CSV file.

    Returns:
        str: The path to the combined CSV file, or None if an error occurs.
    """
    try:
        all_files = [
            os.path.join(csv_directory, f)
            for f in os.listdir(csv_directory)
            if f.endswith(".csv")
        ]
        if not all_files:
            print(f"No CSV files found in directory: {csv_directory}")
            return None

        print(f"Found {len(all_files)} CSV files to combine: {all_files}")

        df_list = []
        for file in all_files:
            try:
                df = pd.read_csv(file)
                df_list.append(df)
                print(f"Successfully read {file}, shape: {df.shape}")
            except pd.errors.EmptyDataError:
                print(f"Warning: {file} is empty and will be skipped.")
            except Exception as e:
                print(f"Error reading {file}: {e}")
                # Optionally, decide whether to skip or halt on error
                # For now, we skip problematic files
                continue

        if not df_list:
            print("No dataframes were successfully read. Exiting.")
            return None

        combined_df = pd.concat(df_list, ignore_index=True)
        print(f"Combined DataFrame shape before deduplication: {combined_df.shape}")

        # Deduplicate
        if "tweet_id" in combined_df.columns:
            print("Deduplicating based on 'tweet_id' column.")
            deduplicated_df = combined_df.drop_duplicates(subset=["tweet_id"])
        else:
            print(
                "Warning: 'tweet_id' column not found. Deduplicating based on all columns."
            )
            deduplicated_df = combined_df.drop_duplicates()

        print(f"Combined DataFrame shape after deduplication: {deduplicated_df.shape}")

        output_path = os.path.join(csv_directory, output_filename)
        deduplicated_df.to_csv(output_path, index=False, encoding="utf-8")
        print(
            f"Successfully combined and deduplicated CSV files. Output saved to: {output_path}"
        )
        return output_path

    except Exception as e:
        print(f"An error occurred during the CSV combination process: {e}")
        return None


if __name__ == "__main__":
    csv_dir = "../csvs"  # Directory where your CSVs are located

    # Create the directory if it doesn't exist (useful if running standalone)
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
        print(f"Created directory: {csv_dir}")
        print("Please add your CSV files to this directory and run the script again.")
    else:
        combined_file_path = combine_csv_files(csv_dir)
        if combined_file_path:
            print(f"Successfully created: {combined_file_path}")
        else:
            print("Failed to combine CSV files.")
