#!/usr/bin/env python3
"""
Extract all fields from Twitter JSONL data into a comprehensive CSV file.
Each media item (photo, video) gets its own dedicated column for easier analysis.
"""

import csv
import datetime
import json
import os
import sys


def extract_hashtags(entities):
    """Extract hashtags from entities."""
    if not entities or "hashtags" not in entities:
        return []
    return [h.get("text", "") for h in entities["hashtags"]]


def extract_urls(entities):
    """Extract URLs from entities."""
    if not entities or "urls" not in entities:
        return []
    return [u.get("expanded_url", u.get("url", "")) for u in entities["urls"]]


def extract_user_mentions(entities):
    """Extract user mentions from entities."""
    if not entities or "user_mentions" not in entities:
        return []
    return [
        f"{u.get('name', '')}(@{u.get('screen_name', '')})"
        for u in entities["user_mentions"]
    ]


def extract_media_urls(item, media_type):
    """Extract media URLs from a single media item."""
    if media_type == "photo":
        if "media_url_https" in item:
            return item["media_url_https"]
    elif media_type == "video":
        if "variants" in item:
            # Get highest quality video
            highest_bitrate = 0
            best_url = ""
            for variant in item["variants"]:
                bitrate = variant.get("bitrate", 0)
                if bitrate > highest_bitrate:
                    highest_bitrate = bitrate
                    best_url = variant.get("url", "")
            return best_url
    return ""


def extract_all_media(tweet):
    """
    Extract all media from a tweet with dedicated columns for each item.

    Returns dict with:
    - photo1, photo2, ... photo9 (empty string if not present)
    - video1, video2, ... video5 (empty string if not present)
    """
    result = {}

    # Initialize photo and video columns to empty strings
    for i in range(1, 10):  # photo1 through photo9
        result[f"photo{i}"] = ""

    for i in range(1, 6):  # video1 through video5
        result[f"video{i}"] = ""

    # Lists to collect photo and video URLs
    photo_urls = []
    video_urls = []

    # Try to get media from the dedicated media field
    if "media" in tweet:
        media = tweet["media"]

        # Handle photos
        if "photo" in media and media["photo"]:
            for item in media["photo"]:
                url = extract_media_urls(item, "photo")
                if url and url not in photo_urls:
                    photo_urls.append(url)

        # Handle videos
        if "video" in media and media["video"]:
            for item in media["video"]:
                url = extract_media_urls(item, "video")
                if url and url not in video_urls:
                    video_urls.append(url)

    # Also check in entities.media as a backup
    if "entities" in tweet and "media" in tweet["entities"]:
        entity_media = tweet["entities"]["media"]

        for item in entity_media:
            media_type = item.get("type", "")

            if media_type == "photo":
                url = item.get("media_url_https", "")
                if url and url not in photo_urls:
                    photo_urls.append(url)

            elif media_type == "video":
                # If video_info exists, get the highest quality variant
                if "video_info" in item and "variants" in item["video_info"]:
                    highest_bitrate = 0
                    best_url = ""
                    for variant in item["video_info"]["variants"]:
                        bitrate = variant.get("bitrate", 0)
                        if bitrate > highest_bitrate:
                            highest_bitrate = bitrate
                            best_url = variant.get("url", "")

                    if best_url and best_url not in video_urls:
                        video_urls.append(best_url)

            elif (
                media_type == "animated_gif"
                and "video_info" in item
                and "variants" in item["video_info"]
            ):
                if item["video_info"]["variants"]:
                    url = item["video_info"]["variants"][0].get("url", "")
                    if url and url not in video_urls:
                        video_urls.append(url)

    # Fill in the photo columns
    for i, url in enumerate(photo_urls[:9]):  # Limit to 9 photos
        result[f"photo{i+1}"] = url

    # Fill in the video columns
    for i, url in enumerate(video_urls[:5]):  # Limit to 5 videos
        result[f"video{i+1}"] = url

    # Add counts
    result["photo_count"] = len(photo_urls)
    result["video_count"] = len(video_urls)

    return result


def extract_place_info(place):
    """Extract place information if available."""
    if not place:
        return {"place_name": "", "place_country": "", "place_type": ""}

    return {
        "place_name": place.get("name", ""),
        "place_country": place.get("country", ""),
        "place_type": place.get("place_type", ""),
    }


def extract_nested_fields(data, prefix="", skip_keys=None):
    """
    Extract nested fields from a dictionary.

    Args:
        data: The dictionary to extract fields from
        prefix: Prefix to add to extracted field names
        skip_keys: Keys to skip (will be handled separately)

    Returns:
        Dictionary with flattened fields
    """
    if skip_keys is None:
        skip_keys = ["entities", "user_info", "media", "place"]

    result = {}

    # Handle non-dict inputs gracefully
    if not isinstance(data, dict):
        return result

    for key, value in data.items():
        # Skip certain fields that we'll handle separately
        if key in skip_keys:
            continue

        field_name = f"{prefix}{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively process nested dictionaries
            nested_fields = extract_nested_fields(value, f"{field_name}_", skip_keys)
            result.update(nested_fields)
        elif isinstance(value, list):
            # For lists, we'll just store their count - individual items will be handled separately
            result[field_name + "_count"] = len(value)
        else:
            # Store the value directly, converting to string if necessary
            result[field_name] = str(value) if value is not None else ""

    return result


def flatten_tweet(tweet):
    """Extract and flatten all fields from a tweet."""
    # Start with basic top-level fields
    flat_tweet = extract_nested_fields(tweet)

    # Handle user_info fields
    if "user_info" in tweet and isinstance(tweet["user_info"], dict):
        user_info = extract_nested_fields(tweet["user_info"], "user_")
        flat_tweet.update(user_info)

    # Handle entities - use individual columns for hashtags
    if "entities" in tweet:
        # Extract lists
        hashtags = extract_hashtags(tweet.get("entities", {}))
        urls = extract_urls(tweet.get("entities", {}))
        mentions = extract_user_mentions(tweet.get("entities", {}))

        # Add hashtags as hashtag1, hashtag2, etc. (up to 10)
        for i, tag in enumerate(hashtags[:10]):
            flat_tweet[f"hashtag{i+1}"] = tag

        # Add URLs as url1, url2, etc. (up to 5)
        for i, url in enumerate(urls[:5]):
            flat_tweet[f"url{i+1}"] = url

        # Add mentions as mention1, mention2, etc. (up to 5)
        for i, mention in enumerate(mentions[:5]):
            flat_tweet[f"mention{i+1}"] = mention

        # Store counts
        flat_tweet["hashtag_count"] = len(hashtags)
        flat_tweet["url_count"] = len(urls)
        flat_tweet["mention_count"] = len(mentions)

    # Handle all media types with individual columns
    media_data = extract_all_media(tweet)
    flat_tweet.update(media_data)

    # Handle place information
    if "place" in tweet:
        place_info = extract_place_info(tweet["place"])
        flat_tweet.update(place_info)

    # Add fields for quoted tweets if available
    if "quoted" in tweet:
        quoted = tweet["quoted"]
        quoted_fields = {
            "quoted_tweet_id": quoted.get("tweet_id", ""),
            "quoted_text": quoted.get("text", ""),
        }

        # Handle quoted author separately
        if "author" in quoted and isinstance(quoted["author"], dict):
            author = quoted["author"]
            quoted_fields.update(
                {
                    "quoted_screen_name": author.get("screen_name", ""),
                    "quoted_name": author.get("name", ""),
                }
            )

        # Add other quoted tweet metrics
        for field in ["favorites", "retweets", "replies", "views", "quotes"]:
            quoted_fields[f"quoted_{field}"] = quoted.get(field, "")

        flat_tweet.update(quoted_fields)

    return flat_tweet


def process_jsonl_to_csv(
    input_file, output_file=None, verbose=False, output_csv_dir=None
):
    """
    Process a JSONL file of tweets and write to a CSV file.

    Args:
        input_file: Path to the input JSONL file
        output_file: Path to the output CSV file (optional, will generate based on input if not provided)
        verbose: Whether to show detailed processing information
        output_csv_dir: Directory to save the CSV file in (optional)

    Returns:
        str: Path to the created CSV file
    """
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return None

    # Generate output filename with timestamp if not provided
    if not output_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{basename}_csv_{timestamp}.csv"

    # If an output directory is specified, join it with the filename
    if output_csv_dir:
        # Ensure the output directory exists
        os.makedirs(output_csv_dir, exist_ok=True)
        output_file = os.path.join(output_csv_dir, os.path.basename(output_file))

    # Read all tweets first to build a complete list of columns
    all_tweets = []
    all_columns = set()

    print(f"Reading tweets from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if verbose and i % 100 == 0 and i > 0:
                print(f"Read {i} tweets...")
            elif (not verbose) and i % 10 == 0 and i > 0:
                print(f"Read {i} tweets...")

            try:
                tweet = json.loads(line.strip())
                flat_tweet = flatten_tweet(tweet)
                all_tweets.append(flat_tweet)
                all_columns.update(flat_tweet.keys())
            except json.JSONDecodeError:
                print(f"Warning: Could not parse line {i+1} as JSON. Skipping.")
            except Exception as e:
                print(f"Error processing tweet on line {i+1}: {str(e)}")

    # Sort columns for a more organized CSV
    sorted_columns = sorted(list(all_columns))

    # Make sure important columns come first
    priority_columns = [
        "tweet_id",
        "created_at",
        "screen_name",
        "text",
        "favorites",
        "retweets",
        "replies",
        "views",
        "bookmarks",
        "quotes",
    ]

    # Add media columns to priority list
    for i in range(1, 10):  # photo1 through photo9
        priority_columns.append(f"photo{i}")

    for i in range(1, 6):  # video1 through video5
        priority_columns.append(f"video{i}")

    # Add hashtag, URL, and mention columns
    for i in range(1, 11):  # hashtag1 through hashtag10
        priority_columns.append(f"hashtag{i}")

    for i in range(1, 6):  # url1 through url5
        priority_columns.append(f"url{i}")

    for i in range(1, 6):  # mention1 through mention5
        priority_columns.append(f"mention{i}")

    # Add count columns
    priority_columns.extend(
        [
            "photo_count",
            "video_count",
            "hashtag_count",
            "url_count",
            "mention_count",
            "conversation_id",
            "lang",
        ]
    )

    # Reorder columns with priority columns first
    final_columns = []
    for col in priority_columns:
        if col in sorted_columns:
            final_columns.append(col)
            sorted_columns.remove(col)
    final_columns.extend(sorted_columns)

    # Write the CSV file
    print(
        f"Writing {len(all_tweets)} tweets to {output_file} with {len(final_columns)} columns..."
    )
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_columns)
        writer.writeheader()

        for i, tweet in enumerate(all_tweets):
            if verbose and i % 100 == 0 and i > 0:
                print(f"Wrote {i} tweets...")
            elif (not verbose) and i % 10 == 0 and i > 0:
                print(f"Wrote {i} tweets...")

            # Ensure all columns are present
            for col in final_columns:
                if col not in tweet:
                    tweet[col] = ""

            try:
                writer.writerow(tweet)
            except Exception as e:
                print(f"Error writing tweet {tweet.get('tweet_id', i)}: {str(e)}")

    print(f"Successfully wrote {len(all_tweets)} tweets to {output_file}")
    print(f"CSV includes {len(final_columns)} columns")

    return output_file


def convert_jsonl_to_csv(
    input_file=None, output_file=None, verbose=False, output_csv_dir=None
):
    """
    Convert JSONL to CSV format with easy-to-use function signature for importing.
    This is the main function that should be imported by other scripts.

    Args:
        input_file: Path to the input JSONL file
        output_file: Path to the output CSV file (optional)
        verbose: Whether to show detailed processing information
        output_csv_dir: Directory to save the CSV file in (optional)

    Returns:
        str: Path to the created CSV file or None if failed
    """
    # Process the file and get the output path
    if not input_file:
        print("Error: No input file specified.")
        return None

    output_file = process_jsonl_to_csv(
        input_file, output_file, verbose, output_csv_dir=output_csv_dir
    )

    if output_file:
        print(f"\nConversion complete! CSV file saved to: {output_file}")
        print(
            "This CSV contains all data fields with dedicated columns for media items."
        )
        print(
            "Each photo and video has its own column (photo1-photo9, video1-video5) for easier analysis."
        )
        return output_file
    else:
        print("Failed to convert JSONL to CSV.")
        return None


if __name__ == "__main__":
    # Configure these parameters directly
    input_file = "tweets_20250505_153155.jsonl"  # Path to your JSONL file
    output_file = (
        None  # Set to None to auto-generate based on input file, or specify a path
    )
    verbose = False  # Set to True for more detailed processing information

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")

        # Look for the most recent JSONL file in the current directory
        jsonl_files = [f for f in os.listdir(".") if f.endswith(".jsonl")]

        if jsonl_files:
            # Sort by modification time, most recent first
            jsonl_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            most_recent = jsonl_files[0]
            print(f"Found most recent JSONL file: {most_recent}")
            print("Using this file instead.")
            input_file = most_recent
        else:
            print("No JSONL files found in the current directory.")
            print(
                "Edit the input_file parameter in the __main__ section to point to your JSONL file."
            )
            sys.exit(1)

    # Convert the file
    convert_jsonl_to_csv(input_file, output_file, verbose)
