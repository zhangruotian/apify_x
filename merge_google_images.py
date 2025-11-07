#!/usr/bin/env python3
"""
Merge Google Images CSV into existing Twitter CSV.
Downloads images with retry logic and only appends successfully downloaded records.
"""

import csv
import hashlib
import os
import sys
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from PIL import Image

import requests


def get_file_extension(url):
    """Extract file extension from URL."""
    parsed_url = urlparse(url)
    path = parsed_url.path
    _, ext = os.path.splitext(path)
    
    # If there's no extension or it's unusual, use defaults
    if not ext or len(ext) > 5:
        # Try to detect from URL parameters or content-type
        if "video" in url.lower():
            return ".mp4"
        else:
            return ".jpg"
    
    return ext


def sanitize_filename(filename):
    """Sanitize filename to be valid on all operating systems."""
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Limit length to avoid file system limitations
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def validate_image(image_path):
    """Validate if an image file can be opened and is not corrupted."""
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify the image
        # Reopen for format check (verify closes the file)
        with Image.open(image_path) as img:
            img.format  # Check format
        return True
    except Exception:
        return False


def download_file_with_retry(url, save_path, max_retries=3, timeout=30, retry_delay=2):
    """
    Download a file from URL with retry logic.
    
    Args:
        url: URL of the file to download
        save_path: Path where the file should be saved
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each request
        retry_delay: Delay in seconds between retries
    
    Returns:
        True if download was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Make a request to get the file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, stream=True, timeout=timeout, headers=headers)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            # Save the file
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was written and has content
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                # Validate image is not corrupted
                if validate_image(save_path):
                    return True
                else:
                    # Delete corrupted file
                    try:
                        os.remove(save_path)
                    except:
                        pass
                    print(f"  ⚠️  Attempt {attempt + 1}/{max_retries}: Image file is corrupted")
            else:
                print(f"  ⚠️  Attempt {attempt + 1}/{max_retries}: File downloaded but is empty")
                
        except requests.exceptions.Timeout:
            print(f"  ⚠️  Attempt {attempt + 1}/{max_retries}: Timeout downloading {url}")
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Attempt {attempt + 1}/{max_retries}: Error downloading {url}: {str(e)[:100]}")
        except Exception as e:
            print(f"  ⚠️  Attempt {attempt + 1}/{max_retries}: Unexpected error: {str(e)[:100]}")
        
        # Wait before retrying (except on last attempt)
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    # All retries failed
    return False


def generate_tweet_id_from_url(url):
    """Generate a unique tweet ID from image URL using hash."""
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:15]
    # Convert to numeric-like ID (Twitter IDs are numeric strings)
    numeric_id = str(int(url_hash, 16))[:18]
    return numeric_id


def create_twitter_row_from_google_image(row, image_url, local_path):
    """Create a Twitter CSV compatible row from Google Images data."""
    # Generate a unique tweet ID from the image URL
    tweet_id = generate_tweet_id_from_url(image_url)
    
    # Create a new row with all required fields
    twitter_row = {
        'tweet_id': tweet_id,
        'created_at': '',  # Google Images doesn't have creation date
        'screen_name': 'GoogleImages',
        'text': row.get('title', '') or row.get('contentUrl', ''),
        'favorites': '',
        'retweets': '',
        'replies': '',
        'views': '',
        'bookmarks': '',
        'quotes': '',
        'photo1': image_url,
        'photo2': '',
        'photo3': '',
        'photo4': '',
        'photo5': '',
        'photo6': '',
        'photo7': '',
        'photo8': '',
        'photo9': '',
        'video1': '',
        'video2': '',
        'video3': '',
        'video4': '',
        'video5': '',
        'hashtag1': '',
        'hashtag2': '',
        'hashtag3': '',
        'hashtag4': '',
        'hashtag5': '',
        'hashtag6': '',
        'hashtag7': '',
        'hashtag8': '',
        'hashtag9': '',
        'hashtag10': '',
        'url1': row.get('contentUrl', ''),
        'url2': '',
        'mention1': '',
        'mention2': '',
        'mention3': '',
        'mention4': '',
        'mention5': '',
        'photo_count': '1',
        'video_count': '0',
        'hashtag_count': '0',
        'url_count': '1' if row.get('contentUrl') else '0',
        'mention_count': '0',
        'conversation_id': '',
        'lang': '',
        'in_reply_to_screen_name': '',
        'in_reply_to_status_id_str': '',
        'in_reply_to_user_id_str': '',
        'place_country': '',
        'place_name': '',
        'place_type': '',
        'quoted_author_avatar': '',
        'quoted_author_blue_verified': '',
        'quoted_author_created_at': '',
        'quoted_author_name': '',
        'quoted_author_rest_id': '',
        'quoted_author_screen_name': '',
        'quoted_bookmarks': '',
        'quoted_conversation_id': '',
        'quoted_created_at': '',
        'quoted_favorites': '',
        'quoted_lang': '',
        'quoted_name': '',
        'quoted_quotes': '',
        'quoted_replies': '',
        'quoted_retweets': '',
        'quoted_screen_name': '',
        'quoted_text': '',
        'quoted_tweet_id': '',
        'quoted_views': '',
        'source': 'Google Images',
        'type': 'image',
        'user_avatar': '',
        'user_created_at': '',
        'user_description': '',
        'user_favourites_count': '',
        'user_followers_count': '',
        'user_friends_count': '',
        'user_location': '',
        'user_name': 'Google Images',
        'user_rest_id': '',
        'user_screen_name': 'GoogleImages',
        'user_verified': 'False',
        'community_id': '',
        'photo1_local_path': local_path,
        'photo2_local_path': '',
        'photo3_local_path': '',
        'photo4_local_path': '',
        'photo5_local_path': '',
        'photo6_local_path': '',
        'photo7_local_path': '',
        'photo8_local_path': '',
        'photo9_local_path': '',
        'video1_local_path': '',
        'video2_local_path': '',
        'video3_local_path': '',
        'video4_local_path': '',
        'video5_local_path': '',
        'video_key_frames': '',
        'all_images': f'["{local_path}"]',
        'is_flood_related': '',
        'flood_classification_confidence': '',
        'flood_classification_reason': '',
    }
    
    return twitter_row


def merge_google_images_csv(
    google_images_csv,
    existing_twitter_csv,
    campaign_base_dir,
    max_retries=3
):
    """
    Merge Google Images CSV into existing Twitter CSV.
    
    Args:
        google_images_csv: Path to Google Images CSV file
        existing_twitter_csv: Path to existing Twitter CSV file
        campaign_base_dir: Base directory for the campaign (e.g., 'twitter/bangladesh_flood')
        max_retries: Maximum number of retry attempts for image downloads
    
    Returns:
        Path to the updated CSV file
    """
    # Check if files exist
    if not os.path.exists(google_images_csv):
        print(f"Error: Google Images CSV file '{google_images_csv}' not found!")
        return None
    
    if not os.path.exists(existing_twitter_csv):
        print(f"Error: Existing Twitter CSV file '{existing_twitter_csv}' not found!")
        return None
    
    # Create directories for media_cleaned/photos
    media_cleaned_dir = os.path.join(campaign_base_dir, "media_cleaned")
    photos_dir = os.path.join(media_cleaned_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)
    
    # Read existing Twitter CSV to get all fieldnames
    print(f"Reading existing Twitter CSV: {existing_twitter_csv}")
    with open(existing_twitter_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        twitter_fieldnames = reader.fieldnames
        existing_rows = list(reader)
    
    print(f"Found {len(existing_rows)} existing rows")
    
    # Read Google Images CSV (try different encodings)
    print(f"\nReading Google Images CSV: {google_images_csv}")
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'Windows-1252', 'cp1252']
    google_rows = None
    
    for encoding in encodings:
        try:
            with open(google_images_csv, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                google_rows = list(reader)
            print(f"Successfully read CSV with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    
    if google_rows is None:
        print(f"Error: Could not read Google Images CSV with any of the tried encodings: {encodings}")
        return None
    
    print(f"Found {len(google_rows)} Google Images rows")
    
    # Process Google Images rows
    new_rows = []
    successful_downloads = 0
    failed_downloads = 0
    
    print(f"\nDownloading images with {max_retries} retries...")
    for idx, google_row in enumerate(google_rows, 1):
        image_url = google_row.get('imageUrl', '').strip()
        if not image_url:
            print(f"  [{idx}/{len(google_rows)}] ⚠️  Skipping row {idx}: No imageUrl")
            failed_downloads += 1
            continue
        
        # Get file extension
        ext = get_file_extension(image_url)
        
        # Generate filename
        url_hash = hashlib.md5(image_url.encode('utf-8')).hexdigest()[:12]
        filename = f"google_images_{url_hash}{ext}"
        save_path = os.path.join(photos_dir, filename)
        
        # Use relative path for CSV (media_cleaned/photos)
        relative_path = os.path.join("twitter", "bangladesh_flood", "media_cleaned", "photos", filename)
        
        # Check if file already exists and is valid
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            if validate_image(save_path):
                print(f"  [{idx}/{len(google_rows)}] ✅ Already exists: {filename}")
                twitter_row = create_twitter_row_from_google_image(google_row, image_url, relative_path)
                new_rows.append(twitter_row)
                successful_downloads += 1
                continue
            else:
                # Delete corrupted existing file
                try:
                    os.remove(save_path)
                    print(f"  [{idx}/{len(google_rows)}] ⚠️  Existing file corrupted, re-downloading: {filename}")
                except:
                    pass
        
        # Download with retry
        print(f"  [{idx}/{len(google_rows)}] Downloading: {image_url[:80]}...")
        if download_file_with_retry(image_url, save_path, max_retries=max_retries):
            # Final validation after download
            if validate_image(save_path):
                print(f"  [{idx}/{len(google_rows)}] ✅ Success: {filename}")
                twitter_row = create_twitter_row_from_google_image(google_row, image_url, relative_path)
                new_rows.append(twitter_row)
                successful_downloads += 1
            else:
                # Delete corrupted file
                try:
                    os.remove(save_path)
                except:
                    pass
                print(f"  [{idx}/{len(google_rows)}] ❌ Image corrupted after download: {filename}")
                failed_downloads += 1
        else:
            print(f"  [{idx}/{len(google_rows)}] ❌ Failed after {max_retries} attempts: {filename}")
            failed_downloads += 1
            # Skip this record - don't add to new_rows
    
    print(f"\n===== DOWNLOAD SUMMARY =====")
    print(f"Total Google Images rows: {len(google_rows)}")
    print(f"Successfully downloaded: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"New rows to append: {len(new_rows)}")
    
    if not new_rows:
        print("\n⚠️  No images were successfully downloaded. No changes made to CSV.")
        return None
    
    # Combine existing rows with new rows
    all_rows = existing_rows + new_rows
    
    # Generate output CSV filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(existing_twitter_csv))[0]
    output_csv_name = f"{base_name}_merged_{timestamp}.csv"
    output_csv_path = os.path.join(campaign_base_dir, "csvs", output_csv_name)
    
    # Write the combined CSV
    print(f"\nWriting merged CSV: {output_csv_path}")
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=twitter_fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\n✅ Successfully merged CSV!")
    print(f"  - Existing rows: {len(existing_rows)}")
    print(f"  - New rows added: {len(new_rows)}")
    print(f"  - Total rows: {len(all_rows)}")
    print(f"  - Output file: {output_csv_path}")
    
    return output_csv_path


def check_and_remove_corrupted_images(csv_path, campaign_base_dir):
    """
    Check merged CSV for corrupted images and remove both the images and CSV records.
    
    Returns:
        Path to cleaned CSV file
    """
    import pandas as pd
    from pathlib import Path
    
    print(f"\n{'='*70}")
    print("🔍 Checking for corrupted images in merged CSV...")
    print(f"{'='*70}")
    
    df = pd.read_csv(csv_path)
    original_count = len(df)
    print(f"📊 Original records: {original_count}")
    
    project_root = Path(csv_path).resolve().parent.parent.parent.parent
    corrupted_indices = []
    deleted_images = []
    
    for idx, row in df.iterrows():
        # Check photo1_local_path (Google Images use photo1)
        photo_path = row.get('photo1_local_path', '')
        if pd.notna(photo_path) and str(photo_path).strip():
            photo_path_str = str(photo_path).strip()
            # Convert to absolute path
            if not os.path.isabs(photo_path_str):
                abs_path = project_root / photo_path_str
            else:
                abs_path = Path(photo_path_str)
            
            if abs_path.exists():
                if not validate_image(abs_path):
                    print(f"  ❌ Row {idx+1}: Corrupted image found: {abs_path.name}")
                    corrupted_indices.append(idx)
                    deleted_images.append(abs_path)
                    # Delete corrupted image
                    try:
                        abs_path.unlink()
                        print(f"     Deleted corrupted image: {abs_path.name}")
                    except Exception as e:
                        print(f"     Failed to delete: {e}")
    
    if corrupted_indices:
        print(f"\n🗑️  Removing {len(corrupted_indices)} records with corrupted images...")
        df_cleaned = df.drop(corrupted_indices).reset_index(drop=True)
        
        # Save cleaned CSV
        df_cleaned.to_csv(csv_path, index=False)
        print(f"✅ Cleaned CSV saved: {len(df_cleaned)} records remaining")
        print(f"   Removed: {len(corrupted_indices)} records")
        return csv_path
    else:
        print("✅ No corrupted images found!")
        return csv_path


if __name__ == "__main__":
    # Configuration
    google_images_csv = "bangladesh flood 2024 (Google Images)(Data).csv"
    existing_twitter_csv = "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv"
    campaign_base_dir = "twitter/bangladesh_flood"
    max_retries = 3
    
    # Merge CSV files
    output_csv = merge_google_images_csv(
        google_images_csv,
        existing_twitter_csv,
        campaign_base_dir,
        max_retries=max_retries
    )
    
    if output_csv:
        print("\n✅ Merge complete!")
        print(f"Images saved to: {os.path.join(campaign_base_dir, 'media_cleaned', 'photos')}")
        
        # Check and remove corrupted images
        print("\n" + "="*70)
        cleaned_csv = check_and_remove_corrupted_images(output_csv, campaign_base_dir)
        print(f"\n✅ Final CSV: {cleaned_csv}")
    else:
        print("\n❌ Merge failed!")
        sys.exit(1)

