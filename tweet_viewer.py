#!/usr/bin/env python3
"""
Tweet Viewer - A Streamlit app to display tweets with their text, images, videos, and metadata.
This app reads the CSV file with local media paths created by download_media.py.
"""

import base64
import glob
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Tweet Viewer",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add CSS for better styling
st.markdown(
    """
    <style>
    .tweet-container {
        border: 1px solid #ddd;
        border-radius: 0 0 10px 10px;
        padding: 15px;
        margin-bottom: 30px;
        background-color: white;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .tweet-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        justify-content: center;
    }
    .tweet-meta {
        color: #657786;
        font-size: 14px;
        margin-bottom: 10px;
        text-align: center;
    }
    .tweet-stats {
        display: flex;
        color: #657786;
        font-size: 14px;
        margin-top: 10px;
        justify-content: center;
    }
    .stat {
        margin-right: 20px;
    }
    .media-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
        justify-content: center;
        align-items: center;
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
    }
    .hashtag {
        color: #1DA1F2;
        font-weight: 500;
    }
    /* Center and fix width for images */
    .stImage {
        display: flex !important;
        justify-content: center !important;
        margin: 0 auto !important;
        width: auto !important;
        text-align: center !important;
    }
    .stImage > img {
        max-width: 200px !important;
        max-height: 200px !important;
        object-fit: contain !important;
        margin: 0 auto !important;
    }
    /* Center and fix width for videos */
    .stVideo {
        display: flex !important;
        justify-content: center !important;
    }
    .stVideo > div {
        max-width: 320px !important;
        margin: 0 auto !important;
    }
    /* Fix for all media to be centered */
    [data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
    }
    /* Center link text */
    .element-container:has(a) {
        text-align: center;
    }
    /* Center all markdown elements */
    .element-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    /* Make sure images are centered in their containers */
    [data-testid="column"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    /* Fix for image containers */
    [data-testid="stImage"] {
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
    }
    /* Make dividers more visible */
    hr {
        height: 2px !important;
        background-color: #888 !important;
        border: none !important;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def find_latest_csv_with_local_paths():
    """Find the most recent CSV file with local paths in the current directory."""
    # First try to find a CSV with local paths
    csv_files = glob.glob("*with_local_paths*.csv")
    if csv_files:
        # Sort by modification time, most recent first
        latest_file = max(csv_files, key=os.path.getmtime)
        return latest_file

    # If not found, look for any CSV file
    csv_files = glob.glob("*.csv")
    if csv_files:
        # Sort by modification time, most recent first
        latest_file = max(csv_files, key=os.path.getmtime)
        return latest_file

    return None


def get_local_media_paths(row):
    """Extract local media paths from a row."""
    photo_paths = []
    video_paths = []

    # Extract photo paths
    for i in range(1, 10):  # photo1 through photo9
        col = f"photo{i}_local_path"
        if col in row and pd.notna(row[col]) and row[col] != "":
            photo_paths.append(row[col])

    # Extract video paths
    for i in range(1, 6):  # video1 through video5
        col = f"video{i}_local_path"
        if col in row and pd.notna(row[col]) and row[col] != "":
            video_paths.append(row[col])

    return photo_paths, video_paths


def get_hashtags(row):
    """Extract hashtags from a row."""
    hashtags = []

    # Extract hashtags
    for i in range(1, 11):  # hashtag1 through hashtag10
        col = f"hashtag{i}"
        if col in row and pd.notna(row[col]) and row[col] != "":
            hashtags.append(row[col])

    return hashtags


def get_links(row):
    """Extract links from a row."""
    links = []

    # Extract links
    for i in range(1, 6):  # url1 through url5
        col = f"url{i}"
        if col in row and pd.notna(row[col]) and row[col] != "":
            links.append(row[col])

    return links


def get_mentions(row):
    """Extract user mentions from a row."""
    mentions = []

    # Extract mentions
    for i in range(1, 6):  # mention1 through mention5
        col = f"mention{i}"
        if col in row and pd.notna(row[col]) and row[col] != "":
            mentions.append(row[col])

    return mentions


def get_base64_video(video_path):
    """Convert video file to base64 for embedding."""
    try:
        file_bytes = Path(video_path).read_bytes()
        encoded = base64.b64encode(file_bytes).decode()
        return encoded
    except Exception as e:
        st.error(f"Error encoding video: {e}")
        return None


def display_tweet(row):
    """Display a tweet with its text, media, and metadata."""
    # Extract data from row
    tweet_id = row.get("tweet_id", "Unknown")
    screen_name = row.get("screen_name", "Unknown")
    name = row.get("user_name", screen_name)
    text = row.get("text", "No text")
    created_at = row.get("created_at", "")
    favorites = row.get("favorites", 0)
    retweets = row.get("retweets", 0)
    replies = row.get("replies", 0)

    # Get media paths
    photo_paths, video_paths = get_local_media_paths(row)

    # Get hashtags, links, mentions
    hashtags = get_hashtags(row)
    links = get_links(row)
    mentions = get_mentions(row)

    # Start the frame container for the entire tweet
    with st.container():
        # Open the frame div that will contain ALL tweet content
        st.markdown(
            f"""
        <div style="border: 1px solid #1DA1F2; border-radius: 8px; padding: 15px; margin-bottom: 20px; text-align: center; background-color: #f8f9fa;">
            <div style="font-weight: bold; text-align: center;">@{screen_name} - {name}</div>
            <div style="margin: 10px 0; text-align: center;">{text}</div>
            <div style="color: #657786; font-size: 14px; text-align: center;">{created_at}</div>
        """,
            unsafe_allow_html=True,
        )

        # Display photos in a grid
        if photo_paths:
            # Calculate how many columns to use based on number of photos
            if len(photo_paths) == 1:
                num_cols = 1
            elif len(photo_paths) == 2:
                num_cols = 2
            else:
                num_cols = 3

            # Add a media-grid wrapper
            st.markdown(
                '<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-top: 15px; margin-bottom: 15px;">',
                unsafe_allow_html=True,
            )

            cols = st.columns(num_cols)
            for i, photo_path in enumerate(photo_paths):
                try:
                    col_idx = i % num_cols
                    with cols[col_idx]:
                        if os.path.exists(photo_path):
                            image = Image.open(photo_path)

                            # Resize large images to more reasonable dimensions
                            max_width = (
                                200  # Maximum width for images, reduced from 250
                            )
                            if image.width > max_width:
                                ratio = max_width / image.width
                                new_height = int(image.height * ratio)
                                # Use simple resize without specifying resampling method
                                image = image.resize((max_width, new_height))

                            # Use explicit centering but not full column width
                            st.image(image, use_container_width=False)
                        else:
                            st.warning(f"Image file not found: {photo_path}")
                except Exception as e:
                    st.error(f"Error displaying image: {e}")

            # Close the media-grid wrapper
            st.markdown("</div>", unsafe_allow_html=True)

        # Handle videos - create a placeholder in the frame
        if video_paths:
            st.markdown(
                '<div style="text-align: center; margin: 15px 0;">',
                unsafe_allow_html=True,
            )

            for video_path in video_paths:
                try:
                    if os.path.exists(video_path):
                        video_file = open(video_path, "rb")
                        video_bytes = video_file.read()
                        # Add container for video to improve centering
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            # Display video with a limited width and centered
                            st.video(video_bytes, start_time=0)
                    else:
                        st.warning(f"Video file not found: {video_path}")
                except Exception as e:
                    st.error(f"Error displaying video: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

        # Now add HTML content for stats, hashtags, links, ID inside the frame
        html_content = []

        # Add statistics
        html_content.append(
            f"""
            <div style="margin-top: 10px; text-align: center;">
                ❤️ {favorites} Likes • 
                🔁 {retweets} Retweets • 
                💬 {replies} Replies
            </div>
        """
        )

        # Add hashtags
        if hashtags:
            html_content.append(
                "<div style='text-align: center; margin-top: 10px;'><strong>Hashtags:</strong> "
                + ", ".join([f"#{tag}" for tag in hashtags])
                + "</div>"
            )

        # Add links
        if links:
            html_content.append(
                "<div style='text-align: center; margin-top: 10px;'><strong>Links:</strong></div>"
            )
            for link in links:
                html_content.append(
                    f"<div style='text-align: center;'><a href='{link}'>{link}</a></div>"
                )

        # Add Tweet ID
        html_content.append(
            f"<div style='text-align: center; margin-top: 10px;'><small>Tweet ID: {tweet_id}</small></div>"
        )

        # Add all the HTML content to the frame
        st.markdown("\n".join(html_content), unsafe_allow_html=True)

        # Close the framed div that contains everything
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function to run the Streamlit app."""
    st.title("Tweet Viewer 🐦")
    st.markdown("### View tweets with their text, images, videos, and metadata")

    # Center the content
    st.markdown(
        """
    <style>
    .main > div {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .st-emotion-cache-16txtl3 h1, 
    .st-emotion-cache-16txtl3 h2, 
    .st-emotion-cache-16txtl3 h3 {
        text-align: center;
    }
    /* Make sure images are centered in their containers */
    [data-testid="column"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    /* Fix for image containers */
    [data-testid="stImage"] {
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar for file selection and filters
    with st.sidebar:
        st.header("Settings")

        # File selection
        csv_file = st.text_input("CSV file path (leave empty for latest)", "")
        if not csv_file:
            latest_csv = find_latest_csv_with_local_paths()
            if latest_csv:
                csv_file = latest_csv
                st.success(f"Using latest CSV file: {latest_csv}")

                if "with_local_paths" not in latest_csv:
                    st.warning(
                        "This CSV file may not have local media paths. Some images and videos might not display."
                    )
            else:
                st.error(
                    "No CSV file found. Please run twitter_scraper.py and download_media.py first."
                )
                return

        if not os.path.exists(csv_file):
            st.error(f"CSV file not found: {csv_file}")
            return

        # Load the data
        try:
            df = pd.read_csv(csv_file)
            st.info(f"Loaded {len(df)} tweets")

            # Filter options
            st.subheader("Filters")

            # Filter by media type
            media_filter = st.selectbox(
                "Show tweets with:",
                [
                    "All",
                    "Photos only",
                    "Videos only",
                    "Both photos and videos",
                    "No media",
                ],
            )

            # Filter by hashtag
            all_hashtags = []
            for i in range(1, 11):
                col = f"hashtag{i}"
                if col in df.columns:
                    hashtags = df[col].dropna().unique().tolist()
                    all_hashtags.extend([h for h in hashtags if h])

            all_hashtags = sorted(list(set(all_hashtags)))
            if all_hashtags:
                selected_hashtag = st.selectbox(
                    "Filter by hashtag:", ["None"] + all_hashtags
                )
            else:
                selected_hashtag = "None"

            # Filter by username
            all_usernames = sorted(df["screen_name"].dropna().unique().tolist())
            if all_usernames:
                selected_username = st.selectbox(
                    "Filter by username:", ["None"] + all_usernames
                )
            else:
                selected_username = "None"

            # Show tweets with most engagement
            sort_by = st.selectbox(
                "Sort by:",
                [
                    "Newest first",
                    "Oldest first",
                    "Most likes",
                    "Most retweets",
                    "Most replies",
                ],
            )

            # Number of tweets to show
            num_tweets = st.slider("Number of tweets to show:", 1, 100, 10)

        except Exception as e:
            st.error(f"Error loading CSV file: {e}")
            return

    # Apply filters
    filtered_df = df.copy()

    # Filter by media type
    if media_filter == "Photos only":
        # Check if any photo column has a value
        has_photos = False
        for i in range(1, 10):
            col = f"photo{i}_local_path"
            if col in filtered_df.columns:
                has_photos |= filtered_df[col].notna() & (filtered_df[col] != "")
        filtered_df = filtered_df[has_photos]
    elif media_filter == "Videos only":
        # Check if any video column has a value
        has_videos = False
        for i in range(1, 6):
            col = f"video{i}_local_path"
            if col in filtered_df.columns:
                has_videos |= filtered_df[col].notna() & (filtered_df[col] != "")
        filtered_df = filtered_df[has_videos]
    elif media_filter == "Both photos and videos":
        # Check if any photo column and any video column have values
        has_photos = False
        for i in range(1, 10):
            col = f"photo{i}_local_path"
            if col in filtered_df.columns:
                has_photos |= filtered_df[col].notna() & (filtered_df[col] != "")

        has_videos = False
        for i in range(1, 6):
            col = f"video{i}_local_path"
            if col in filtered_df.columns:
                has_videos |= filtered_df[col].notna() & (filtered_df[col] != "")

        filtered_df = filtered_df[has_photos & has_videos]
    elif media_filter == "No media":
        # Check if no photo column and no video column have values
        has_photos = False
        for i in range(1, 10):
            col = f"photo{i}_local_path"
            if col in filtered_df.columns:
                has_photos |= filtered_df[col].notna() & (filtered_df[col] != "")

        has_videos = False
        for i in range(1, 6):
            col = f"video{i}_local_path"
            if col in filtered_df.columns:
                has_videos |= filtered_df[col].notna() & (filtered_df[col] != "")

        filtered_df = filtered_df[~(has_photos | has_videos)]

    # Filter by hashtag
    if selected_hashtag != "None":
        has_hashtag = False
        for i in range(1, 11):
            col = f"hashtag{i}"
            if col in filtered_df.columns:
                has_hashtag |= filtered_df[col] == selected_hashtag
        filtered_df = filtered_df[has_hashtag]

    # Filter by username
    if selected_username != "None":
        filtered_df = filtered_df[filtered_df["screen_name"] == selected_username]

    # Sort by selected option
    try:
        if sort_by == "Newest first":
            # Type ignore comment to suppress linter errors
            filtered_df = filtered_df.sort_values("created_at", ascending=False)  # type: ignore
        elif sort_by == "Oldest first":
            filtered_df = filtered_df.sort_values("created_at", ascending=True)  # type: ignore
        elif sort_by == "Most likes":
            filtered_df = filtered_df.sort_values("favorites", ascending=False)  # type: ignore
        elif sort_by == "Most retweets":
            filtered_df = filtered_df.sort_values("retweets", ascending=False)  # type: ignore
        elif sort_by == "Most replies":
            filtered_df = filtered_df.sort_values("replies", ascending=False)  # type: ignore
    except Exception as e:
        st.warning(f"Unable to sort: {e}")

    # Limit number of tweets to show
    filtered_df = filtered_df.head(num_tweets)

    # Display tweet count
    if len(filtered_df) == 0:
        st.warning("No tweets match the selected filters.")
        return

    st.markdown(f"### Showing {len(filtered_df)} tweets")

    # Display each tweet with dividers between them (but not after the last one)
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        display_tweet(row)
        # Add a divider only if it's not the last tweet
        if i < len(filtered_df) - 1:
            st.divider()

    # Add footer
    st.markdown("---")
    st.markdown(
        "Built with Streamlit • Data collected using twitter_scraper.py and download_media.py"
    )


if __name__ == "__main__":
    main()
