import os
import shutil
import sys

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def prepare_files():
    """Prepares the local directory structure for upload."""
    print("Preparing local file structure...")
    upload_dir = "google_drive_upload"
    if os.path.exists(upload_dir):
        print(f"'{upload_dir}' already exists. Removing it before staging files.")
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)

    # TikTok data structure
    tiktok_upload_dir = os.path.join(upload_dir, "tiktok")
    tiktok_datasets = {
        "Bangladesh Flood": {
            "csv": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031.csv",
            "videos": "tiktok/bangladesh_flood/videos",
        },
        "Assam Flood": {
            "csv": "tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv",
            "videos": "tiktok/assam_flood/videos",
        },
        "Kerala Flood": {
            "csv": "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv",
            "videos": "tiktok/kerala_flood/videos",
        },
        "Pakistan Flood": {
            "csv": "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv",
            "videos": "tiktok/pakistan_flood/videos",
        },
        "South Asia Flood": {
            "csv": "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv",
            "videos": "tiktok/south_asia_flood/videos",
        },
    }

    for folder, paths in tiktok_datasets.items():
        dest_folder = os.path.join(tiktok_upload_dir, folder)
        media_folder = os.path.join(dest_folder, "media")
        os.makedirs(media_folder, exist_ok=True)

        if os.path.exists(paths["csv"]):
            shutil.copy(paths["csv"], dest_folder)
            print(f"Copied {paths['csv']} to {dest_folder}")
        else:
            print(f"Warning: TikTok CSV file not found: {paths['csv']}")

        if os.path.exists(paths["videos"]):
            print(f"Copying videos from {paths['videos']} to {media_folder}...")
            # shutil.copytree(paths["videos"], media_folder, dirs_exist_ok=True)
            # Manually copy files to handle symbolic links correctly by copying the actual content.
            for item_name in os.listdir(paths["videos"]):
                source_item = os.path.join(paths["videos"], item_name)
                target_item = os.path.join(media_folder, item_name)
                if os.path.islink(source_item):
                    # If it's a symlink, copy the file it points to
                    shutil.copy2(os.path.realpath(source_item), target_item)
                elif os.path.isdir(source_item):
                    # If it's a directory, copy the whole directory
                    shutil.copytree(source_item, target_item, dirs_exist_ok=True)
                else:
                    # It's a regular file
                    shutil.copy2(source_item, target_item)
            print("...Done copying videos.")
        else:
            print(f"Warning: TikTok videos directory not found: {paths['videos']}")

    # Twitter data structure
    twitter_upload_dir = os.path.join(upload_dir, "twitter")
    twitter_datasets = {
        "Assam Flood": {
            "csv": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
            "media": "twitter/assam_flood/media_cleaned",
        },
        "Bangladesh Flood": {
            "csv": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
            "media": "twitter/bangladesh_flood/media_cleaned",
        },
        "Kerala Flood": {
            "csv": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
            "media": "twitter/kerala_flood/media_cleaned",
        },
        "Pakistan Flood": {
            "csv": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
            "media": "twitter/pakistan_flood/media_cleaned",
        },
    }

    for folder, paths in twitter_datasets.items():
        dest_folder = os.path.join(twitter_upload_dir, folder)
        media_folder = os.path.join(dest_folder, "media")
        os.makedirs(media_folder, exist_ok=True)

        if os.path.exists(paths["csv"]):
            shutil.copy(paths["csv"], dest_folder)
            print(f"Copied {paths['csv']} to {dest_folder}")
        else:
            print(f"Warning: Twitter CSV file not found: {paths['csv']}")

        if os.path.exists(paths["media"]):
            print(f"Copying media from {paths['media']} to {media_folder}...")
            # shutil.copytree(paths["media"], media_folder, dirs_exist_ok=True)
            # Manually copy files to handle symbolic links correctly by copying the actual content.
            for item_name in os.listdir(paths["media"]):
                source_item = os.path.join(paths["media"], item_name)
                target_item = os.path.join(media_folder, item_name)
                if os.path.islink(source_item):
                    shutil.copy2(os.path.realpath(source_item), target_item)
                elif os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_item, target_item)
            print("...Done copying media.")
        else:
            print(f"Warning: Twitter media directory not found: {paths['media']}")

    print("File preparation complete.")
    return upload_dir


def upload_folder_to_drive(drive, folder_path, parent_folder_id=None):
    """Recursively uploads a folder to Google Drive."""
    folder_name = os.path.basename(folder_path)

    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"

    file_list = drive.ListFile({"q": query}).GetList()
    if file_list:
        drive_folder = file_list[0]
        print(f"Folder '{folder_name}' already exists. Using existing folder.")
    else:
        print(f"Creating folder: {folder_name}")
        folder_metadata = {
            "title": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            folder_metadata["parents"] = [{"id": parent_folder_id}]

        drive_folder = drive.CreateFile(folder_metadata)
        drive_folder.Upload()

    folder_id = drive_folder["id"]

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            upload_folder_to_drive(drive, item_path, folder_id)
        else:
            # Check if file already exists
            file_query = (
                f"title='{item}' and '{folder_id}' in parents and trashed=false"
            )
            existing_files = drive.ListFile({"q": file_query}).GetList()
            if existing_files:
                print(f"  File '{item}' already exists. Skipping upload.")
                continue

            print(f"  Uploading file: {item}")
            try:
                file_drive = drive.CreateFile(
                    {"title": item, "parents": [{"id": folder_id}]}
                )
                file_drive.SetContentFile(item_path)
                file_drive.Upload()
            except Exception as e:
                print(f"    Failed to upload {item}: {e}")
                print("    Skipping this file.")


def main():
    """Main function to prepare files and upload to Google Drive."""
    # Step 1: Prepare the local directory
    local_folder_path = prepare_files()

    # Step 2: Authenticate and upload to Google Drive
    try:
        # Check for client_secrets.json before attempting to authenticate
        if not os.path.exists("client_secrets.json"):
            print(
                "ERROR: client_secrets.json not found in the project root.",
                file=sys.stderr,
            )
            print(
                "Please follow the instructions to download it from Google Cloud Console and place it in the project directory.",
                file=sys.stderr,
            )
            sys.exit(1)

        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
        drive = GoogleDrive(gauth)

        print("\nStarting Google Drive upload...")
        upload_folder_to_drive(drive, local_folder_path)
        print("\nUpload to Google Drive complete!")
        print(
            f"A staging folder '{local_folder_path}' was created. You can remove it if you no longer need it."
        )

    except Exception as e:
        print(f"An error occurred during Google Drive upload: {e}", file=sys.stderr)
        print(
            "Please ensure you have PyDrive2 installed ('pip install PyDrive2') and that you complete the authentication process in your browser.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
