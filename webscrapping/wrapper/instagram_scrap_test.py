import asyncio
import json
from typing import List
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import time


def get_instagram_followers_count(username: str, session: requests.Session) -> int:
    """
    Get the number of followers of a given Instagram profile.
    :param username: The profile name.
    :param session: The session to use.
    :return: The number of followers.
    """
    try:
        raw_url = "https://www.instagram.com/"
        profile_url = raw_url + username
        resp = session.get(profile_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        script = soup.find('script', text=lambda t: t.startswith('window._sharedData'))
        page_json = script.string.split(' = ', 1)[1].rstrip(';')
        data = json.loads(page_json)
        return int(data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count'])
    except Exception as e:
        print(e)
        return 0


async def get_followers_async(profile_list: List[str]) -> List[int]:
    res = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.session() as session:
            internal_loop = asyncio.get_event_loop()
            tasks = [
                internal_loop.run_in_executor(executor, get_instagram_followers_count,
                                              *(profile, session)) for profile in profile_list
            ]
            print("Tasks instantiated!")
            for response in await asyncio.gather(*tasks):
                print("Appending {}".format(response))
                res.append(response)
            return res

if __name__ == "main":
    profiles = ['gabrielfreiredev', 'freire.tatyana', 'saranobre', 'daralmeida', 'babisp']
    start = time.time()
    for p in profiles:
        count = get_instagram_followers_count(p, requests)
        print(f'{p} has {count} followers')
    end = time.time()
    elapsed = end - start
    print(f'SYNC elapsed time: {elapsed} seconds')

    start = time.time()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(get_followers_async(profiles))
    r = loop.run_until_complete(future)
    end = time.time()
    print(r)
    elapsed = end - start
    print(f'ASYNC Elapsed time: {elapsed} seconds')

