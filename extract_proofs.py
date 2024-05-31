import os
import pickle
from tqdm import tqdm
from zimscan import Reader
from bs4 import BeautifulSoup
import re

# Compile useful regex
whitespace_r = re.compile(r"\s+")
definition_r = re.compile(r"Definition \d+")

def clean_text(value):
    value = whitespace_r.sub(" ", value)
    value = value.strip()
    return value

def extract_article_data(article_content):
    soup = BeautifulSoup(article_content, 'html.parser')
    article_data = []
    current_title = None
    current_content = []
    special_titles = ['Proof', 'Solution', 'Sources']

    # Extract all tags and their text content from the article
    for tag in soup.find_all(True):
        tag_name = tag.name
        tag_text = clean_text(tag.get_text())

        if tag_name == 'body':
            body_content = clean_text(tag.get_text())
            if body_content:
                current_content.append(body_content)

        if tag_name in ['h1', 'h2', 'h3'] or definition_r.match(tag_text):
            if current_title:
                article_data.append({
                    "title": current_title,
                    "content": current_content,
                    "type": "definition" if definition_r.match(current_title) else None
                })
            current_title = tag_text
            current_content = []
        elif tag_name == 'table':
            table_data = []
            for row in tag.find_all('tr'):
                row_data = [clean_text(cell.get_text()) for cell in row.find_all(['td', 'th'])]
                table_data.append(row_data)
            current_content.append(table_data)
        elif tag_text and tag_name not in ['span', 'meta', 'a', 'ul', 'li']:
            if tag_text in special_titles and current_title:
                article_data.append({
                    "title": current_title,
                    "content": current_content,
                    "type": tag_text.lower()
                })
                current_content = []
            else:
                current_content.append(tag_text)

    if current_title:
        article_data.append({
            "title": current_title,
            "content": current_content,
            "type": "solution" if "solution" in current_title.lower() else "proof" if "proof" in current_title.lower() else "sources" if "sources" in current_title.lower() else "definition" if definition_r.match(current_title) else None
        })

    return article_data

def parse_zim_file(file_path):
    articles = {}
    article_count = 0
    max_articles = 2000
    try:
        with open(file_path, 'rb') as f:
            with Reader(f, skip_metadata=True) as reader:
                for article in tqdm(reader):
                    if article_count >= max_articles:
                        break
                    try:
                        article_content = article.read()
                        article_data = extract_article_data(article_content)
                        for data in article_data:
                            title = data['title']
                            content = data['content']
                            if title in articles:
                                if isinstance(articles[title], list):
                                    articles[title].extend(content)
                                else:
                                    articles[title] = [articles[title]] + content
                            else:
                                articles[title] = content
                        article_count += 1
                    except Exception as e:
                        print(f"Error reading article: {e}")
                        continue
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return [{"title": title, "content": content, "type": None} for title, content in articles.items()]

# Define the ZIM file path and pickle file path
zim_file_path = '/Users/kelsey/Downloads/proofwiki_en_all_maxi_2024-05.zim'
pickle_file_path = 'proofwiki_data.pkl'

# Check if the pickle file exists
if os.path.exists(pickle_file_path):
    # Load the data from the pickle file
    with open(pickle_file_path, 'rb') as pickle_file:
        article_data = pickle.load(pickle_file)
else:
    # Parse the ZIM file and get all articles
    article_data = parse_zim_file(zim_file_path)
    # Save the data to a pickle file
    with open(pickle_file_path, 'wb') as pickle_file:
        pickle.dump(article_data, pickle_file)

# Print the structured data to the console
for article in article_data:
    print(article)
