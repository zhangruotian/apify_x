#!/usr/bin/env python3
"""
TikTok Viewer - A Streamlit app to display TikTok posts with their videos and metadata.
This app reads the CSV file created by tiktok_scraper.py and extract_tiktok_data.py.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="TikTok Viewer",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add CSS for better styling
st.markdown(
    """
    <style>
    .tiktok-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 30px;
        background-color: white;
        max-width: 550px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .tiktok-title {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 10px;
        text-align: center;
    }
    .tiktok-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        justify-content: center;
        width: 100%;
    }
    .tiktok-channel {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
    }
    .tiktok-channel-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .tiktok-channel-info {
        text-align: left;
    }
    .tiktok-channel-name {
        font-weight: bold;
        font-size: 16px;
    }
    .tiktok-channel-username {
        color: #777;
        font-size: 14px;
    }
    .tiktok-meta {
        color: #657786;
        font-size: 14px;
        margin-bottom: 10px;
        text-align: center;
    }
    .tiktok-stats {
        display: flex;
        justify-content: space-around;
        color: #657786;
        font-size: 14px;
        margin-top: 15px;
        width: 100%;
    }
    .stat {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .stat-value {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .stat-label {
        color: #888;
    }
    .hashtag {
        color: #25F4EE;
        font-weight: 500;
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
    /* Make sure videos are centered in their containers */
    [data-testid="column"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    /* Make dividers more visible */
    hr {
        height: 2px !important;
        background-color: #888 !important;
        border: none !important;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }
    /* TikTok colors for stats */
    .likes {
        color: #EE1D52;
    }
    .comments {
        color: #25F4EE;
    }
    .shares {
        color: #4DE3E0;
    }
    .views {
        color: #999999;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def find_latest_csv():
    """Find the most recent CSV file in the csvs directory."""
    csvs_dir = os.path.join(os.path.dirname(__file__), "csvs")

    # First try to find a filtered CSV file
    filtered_files = list(Path(csvs_dir).glob("tiktok_posts_20240801_to_20241031.csv"))
    if filtered_files:
        return str(max(filtered_files, key=os.path.getmtime))


    return None


def get_video_path(post_id):
    """Get the local path to a video file based on its ID."""
    video_dir = os.path.join(os.path.dirname(__file__), "media", "videos")
    video_path = os.path.join(video_dir, f"tiktok_{post_id}.mp4")

    if os.path.exists(video_path):
        return video_path

    return None


def format_number(num):
    """Format large numbers to a more readable format (e.g., 1.2K, 3.4M)."""
    if num is None or pd.isna(num):
        return "0"

    num = float(num)
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(int(num))


def display_tiktok_post(row):
    """Display a TikTok post with its video and metadata."""
    # Extract data from row
    post_id = row.get("id", "Unknown")
    title = row.get("title", "")
    views = row.get("views", 0)
    likes = row.get("likes", 0)
    comments = row.get("comments", 0)
    shares = row.get("shares", 0)
    bookmarks = row.get("bookmarks", 0)
    hashtags = row.get("hashtags", "")
    uploaded_at = row.get("uploaded_at_formatted", "")

    # Extract channel info
    channel_name = row.get("channel_name", "")
    channel_username = row.get("channel_username", "")
    channel_avatar = row.get("channel_avatar", "")
    channel_url = row.get("channel_url", "")
    channel_verified = row.get("channel_verified", False)

    # Get local video path
    video_path = get_video_path(post_id)

    # Start the container for the entire post
    with st.container():
        # Open the frame div
        st.markdown(
            f"""
            <div class="tiktok-container">
                <div class="tiktok-header">
                    <div class="tiktok-title">{title}</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Display channel info
        st.markdown(
            f"""
            <div class="tiktok-channel">
                <img src="{channel_avatar}" class="tiktok-channel-avatar" onerror="this.src='https://via.placeholder.com/40'">
                <div class="tiktok-channel-info">
                    <div class="tiktok-channel-name">
                        {channel_name} {"✓" if channel_verified else ""}
                    </div>
                    <div class="tiktok-channel-username">@{channel_username}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display video if available
        if video_path:
            try:
                video_file = open(video_path, "rb")
                video_bytes = video_file.read()
                # Center the video with columns
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.video(video_bytes, start_time=0)
            except Exception as e:
                st.error(f"Error displaying video: {e}")
        else:
            st.warning("Video not downloaded. Run download_media.py first.")

        # Display hashtags
        if hashtags and isinstance(hashtags, str):
            hashtag_list = hashtags.split(",")
            hashtag_html = ", ".join([f"#{tag.strip()}" for tag in hashtag_list])
            st.markdown(
                f'<div style="margin: 10px 0; text-align: center;">{hashtag_html}</div>',
                unsafe_allow_html=True,
            )

        # Display upload date
        if uploaded_at:
            st.markdown(
                f'<div class="tiktok-meta">{uploaded_at}</div>',
                unsafe_allow_html=True,
            )

        # Display stats
        st.markdown(
            f"""
            <div class="tiktok-stats">
                <div class="stat">
                    <div class="stat-value views">{format_number(views)}</div>
                    <div class="stat-label">Views</div>
                </div>
                <div class="stat">
                    <div class="stat-value likes">{format_number(likes)}</div>
                    <div class="stat-label">Likes</div>
                </div>
                <div class="stat">
                    <div class="stat-value comments">{format_number(comments)}</div>
                    <div class="stat-label">Comments</div>
                </div>
                <div class="stat">
                    <div class="stat-value shares">{format_number(shares)}</div>
                    <div class="stat-label">Shares</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{format_number(bookmarks)}</div>
                    <div class="stat-label">Bookmarks</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 10px;">
                <small>Post ID: {post_id}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Close the container div
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function to run the Streamlit app."""
    st.title("TikTok Viewer 🎵")
    st.markdown("### View TikTok posts with videos and engagement metrics")

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
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize variables
    csv_file = ""
    df = None
    has_video = "All posts"
    selected_hashtag = "None"
    selected_username = "None"
    sort_by = "Most views"
    num_posts = 10

    # Sidebar for file selection and filters
    with st.sidebar:
        st.header("Settings")

        # File selection
        default_csv_path = find_latest_csv()
        csv_file = st.text_input("CSV file path", value=default_csv_path or "")

        if not csv_file:
            st.error("No CSV file found or specified")
            return

        if not os.path.exists(csv_file):
            st.error(f"CSV file not found: {csv_file}")
            return

        # Load the data
        try:
            df = pd.read_csv(csv_file)
            st.info(f"Loaded {len(df)} TikTok posts")

            # Filter options
            st.subheader("Filters")

            # Filter by video availability
            has_video = st.selectbox(
                "Show posts:",
                [
                    "All posts",
                    "Only posts with downloaded videos",
                ],
            )

            # Filter by hashtag
            if "hashtags" in df.columns:
                # Extract all hashtags from the comma-separated lists
                all_hashtags = set()
                for hashtags_str in df["hashtags"].dropna():
                    if hashtags_str:
                        all_hashtags.update(
                            [tag.strip() for tag in hashtags_str.split(",")]
                        )

                all_hashtags = sorted(list(all_hashtags))
                if all_hashtags:
                    selected_hashtag = st.selectbox(
                        "Filter by hashtag:", ["None"] + all_hashtags
                    )

            # Filter by username
            if "channel_username" in df.columns:
                all_usernames = sorted(
                    df["channel_username"].dropna().unique().tolist()
                )
                if all_usernames:
                    selected_username = st.selectbox(
                        "Filter by username:", ["None"] + all_usernames
                    )

            # Sort options
            sort_by = st.selectbox(
                "Sort by:",
                [
                    "Most views",
                    "Most likes",
                    "Most comments",
                    "Most shares",
                    "Newest first",
                    "Oldest first",
                ],
            )

            # Number of posts to show
            total_posts = len(df)
            st.write("Number of posts to show (0 = show all):")
            num_posts = st.slider("", 0, total_posts, 10)
            if num_posts == 0:
                st.text(f"Showing all {total_posts} posts")
                num_posts = None  # No limit

        except Exception as e:
            st.error(f"Error loading CSV file: {e}")
            return

    # Apply filters
    filtered_df = df.copy()

    # Filter by video availability
    if has_video == "Only posts with downloaded videos":
        # Create a new column indicating if the video is available locally
        filtered_df["has_local_video"] = filtered_df["id"].apply(
            lambda x: os.path.exists(
                os.path.join(
                    os.path.dirname(__file__), "media", "videos", f"tiktok_{x}.mp4"
                )
            )
        )
        filtered_df = filtered_df[filtered_df["has_local_video"]]

    # Filter by hashtag
    if selected_hashtag != "None" and "hashtags" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["hashtags"].fillna("").str.contains(selected_hashtag)
        ]

    # Filter by username
    if selected_username != "None" and "channel_username" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["channel_username"] == selected_username]

    # Sort by selected option
    try:
        if sort_by == "Most views":
            filtered_df = filtered_df.sort_values("views", ascending=False)
        elif sort_by == "Most likes":
            filtered_df = filtered_df.sort_values("likes", ascending=False)
        elif sort_by == "Most comments":
            filtered_df = filtered_df.sort_values("comments", ascending=False)
        elif sort_by == "Most shares":
            filtered_df = filtered_df.sort_values("shares", ascending=False)
        elif sort_by == "Newest first":
            filtered_df = filtered_df.sort_values("uploaded_at", ascending=False)
        elif sort_by == "Oldest first":
            filtered_df = filtered_df.sort_values("uploaded_at", ascending=True)
    except Exception as e:
        st.warning(f"Unable to sort: {e}")

    # Limit number of posts to show
    if num_posts is not None:
        filtered_df = filtered_df.head(num_posts)

    # Display post count
    if len(filtered_df) == 0:
        st.warning("No posts match the selected filters.")
        return

    st.markdown(f"### Showing {len(filtered_df)} TikTok posts")

    # Display each post with dividers between them
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        display_tiktok_post(row)
        # Add a divider only if it's not the last post
        if i < len(filtered_df) - 1:
            st.divider()

    # Add footer
    st.markdown("---")
    st.markdown(
        "Built with Streamlit • Data collected using tiktok_scraper.py and download_media.py"
    )


if __name__ == "__main__":
    main()
