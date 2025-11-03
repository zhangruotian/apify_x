import os
import sys

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def authenticate():
    """Handles Google Drive authentication."""
    if not os.path.exists("client_secrets.json"):
        print("ERROR: client_secrets.json not found.", file=sys.stderr)
        print("Please ensure it is in the project root directory.", file=sys.stderr)
        sys.exit(1)

    gauth = GoogleAuth()
    try:
        # Try to load saved credentials
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            # Authenticate if they're not there
            print(
                "Credentials not found. Please follow the browser authentication flow."
            )
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            print("Credentials expired. Refreshing token...")
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile("credentials.json")
    except Exception as e:
        print(f"\nAn error occurred during authentication: {e}", file=sys.stderr)
        print("It's possible the 'credentials.json' file is corrupt.", file=sys.stderr)
        print(
            "Please delete 'credentials.json' (if it exists) and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    return GoogleDrive(gauth)


def get_local_files(path):
    """Recursively gets a set of relative file paths from a local directory."""
    local_files = set()
    for root, _, files in os.walk(path):
        for name in files:
            full_path = os.path.join(root, name)
            relative_path = os.path.relpath(full_path, path)
            local_files.add(relative_path)
    return local_files


def get_drive_files_recursive(drive, folder_id, path_prefix=""):
    """Recursively gets a set of relative file paths from a Google Drive folder."""
    remote_files = set()
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        file_list = drive.ListFile({"q": query}).GetList()
        for f in file_list:
            current_path = os.path.join(path_prefix, f["title"])
            if f["mimeType"] == "application/vnd.google-apps.folder":
                remote_files.update(
                    get_drive_files_recursive(drive, f["id"], current_path)
                )
            else:
                remote_files.add(current_path)
    except Exception as e:
        print(
            f"Error listing files in Drive folder ID {folder_id}: {e}", file=sys.stderr
        )
    return remote_files


def main():
    """Main function to verify uploaded files."""
    local_root_path = "google_drive_upload"
    if not os.path.isdir(local_root_path):
        print(f"Local staging folder '{local_root_path}' not found.", file=sys.stderr)
        print(
            "Please run 'prepare_and_upload.py' at least once to create it.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Connecting to Google Drive to verify uploaded files...")
    drive = authenticate()
    print("Authentication successful.")

    root_folder_name = "google_drive_upload"
    file_list = drive.ListFile(
        {
            "q": f"title='{root_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        }
    ).GetList()

    if not file_list:
        print(f"\nRoot folder '{root_folder_name}' not found on Google Drive.")
        print("It seems no folders were uploaded successfully.")
        local_files_total = len(get_local_files(local_root_path))
        print(f"There are {local_files_total} files ready to be uploaded locally.")
        return

    drive_root_folder_id = file_list[0]["id"]
    print(f"Found root folder '{root_folder_name}' on Google Drive.")

    print("\nScanning local files...")
    local_files = get_local_files(local_root_path)
    print(f"Found {len(local_files)} files staged locally.")

    print("Scanning Google Drive files... (This may take a moment)")
    remote_files = get_drive_files_recursive(drive, drive_root_folder_id)
    print(f"Found {len(remote_files)} files on Google Drive.")

    print("\n--- Verification Report ---")
    missing_files = local_files - remote_files

    if not missing_files:
        print("✅ Success! All local files have been uploaded to Google Drive.")
    else:
        print(
            f"🔥 Comparison complete. Found {len(missing_files)} missing file(s) on Google Drive."
        )
        print(
            "\nTo complete the upload, please run the 'prepare_and_upload.py' script again."
        )
        print(
            "It will automatically skip existing files and only upload what is missing."
        )


if __name__ == "__main__":
    main()
