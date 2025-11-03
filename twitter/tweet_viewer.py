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
        height: 3px !important;
        background-color: #1DA1F2 !important;
        border: none !important;
        margin-top: 30px !important;
        margin-bottom: 30px !important;
        width: 60% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    /* Add more space between tweets */
    .element-container {
        margin-bottom: 20px;
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
    """Display a tweet with only text and media content."""
    # Extract data from row
    text = row.get("text", "No text")

    # Get media paths
    photo_paths, video_paths = get_local_media_paths(row)

    # Start the frame container for the entire tweet
    with st.container():
        # Open the frame div that will contain ALL tweet content
        st.markdown(
            f"""
        <div style="border: 2px solid #1DA1F2; border-radius: 8px; padding: 20px; margin-bottom: 30px; text-align: center; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="margin: 10px 0; text-align: center; font-size: 16px; line-height: 1.5; color: #333;">{text}</div>
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
                            st.error(
                                f"📸 Image missing: {os.path.basename(photo_path)}"
                            )
                            st.caption(f"Path: {photo_path}")
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
                        st.error(f"🎥 Video missing: {os.path.basename(video_path)}")
                        st.caption(f"Path: {video_path}")
                except Exception as e:
                    st.error(f"Error displaying video: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

        # Close the framed div that contains everything
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function to run the Streamlit app."""
    st.title("🧹 Cleaned Tweet Viewer 🐦")
    st.markdown("### View AI-filtered flood disaster tweets")
    st.markdown("*Simple view: text and media only*")

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

    # Initialize variables
    csv_file = ""
    df = None
    sort_by = "Newest first"
    num_tweets = 10

    # Sidebar for file selection and filters
    with st.sidebar:
        st.header("Settings")

        # Dataset selection
        st.subheader("📊 Select Dataset")
        dataset_options = {
            "Assam Flood (Cleaned)": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
            "Bangladesh Flood (Cleaned)": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
            "Kerala Flood (Cleaned)": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
            "Pakistan Flood (Cleaned)": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
            "Custom Path": "custom",
        }

        selected_dataset = st.selectbox("Choose dataset:", list(dataset_options.keys()))

        if selected_dataset == "Custom Path":
            csv_file = st.text_input("CSV file path:", "")
        else:
            csv_file = dataset_options[selected_dataset]
            st.success(f"Selected: {selected_dataset}")
            st.info(f"Path: {csv_file}")

        if not csv_file:
            st.warning("Please select a dataset or enter a custom path.")
            return

        if not os.path.exists(csv_file):
            st.error(f"CSV file not found: {csv_file}")
            st.info("💡 Make sure you have run the cleaning process first!")
            return

        # Load the data
        try:
            df = pd.read_csv(csv_file)
            st.success(f"✅ Loaded {len(df)} cleaned tweets")

            # Show dataset statistics
            st.subheader("📈 Dataset Info")

            # Count media files
            photo_count = 0
            video_count = 0
            for _, row in df.iterrows():
                photo_paths, video_paths = get_local_media_paths(row)
                photo_count += len(photo_paths)
                video_count += len(video_paths)

            # Display stats
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 Total Tweets", len(df))
                st.metric("📸 Total Photos", photo_count)
            with col2:
                st.metric("🎥 Total Videos", video_count)

            # Check if this is a cleaned dataset
            if "cleaned_" in csv_file:
                st.info(
                    "🧹 This is a cleaned dataset (AI-filtered for flood disasters)"
                )

                # Check for classification log
                log_path = csv_file.replace(".csv", "_classification_log.json")
                if os.path.exists(log_path):
                    st.success("📜 Classification log available")
                else:
                    st.warning("📜 Classification log not found")

            # Sorting options only
            st.subheader("Display Options")

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
            total_tweets = len(df)
            st.write("Number of tweets to show (0 = show all):")
            num_tweets = st.slider("", 0, total_tweets, 10)
            if num_tweets == 0:
                st.text(f"Showing all {total_tweets} tweets")
                num_tweets = None  # No limit when showing all tweets

        except Exception as e:
            st.error(f"Error loading CSV file: {e}")
            return

    # Apply sorting only (no filters)
    filtered_df = df.copy()

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
    if num_tweets is not None:  # Only limit if num_tweets is not None (i.e., not 0)
        filtered_df = filtered_df.head(num_tweets)

    # Display tweet count
    if len(filtered_df) == 0:
        st.warning("No tweets found in the dataset.")
        return

    st.markdown(f"### 📋 Showing {len(filtered_df)} tweets")
    st.markdown("---")

    # Display each tweet with clear separators and numbering
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        # Add tweet number indicator
        st.markdown(
            f"""
            <div style="text-align: center; margin: 20px 0 10px 0;">
                <span style="background-color: #1DA1F2; color: white; padding: 5px 12px; border-radius: 15px; font-size: 14px; font-weight: bold;">
                    Tweet {i + 1}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        display_tweet(row)

        # Add a clear separator between tweets (but not after the last one)
        if i < len(filtered_df) - 1:
            st.markdown(
                """
                <div style="margin: 40px 0; border-top: 3px solid #1DA1F2; width: 60%; margin-left: auto; margin-right: auto;"></div>
                """,
                unsafe_allow_html=True,
            )

    # Add end marker
    st.markdown(
        """
        <div style="text-align: center; margin: 50px 0 30px 0;">
            <span style="background-color: #28a745; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold;">
                ✅ End of Tweets
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add footer
    st.markdown("---")
    st.markdown(
        "🛠️ Built with Streamlit • 🤖 AI-filtered using OpenAI • 📊 Data collected and cleaned using twitter_scraper.py"
    )

    # Add info about the cleaning process
    with st.expander("ℹ️ About the Data"):
        st.markdown(
            """
        **This dataset contains:**
        - AI-filtered flood disaster tweets
        - Text content and associated media files
        - High-quality, verified flood-related content only
        
        **Cleaning process:**
        - Each tweet analyzed by GPT-4o-mini
        - Non-flood content automatically filtered out
        - Only genuine flood disasters kept
        """
        )


if __name__ == "__main__":
    main()
