# Social Media Flood Datasets

This document lists the available datasets for flood-related social media analysis from TikTok and Twitter platforms.

## 📱 TikTok Video Datasets

### Individual Datasets
| Dataset            | Records | Videos | CSV Path                                                                                             | Video Directory                      |
|--------------------|---------|--------|------------------------------------------------------------------------------------------------------|--------------------------------------|
| Bangladesh Flood   | 340     | 340    | `tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv`                                | `tiktok/bangladesh_flood/videos`     |
| Assam Flood        | 62      | 62     | `tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv`         | `tiktok/assam_flood/videos`          |
| Kerala Flood       | 59      | 59     | `tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv`       | `tiktok/kerala_flood/videos`         |
| Pakistan Flood     | 48      | 48     | `tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv`   | `tiktok/pakistan_flood/videos`       |
| South Asia Flood   | 591     | 591    | `tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv`                 | `tiktok/south_asia_flood/videos`     |

### Combined Dataset
| Dataset                | Records | Unique Records | Duplicates Removed | CSV Path                            |
|------------------------|---------|----------------|-------------------|-------------------------------------|
| 🌊 All Floods Combined | 1,100   | 1,083          | 17                | `tiktok/combined_all_floods.csv`   |


**Total Videos Available**: 1083 video files across all events

## 🐦 Twitter Tweet Datasets

### 🧹 Cleaned Datasets (AI-Filtered)
| Dataset            | Records | Photos | Videos | CSV Path                                                      | Media Directory                      |
|--------------------|---------|--------|--------|---------------------------------------------------------------|--------------------------------------|
| Assam Flood        | 308     | 194    | 73     | `twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv`     | `twitter/assam_flood/media_cleaned`  |
| Bangladesh Flood   | 613     | 562    | 157    | `twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv` | `twitter/bangladesh_flood/media_cleaned` |
| Kerala Flood       | 421     | 188    | 209    | `twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv`   | `twitter/kerala_flood/media_cleaned` |
| Pakistan Flood     | 240     | 171    | 63     | `twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv` | `twitter/pakistan_flood/media_cleaned` |



### 🌊 Combined Clean Dataset
| Dataset                    | Records | Photos | Videos |                            
|----------------------------|---------|--------|--------|
| **All Twitter Floods (Clean)** | **1,582** | **1,115** | **502** |  

**Total Media Files**: 1,617 media files (1,115 photos + 502 videos) across all events


