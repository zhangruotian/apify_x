# Twitter Scraper using Apify

This project uses the Apify Twitter Scraper actor to collect tweets based on keywords. It uses a streamlined approach to collect and analyze tweet data:

1. **Data Collection & Conversion**: `twitter_scraper.py` extracts tweets using the Apify API, saves them in JSONL format, and automatically converts them to CSV with dedicated columns for media items
2. **Media Analysis**: `check_media.py` and `check_videos.py` analyze the collected tweets for photos and videos
3. **Media Download**: `download_media.py` downloads all photos and videos from tweets and adds columns with local file paths
4. **Tweet Viewer**: `tweet_viewer.py` is a Streamlit app that displays tweets with their text, images, videos, and metadata

## Setup

1. Make sure you have Python 3.11.10 installed (this project uses pyenv for Python version management)
2. Create and activate the virtual environment:

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a free Apify account if you don't have one:
   - Sign up at [apify.com](https://apify.com)
   - Get your API token from [console.apify.com/account/integrations](https://console.apify.com/account/integrations)

5. Update the `.env` file with your Apify API token:

```
APIFY_API_TOKEN=your_actual_token_here
```

## Usage: Streamlined Process

Just run the main script with your desired parameters:

```bash
python twitter_scraper.py
```

Edit the parameters directly in the `__main__` section of `twitter_scraper.py`:
```python
# Configure these parameters directly
query = "hurricane debby"  # Your search query
max_tweets = 100  # Maximum number of tweets to retrieve
sort_by = "Top"  # Options: "Top" or "Latest"
convert_to_csv = True  # Whether to also convert the JSONL to CSV
```

This single script will:
1. Collect tweets matching your query
2. Save them to a JSONL file
3. Automatically convert to CSV with dedicated media columns
4. Report the paths to both output files

## Media Analysis

After collecting tweets, you can analyze the media content:

```bash
# Check all media content (photos and videos)
python check_media.py

# Detailed analysis of video content
python check_videos.py
```

Both scripts will automatically use the most recent CSV file created.

## Media Download

To download all photos and videos from tweets:

```bash
python download_media.py
```

This script will:
1. Read the most recent CSV file (or you can specify one)
2. Download all photos and videos to the `media/photos` and `media/videos` directories
3. Create a new CSV file with additional columns for local file paths
4. Provide a summary of downloaded media

The output CSV will have additional columns like `photo1_local_path` and `video1_local_path` that contain the paths to the downloaded files.

## Interactive Tweet Viewer

To visualize your tweets with a user-friendly interface:

```bash
streamlit run tweet_viewer.py
```

This will launch a web app with the following features:
1. Interactive display of tweets with photos and videos
2. Filtering options by media type, hashtag, and username
3. Sorting by date, likes, retweets, or replies
4. Adjustable number of tweets to display

The viewer automatically finds the most recent CSV file with local paths, or you can specify a specific file.

## Why This Approach?

This project uses a streamlined approach for several reasons:

1. **Data Integrity**: The JSONL format preserves the complete nested structure of Twitter data
2. **Simplified Usage**: Just run one script to collect and prepare data for analysis
3. **Media-Focused Analysis**: Dedicated tools to examine photo and video content
4. **Clean CSV Structure**: Media items get their own dedicated columns for easy analysis
5. **Local Media Access**: Download and store media files locally for offline analysis

## Understanding the Data Formats

### JSONL Format

JSONL (JSON Lines) preserves the original structure of tweet data:

- Complete nested structure intact
- All arrays and objects preserved
- One JSON object per line for easy parsing
- All Twitter fields included as-is from the API

### CSV Format with Dedicated Columns

The extraction process creates a CSV with dedicated columns for all items:

- Media items get their own columns (photo1-photo9, video1-video5)
- Hashtags, URLs and mentions each have dedicated columns
- No semicolons or complex parsing needed - each item has its own column
- Perfect for spreadsheet applications and data analysis tools

## Script Details

### twitter_scraper.py

The Twitter scraper uses the Apify API to collect tweets matching your search query:

- **Actor ID**: `ghSpYIW3L1RvT57NT`
- **Parameters**:
  - `query`: Search query (e.g., "hurricane debby")
  - `max_tweets`: Maximum number of tweets to retrieve
  - `sort_by`: Either "Top" (relevance) or "Latest" (chronological)
  - `convert_to_csv`: Whether to automatically convert to CSV

### extract_tweet_data.py

Converts JSONL tweet data to CSV with dedicated columns:

- **Input**: JSONL file from `twitter_scraper.py`
- **Output**: CSV file with dedicated columns for all items
- **Features**:
  - Each photo gets its own column (photo1-photo9)
  - Each video gets its own column (video1-video5)
  - Each hashtag gets its own column (hashtag1-hashtag10)
  - Each URL and mention gets its own column

### check_media.py and check_videos.py

Analyze media content in your collected tweets:

- Statistics on photos and videos
- Identifies tweets with multiple media types
- Lists tweets with the most media items
- Detailed analysis of video formats and resolutions

### download_media.py

Downloads all media files from tweets and creates a new CSV with local paths:

- **Input**: CSV file from `extract_tweet_data.py`
- **Output**: 
  - Media files in `media/photos` and `media/videos` directories
  - New CSV file with additional columns for local file paths
- **Features**:
  - Creates unique filenames based on tweet ID and user name
  - Handles both photos and videos with appropriate timeouts
  - Adds columns with local file paths (e.g., `photo1_local_path`)
  - Provides detailed summary of downloaded media

### tweet_viewer.py

Provides an interactive web interface for viewing tweets:

- **Input**: CSV file with local paths from `download_media.py`
- **Features**:
  - Beautiful tweet display with original styling
  - Photo and video display from local files
  - Filtering by media type, hashtag, or username
  - Sorting by various engagement metrics
  - Responsive layout for different screen sizes

## Working with the JSONL Data

If you want to directly work with the original JSONL data:

```python
# Example: Read the JSONL file in Python
import json

tweets = []
with open('tweets_20240807_123456.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        tweets.append(json.loads(line))

# Now you can work with the complete tweet objects
for tweet in tweets:
    print(tweet['text'])
    
    # Access nested data naturally
    if 'media' in tweet and 'video' in tweet['media']:
        for video in tweet['media']['video']:
            for variant in video.get('variants', []):
                print(f"Video variant: {variant['url']}")
```

## Working with the Downloaded Media

You can use the CSV file with local paths to access the downloaded media:

```python
# Example: Using the CSV file with local media paths
import csv
from PIL import Image  # pip install pillow

# Read the CSV file with local paths
with open('tweets_with_local_paths.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Process photos
        for i in range(1, 10):  # photo1 through photo9
            photo_path = row.get(f'photo{i}_local_path', '')
            if photo_path:
                try:
                    # Open and process the image
                    img = Image.open(photo_path)
                    print(f"Photo dimensions: {img.width}x{img.height}")
                except Exception as e:
                    print(f"Error processing {photo_path}: {e}")
```

## Notes

- Twitter has rate limits that may affect the scraping process
- Using Apify's proxies (available on paid plans) can help avoid IP blocks
- Be sure to comply with Twitter's Terms of Service when using scraped data
- Some media URLs may expire or become unavailable, which is why local downloading is useful 