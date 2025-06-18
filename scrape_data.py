import requests
import json
import os
from datetime import datetime
from github import Github

# Configuration
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in"
GITHUB_REPO = "sanand0/tools-in-data-science-public"
DATA_FILE = "tds_data.json"

# Environment variables
DISCOURSE_COOKIES = {
    '_t': os.environ.get('DISCOURSE_T_COOKIE'),
    '_forum_session': os.environ.get('DISCOURSE_SESSION_COOKIE')
}
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Create authenticated Discourse session
def create_discourse_session():
    session = requests.Session()
    for name, value in DISCOURSE_COOKIES.items():
        if value:
            session.cookies.set(name, value, domain=DISCOURSE_URL.split('//')[1])
        else:
            raise ValueError(f"Missing cookie: {name}")
    return session

# Scrape Discourse posts
def scrape_discourse_posts(start_date, end_date):
    session = create_discourse_session()
    topics_data = []
    
    # Verify authentication
    response = session.get(f"{DISCOURSE_URL}/session/current.json")
    if response.status_code != 200:
        raise Exception(f"Discourse authentication failed: Status {response.status_code}, Response: {response.text}")
    
    # Fetch topics from Tools in Data Science category (assumed ID 20)
    page = 1
    while True:
        response = session.get(f"{DISCOURSE_URL}/c/courses/tds-kb/34.json?page={page}")
        if response.status_code != 200:
            print(f"Failed to fetch topics page {page}: {response.text}")
            break
        data = response.json()
        topics = data.get('topic_list', {}).get('topics', [])
        if not topics:
            break
            
        for topic in topics:
            created_at = datetime.strptime(topic['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if start_date <= created_at <= end_date:
                topic_id = topic['id']
                topic_response = session.get(f"{DISCOURSE_URL}/t/{topic_id}.json")
                if topic_response.status_code == 200:
                    topic_data = topic_response.json()
                    posts = topic_data.get('post_stream', {}).get('posts', [])
                    for post in posts:
                        topics_data.append({
                            'topic_id': topic_id,
                            'title': topic['title'],
                            'post_id': post['id'],
                            'content': post['cooked'],
                            'created_at': post['created_at'],
                            'url': f"{DISCOURSE_URL}/t/{topic_id}/{post['post_number']}"
                        })
                else:
                    print(f"Failed to fetch topic {topic_id}: {topic_response.text}")
        page += 1
    
    return topics_data

# Scrape GitHub repository content
def scrape_github_content():
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not set")
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    contents = repo.get_contents("")
    github_data = []
    
    def process_content(content, path=""):
        if content.type == "dir":
            for subcontent in repo.get_contents(content.path):
                process_content(subcontent, f"{path}/{subcontent.name}")
        else:
            if content.name.endswith(('.md', '.ipynb', '.py')):
                try:
                    github_data.append({
                        'path': f"{path}/{content.name}",
                        'content': content.decoded_content.decode('utf-8')
                    })
                except Exception as e:
                    print(f"Error processing {path}/{content.name}: {e}")
    
    for content in contents:
        process_content(content)
    
    return github_data

# Save scraped data to JSON
def save_scraped_data():
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 4, 14)
    
    try:
        print("Scraping Discourse posts...")
        discourse_data = scrape_discourse_posts(start_date, end_date)
        print(f"Retrieved {len(discourse_data)} Discourse posts")
    except Exception as e:
        print(f"Error scraping Discourse: {e}")
        discourse_data = []
    
    try:
        print("Scraping GitHub content...")
        github_data = scrape_github_content()
        print(f"Retrieved {len(github_data)} GitHub files")
    except Exception as e:
        print(f"Error scraping GitHub: {e}")
        github_data = []
    
    combined_data = {
        'discourse': discourse_data,
        'github': github_data
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Data saved to {DATA_FILE}")
    return combined_data

# Test authentication
def test_discourse_auth():
    try:
        session = create_discourse_session()
        response = session.get(f"{DISCOURSE_URL}/session/current.json")
        if response.status_code == 200:
            user_data = response.json()
            print(f"Authenticated as: {user_data['current_user']['username']}")
        else:
            print(f"Authentication failed: Status {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Authentication test failed: {e}")

if __name__ == "__main__":
    print("Testing Discourse authentication...")
    test_discourse_auth()
    print("\nRunning data scraping...")
    save_scraped_data()
