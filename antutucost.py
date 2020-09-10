import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def parse(token):
    antutu_url = 'https://www.antutu.com/en/ranking/rank1.htm'

    collection = []
    session = get_session(token)
    r = session.get(antutu_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    r.close()

    rows = soup(class_='nrank-b')

    for row in tqdm(rows, desc='Parsing...'):
        phone = row.find(class_='bfirst').find('span').next_sibling

        # Samsung phones are listed with the Exynos processor model #
        # Ebay often doesn't have this model
        # Assume the Exynos and the Snapdragon model have similar performance
        # Even though in reality the Exynos performs worse :(

        if '(' in phone:
            phone = phone[:phone.index('(')]

        score = int(row.find(class_='blast').string)

        price = float(ebay_search(phone, session))

        if price:
            value = score / price
        else:
            value = 0

        collection.append({'phone': phone, 'price': price, 'value': value})

    collection = sorted(collection, key=lambda x: x['value'], reverse=True)
    pd.DataFrame(data=collection).to_csv('results.csv', index=False)


def ebay_search(query, session):
    """Return first price queried from Ebay search API"""
    # category_id 9355 is for Cell Phones & Smartphones
    # avoid getting phone cases in our search
    r = session.get(f'https://api.ebay.com/buy/browse/v1/item_summary/search?'
                    f'q={query.replace(" ", ",")}&'
                    f'category_ids=9355&limit=1&'
                    f'filter=buyingOptions:{{FIXED_PRICE}},conditions:{{NEW}}')
    r.raise_for_status()
    data = r.json()

    # no search results
    if not data['total']:
        return 0

    price = data['itemSummaries'][0]['price']['value']
    r.close()
    return price


def get_session(token):
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {token}'})
    return session


def get_token():
    """Gets token from user input and validates"""
    test_url = 'https://api.ebay.com/buy/browse/v1/item_summary/search?q=kanye'
    status = 401

    while status == 401:
        token = input('Paste Ebay User Token:')
        with get_session(token) as session:
            status = session.get(test_url).status_code

    return token


if __name__ == '__main__':
    parse(get_token())
