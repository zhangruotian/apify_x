#!/usr/bin/env python3
"""
TikTok Viewer - A Streamlit app to display TikTok posts with their videos and metadata.
This app reads the CSV file created by tiktok_scraper.py and extract_tiktok_data.py.
"""

import os

import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="TikTok Viewer",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define dataset paths relative to the project root
DATASETS = {
    "🌊 All Floods Combined": {
        "csv_path": "tiktok/combined_all_floods.csv",
        "video_dir": "combined",  # Special handling needed for combined dataset
    },
    "Bangladesh Flood": {
        "csv_path": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv",
        "video_dir": "tiktok/bangladesh_flood/videos",
    },
    "Assam Flood": {
        "csv_path": "tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv",
        "video_dir": "tiktok/assam_flood/videos",
    },
    "Kerala Flood": {
        "csv_path": "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv",
        "video_dir": "tiktok/kerala_flood/videos",
    },
    "Pakistan Flood": {
        "csv_path": "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv",
        "video_dir": "tiktok/pakistan_flood/videos",
    },
    "South Asia Flood": {
        "csv_path": "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv",
        "video_dir": "tiktok/south_asia_flood/videos",
    },
}

# Add CSS for better styling
st.markdown(
    """
    <style>
    .tiktok-container {
        border: 2px solid #25F4EE;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #fafafa;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-shadow: 0 4px 12px rgba(37, 244, 238, 0.2);
    }
    .tiktok-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        text-align: center;
        color: #333;
        line-height: 1.4;
    }
    .hashtag {
        color: #25F4EE;
        font-weight: 500;
    }
    /* Center and fix width for videos - smaller size */
    .stVideo {
        display: flex !important;
        justify-content: center !important;
    }
    .stVideo > div {
        max-width: 300px !important;
        max-height: 400px !important;
        margin: 0 auto !important;
    }
    .stVideo video {
        max-width: 300px !important;
        max-height: 400px !important;
        object-fit: contain !important;
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


    </style>
    """,
    unsafe_allow_html=True,
)


def get_video_path(post_id, video_dir, row=None):
    """Get the local path to a video file based on its ID."""
    # Handle combined dataset with distributed videos
    if video_dir == "combined" and row is not None:
        # Use the video_local_path from the CSV if available
        if "video_local_path" in row and pd.notna(row["video_local_path"]):
            video_path = row["video_local_path"]
            if os.path.exists(video_path):
                return video_path

        # # Fallback: try to find the video in all possible directories
        # possible_dirs = [
        #     "tiktok/bangladesh_flood/videos",
        #     "tiktok/assam_flood/videos",
        #     "tiktok/kerala_flood/videos",
        #     "tiktok/pakistan_flood/videos",
        #     "tiktok/south_asia_flood/videos",
        # ]

        # for dir_path in possible_dirs:
        #     video_path = os.path.join(dir_path, f"tiktok_{post_id}.mp4")
        #     if os.path.exists(video_path):
        #         return video_path

        return None

    # Standard handling for individual datasets
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


def display_tiktok_post(row, video_dir):
    """Display a simplified TikTok post with only text, video, and hashtags."""
    # Extract only the essential data
    post_id = row.get("id", "Unknown")
    title = row.get("title", "")
    hashtags = row.get("hashtags", "")
    event = row.get("event", "")

    # Get local video path
    video_path = get_video_path(post_id, video_dir, row)

    # Start the container for the entire post
    with st.container():
        # Open the frame div
        st.markdown(
            """
            <div class="tiktok-container">
            """,
            unsafe_allow_html=True,
        )

        # Display event badge (if available) - small and subtle
        if event:
            st.markdown(
                f'<div style="margin-bottom: 15px; text-align: center;"><small style="background-color: #25F4EE; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">📍 {event}</small></div>',
                unsafe_allow_html=True,
            )

        # Display title text
        if title:
            st.markdown(
                f'<div class="tiktok-title">{title}</div>',
                unsafe_allow_html=True,
            )

        # Display video if available - small and consistent size
        if video_path:
            try:
                video_file = open(video_path, "rb")
                video_bytes = video_file.read()
                # Center the video with fixed small size
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    # Use a container to control video size
                    st.markdown(
                        '<div style="max-width: 300px; margin: 0 auto;">',
                        unsafe_allow_html=True,
                    )
                    st.video(video_bytes, start_time=0)
                    st.markdown("</div>", unsafe_allow_html=True)
                video_file.close()
            except Exception as e:
                st.error(f"Error displaying video: {e}")
        else:
            st.markdown(
                '<div style="padding: 20px; background-color: #f0f0f0; border-radius: 10px; color: #666; text-align: center; margin: 15px auto; max-width: 300px;">📹 Video not available</div>',
                unsafe_allow_html=True,
            )

        # Display hashtags
        if hashtags and isinstance(hashtags, str):
            hashtag_list = hashtags.split(",")
            hashtag_html = " ".join(
                [
                    f'<span style="color: #25F4EE; font-weight: 500;">#{tag.strip()}</span>'
                    for tag in hashtag_list
                    if tag.strip()
                ]
            )
            st.markdown(
                f'<div style="margin-top: 15px; text-align: center; font-size: 14px; line-height: 1.4;">{hashtag_html}</div>',
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
    video_dir = ""
    df = None
    sort_by = "Most views"
    num_posts = 10

    # Sidebar for file selection and filters
    with st.sidebar:
        st.header("Settings")

        # Dataset selection
        selected_dataset = st.selectbox(
            "Select a dataset to view:", list(DATASETS.keys())
        )

        if selected_dataset:
            dataset_info = DATASETS[selected_dataset]
            csv_file = dataset_info["csv_path"]
            video_dir = dataset_info["video_dir"]

        if not csv_file:
            st.error("Please select a dataset.")
            return

        st.info(f"Dataset: {selected_dataset}")

        if not os.path.exists(csv_file):
            st.error(f"CSV file not found: {csv_file}")
            return

        # Load the data
        try:
            df = pd.read_csv(csv_file)
            st.info(f"Loaded {len(df)} TikTok posts")

            # Display options
            st.subheader("Display Options")

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

    # Start with full dataset (no filters)
    filtered_df = df.copy()

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

    # Display each post with clear separation
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        display_tiktok_post(row, video_dir)
        # Add divider between posts
        if i < len(filtered_df) - 1:
            st.markdown("---")

    # Add footer
    st.markdown("---")
    st.markdown(
        "Built with Streamlit • Data collected using tiktok_scraper.py and download_media.py"
    )


if __name__ == "__main__":
    main()
