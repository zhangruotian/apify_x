#!/usr/bin/env python
# Extract TikTok data from JSONL and convert to CSV

import csv
import json
import os


def convert_jsonl_to_csv(jsonl_path, output_csv_dir=None):
    """
    Convert a JSONL file of TikTok posts to a CSV file.

    Args:
        jsonl_path (str): Path to the JSONL file with TikTok data
        output_csv_dir (str): Optional. Directory to save the output CSV file.

    Returns:
        str: Path to the created CSV file
    """
    if not os.path.exists(jsonl_path):
        print(f"Error: File {jsonl_path} not found")
        return None

    # Create CSV file path
    base_name = os.path.basename(jsonl_path)
    csv_filename = base_name.replace(".jsonl", ".csv")
    if output_csv_dir:
        os.makedirs(output_csv_dir, exist_ok=True)
        csv_path = os.path.join(output_csv_dir, csv_filename)
    else:
        csv_path = jsonl_path.replace(".jsonl", ".csv")

    # Define CSV headers based on TikTok data structure
    csv_headers = [
        # Basic post info
        "id",
        "title",
        "views",
        "likes",
        "comments",
        "shares",
        "bookmarks",
        "hashtags",
        "uploaded_at",
        "uploaded_at_formatted",
        "post_url",
        # Channel info
        "channel_name",
        "channel_username",
        "channel_id",
        "channel_bio",
        "channel_url",
        "channel_avatar",
        "channel_verified",
        "channel_followers",
        "channel_following",
        "channel_videos",
        # Video info
        "video_width",
        "video_height",
        "video_ratio",
        "video_duration",
        "video_url",
        "video_cover",
        "video_thumbnail",
        # Song info
        "song_id",
        "song_title",
        "song_artist",
        "song_album",
        "song_duration",
        "song_cover",
    ]

    try:
        with open(jsonl_path, "r", encoding="utf-8") as jsonl_file, open(
            csv_path, "w", encoding="utf-8", newline=""
        ) as csv_file:

            # Set up CSV writer
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()

            # Process each line (tweet) in the JSONL file
            line_count = 0
            processed_count = 0

            for line in jsonl_file:
                line_count += 1

                try:
                    # Parse JSON from the line
                    tiktok_post = json.loads(line.strip())

                    # Create a dictionary for the CSV row
                    csv_row = {}

                    # Extract basic post info
                    csv_row["id"] = tiktok_post.get("id", "")
                    csv_row["title"] = tiktok_post.get("title", "")
                    csv_row["views"] = tiktok_post.get("views", 0)
                    csv_row["likes"] = tiktok_post.get("likes", 0)
                    csv_row["comments"] = tiktok_post.get("comments", 0)
                    csv_row["shares"] = tiktok_post.get("shares", 0)
                    csv_row["bookmarks"] = tiktok_post.get("bookmarks", 0)

                    # Join hashtags with comma
                    hashtags = tiktok_post.get("hashtags", [])
                    csv_row["hashtags"] = ",".join(hashtags) if hashtags else ""

                    # Time fields
                    csv_row["uploaded_at"] = tiktok_post.get("uploadedAt", "")
                    csv_row["uploaded_at_formatted"] = tiktok_post.get(
                        "uploadedAtFormatted", ""
                    )

                    # Post URL
                    csv_row["post_url"] = tiktok_post.get("postPage", "")

                    # Extract channel info
                    channel = tiktok_post.get("channel", {})
                    csv_row["channel_name"] = channel.get("name", "")
                    csv_row["channel_username"] = channel.get("username", "")
                    csv_row["channel_id"] = channel.get("id", "")
                    csv_row["channel_bio"] = channel.get("bio", "").replace("\n", " ")
                    csv_row["channel_url"] = channel.get("url", "")
                    csv_row["channel_avatar"] = channel.get("avatar", "")
                    csv_row["channel_verified"] = channel.get("verified", False)
                    csv_row["channel_followers"] = channel.get("followers", 0)
                    csv_row["channel_following"] = channel.get("following", 0)
                    csv_row["channel_videos"] = channel.get("videos", 0)

                    # Extract video info
                    video = tiktok_post.get("video", {})
                    csv_row["video_width"] = video.get("width", 0)
                    csv_row["video_height"] = video.get("height", 0)
                    csv_row["video_ratio"] = video.get("ratio", "")
                    csv_row["video_duration"] = video.get("duration", 0)
                    csv_row["video_url"] = video.get("url", "")
                    csv_row["video_cover"] = video.get("cover", "")
                    csv_row["video_thumbnail"] = video.get("thumbnail", "")

                    # Extract song info
                    song = tiktok_post.get("song", {})
                    csv_row["song_id"] = song.get("id", "")
                    csv_row["song_title"] = song.get("title", "")
                    csv_row["song_artist"] = song.get("artist", "")
                    csv_row["song_album"] = song.get("album", "")
                    csv_row["song_duration"] = song.get("duration", 0)
                    csv_row["song_cover"] = song.get("cover", "")

                    # Write the row to CSV
                    writer.writerow(csv_row)
                    processed_count += 1

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON on line {line_count}: {e}")
                except Exception as e:
                    print(f"Error processing line {line_count}: {e}")

            print(
                f"Successfully processed {processed_count} of {line_count} TikTok posts"
            )
            print(f"CSV file saved to: {csv_path}")

            return csv_path

    except Exception as e:
        print(f"Error during CSV conversion: {e}")
        return None


if __name__ == "__main__":
    # For testing: you can provide a JSONL file path as a command-line argument
    import sys

    if len(sys.argv) > 1:
        jsonl_path = sys.argv[1]
        convert_jsonl_to_csv(jsonl_path)
    else:
        print("Please provide a JSONL file path as an argument")
