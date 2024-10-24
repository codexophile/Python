from googleapiclient.discovery import build

# Your API Key
API_KEY = 'AIzaSyB41uuRwzZyKBJcMPr-kyNwXBpeOcESOpU'
video_id = 'iJkaAJUzeWQ'
region_code = 'US'  # Adjust for your region if needed

# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Get video details (including categoryId)
video_response = youtube.videos().list(
    part='snippet',
    id=video_id
).execute()

# Get the categoryId from the video response
if video_response['items']:
    category_id = video_response['items'][0]['snippet']['categoryId']

    # Get the category name using the videoCategories.list endpoint
    category_response = youtube.videoCategories().list(
        part='snippet',
        regionCode=region_code
    ).execute()

    # Find the category name matching the category_id
    for category in category_response['items']:
        if category['id'] == category_id:
            category_name = category['snippet']['title']
            print(f"Category Name: {category_name}")
            break
else:
    print("Video not found.")
