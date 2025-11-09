# Social Media Flood Datasets

This document lists the available datasets for flood-related social media analysis from TikTok and Twitter platforms.

## 📱 TikTok Video Datasets

### Individual Datasets
| Dataset            | Records | Videos | CSV Path                                                                                             | Video Directory                      |
|--------------------|---------|--------|------------------------------------------------------------------------------------------------------|--------------------------------------|
| Bangladesh Flood   | 385     | 385    | `tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv`                                | `tiktok/bangladesh_flood/videos`     |
| Assam Flood        | 58      | 58     | `tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv`         | `tiktok/assam_flood/videos`          |
| Kerala Flood       | 41      | 41     | `tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv`       | `tiktok/kerala_flood/videos`         |
| Pakistan Flood     | 45      | 45     | `tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv`   | `tiktok/pakistan_flood/videos`       |
| South Asia Flood   | 574     | 574    | `tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv`                 | `tiktok/south_asia_flood/videos`     |

**Total Videos Available**: 1,103 video files across all events

### 🌊 Combined TikTok Dataset
| Dataset                    | Records | Videos |                            
|----------------------------|---------|--------|
| **All TikTok Floods** | **1,103** | **1,103** |

## 🐦 Twitter Tweet Datasets

### 🧹 Cleaned Datasets (AI-Filtered)
| Dataset            | Records | Photos | Videos | CSV Path                                                      | Media Directory                      |
|--------------------|---------|--------|--------|---------------------------------------------------------------|--------------------------------------|
| Assam Flood        | 311     | 195    | 73     | `twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv`     | `twitter/assam_flood/media_cleaned`  |
| Bangladesh Flood   | 952     | 911    | 144    | `twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv` | `twitter/bangladesh_flood/media_cleaned` |
| Kerala Flood       | 361     | 172    | 177    | `twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv`   | `twitter/kerala_flood/media_cleaned` |
| Pakistan Flood     | 237     | 168    | 62     | `twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv` | `twitter/pakistan_flood/media_cleaned` |

### 🌊 Combined Clean Dataset
| Dataset                    | Records | Photos | Videos |                            
|----------------------------|---------|--------|--------|
| **All Twitter Floods (Clean)** | **1,861** | **1,446** | **456** |  

**Total Media Files**: 1,902 media files (1,446 photos + 456 videos) across all events

## 📊 Combined Dataset

### 🌐 All Platforms Combined
| Dataset                    | Records | Source Breakdown |                            
|----------------------------|---------|------------------|
| **All Floods (TikTok + Twitter)** | **2,964** | TikTok: 1,103<br>Twitter: 1,861 |

**Combined CSV File**: `merged_all_flood_data.csv`
- Contains all records from both TikTok and Twitter datasets
- Includes `source` field (tiktok/twitter) and `region` field (assam/bangladesh/kerala/pakistan/south_asia)
- All analysis fields from `is_flood_related` onwards are preserved in original order
- Total columns: 194

### Regional Distribution
| Region       | Total Records | TikTok | Twitter |
|--------------|---------------|--------|---------|
| Bangladesh   | 1,337         | 385    | 952     |
| South Asia   | 574           | 574    | -       |
| Kerala       | 402           | 41     | 361     |
| Assam        | 369           | 58     | 311     |
| Pakistan     | 282           | 45     | 237     |
