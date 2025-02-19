#sample code
import asyncio
import os
from dotenv import load_dotenv
from scrapper import TwitterScraper
from search import SearchMode

async def test_search_tweets(scraper):
    """
    Test the search functionality with different modes.
    
    Args:
        scraper: Configured TwitterScraper instance
    """
    print("Login successful! 🎉")
    try:
        # Test different search modes
        search_tests = [
            ("from:@the_great_svg", SearchMode.LATEST, 1),
            # ("news", SearchMode.TOP, 3),
            # ("nature photography", SearchMode.PHOTOS, 3),
            # ("music video", SearchMode.VIDEOS, 3),
            # ("elon musk", SearchMode.USERS, 3)
        ]
        
        for query, mode, max_items in search_tests:
            print(f"\n🔍 Testing {mode.value} search with query: '{query}'...")
            
            tweets = await scraper.search_tweets(query, mode, max_items)
            
            if tweets:
                print(f"Found {len(tweets)} results:")
                for tweet in tweets:
                    print("\n-------------------")
                    print(f"Tweet by @{tweet['user']['screen_name']} ({tweet['user']['name']})")
                    print(f"Text: {tweet['text'][:100]}...")
                    print(f"Created at: {tweet['created_at']}")
                    print(f"Likes: {tweet['favorite_count']}")
                    print(f"Retweets: {tweet['retweet_count']}")
                    if tweet.get('views'):
                        print(f"Views: {tweet['views']}")
            else:
                print("No results found.")
            
    except Exception as e:
        print(f"Search failed: {str(e)}")
        raise

async def main():
    # Load environment variables
    load_dotenv()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")
    email = os.getenv("TWITTER_EMAIL")

    if not all([bearer_token, username, password, email]):
        print("Please set TWITTER_BEARER_TOKEN, TWITTER_USERNAME, TWITTER_PASSWORD, and TWITTER_EMAIL environment variables.")
        return

    # Initialize scraper
    scraper = TwitterScraper(bearer_token)
    
    try:
        print("Attempting to log in...")
        await scraper.login(username, password, email)
        
        # Run search test
        await test_search_tweets(scraper)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if scraper.auth:
            await scraper.auth.close()

if __name__ == "__main__":
    asyncio.run(main())