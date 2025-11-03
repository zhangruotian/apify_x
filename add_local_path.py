import os

import pandas as pd

# Define file paths
input_csv_path = "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031.csv"
output_csv_path = "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv"
videos_directory = "tiktok/bangladesh_flood/videos"


def add_video_local_path():
    """
    Reads a CSV file, adds a 'video_local_path' column based on the 'id',
    and saves it to a new CSV file.
    """
    print(f"Reading input CSV file: {input_csv_path}")
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found at {input_csv_path}")
        return

    try:
        df = pd.read_csv(input_csv_path)

        # Check if 'id' column exists
        if "id" not in df.columns:
            print("Error: 'id' column not found in the CSV file.")
            return

        # Check if 'video_local_path' column already exists
        if "video_local_path" in df.columns:
            print("The 'video_local_path' column already exists. Overwriting it.")

        print("Generating 'video_local_path' column...")
        # Construct the local path using the videos_directory and the post id
        df["video_local_path"] = df["id"].apply(
            lambda post_id: os.path.join(videos_directory, f"tiktok_{post_id}.mp4")
        )

        print(f"Saving new CSV file to: {output_csv_path}")
        df.to_csv(output_csv_path, index=False)

        print("\nProcess complete.")
        print(f"A new file has been created at: {output_csv_path}")
        # Display the first 5 rows of the new column for verification
        print("\nVerification: First 5 entries for 'video_local_path':")
        print(df[["id", "video_local_path"]].head())

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    add_video_local_path()
