# Twitter Scraper using Apify

This project uses the Apify Twitter Scraper actor to collect tweets based on keywords. It uses a streamlined approach to collect and analyze tweet data:

1. **Data Collection & Conversion**: `twitter_scraper.py` extracts tweets using the Apify API, saves them in JSONL format, and automatically converts them to CSV with dedicated columns for media items
2. **Media Analysis**: `check_media.py` and `check_videos.py` analyze the collected tweets for photos and videos

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

## Why This Approach?

This project uses a streamlined approach for several reasons:

1. **Data Integrity**: The JSONL format preserves the complete nested structure of Twitter data
2. **Simplified Usage**: Just run one script to collect and prepare data for analysis
3. **Media-Focused Analysis**: Dedicated tools to examine photo and video content
4. **Clean CSV Structure**: Media items get their own dedicated columns for easy analysis

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

## Notes

- Twitter has rate limits that may affect the scraping process
- Using Apify's proxies (available on paid plans) can help avoid IP blocks
- Be sure to comply with Twitter's Terms of Service when using scraped data 