import os
import requests
from dotenv import load_dotenv
load_dotenv()

# Notion配置
NOTION_API_KEY = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')
NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28'
}

# Flomo配置
FLOMO_API_URL = f"https://flomoapp.com/iwh/OTM1MTU/{os.getenv('FLOMO_API')}/"
FLOMO_HEADERS = {'Content-Type': 'application/json'}

# 请求Notion数据库
def query_notion_database():
    response = requests.post(f'https://api.notion.com/v1/databases/{DATABASE_ID}/query', headers=NOTION_HEADERS)
    return response.json()

# 获取页面的子块
def get_page_children(page_id):
    response = requests.get(f'https://api.notion.com/v1/blocks/{page_id}/children', headers=NOTION_HEADERS)
    return response.json()

def extract_callouts(blocks, headers):
    callouts = []
    def get_children(block_id):
        # 获取特定块的子块
        children_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
        response = requests.get(children_url, headers=headers)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            return []

    def extract_text(block):
        # 从rich_text属性收集文本片段
        return ''.join(text['plain_text'] for text in block['rich_text']) if 'rich_text' in block else ''

    for block in blocks.get('results', []):
        if block['type'] == 'callout':
            # 提取callout块的文本
            callout_text = extract_text(block['callout'])
            # 如果callout块有子块，获取并处理这些子块
            if block['has_children']:
                children = get_children(block['id'])
                for child in children:
                    if child['type'] == 'quote':
                        callout_text += "\n> "
                        callout_text += extract_text(child['quote'])
            callouts.append(callout_text)
    return callouts


# 发送callout到Flomo
def send_to_flomo(book_name, content):
    data = {'content': content + '\n\n#回顾 #读书笔记/' + book_name}
    response = requests.post(FLOMO_API_URL, headers=FLOMO_HEADERS, json=data)
    return response.status_code, response.text
# 主函数
def main():
    database_data = query_notion_database()
    for page in database_data.get('results', []):
        page_id = page['id']
        book_name = page['properties']['BookName']['title'][0]['plain_text']
        print("book_name: ", book_name)
        book_id = int(page['properties']['BookId']['rich_text'][0]['plain_text'])

        saved_books = [33889243]
        if book_id in saved_books:
            continue
        children_data = get_page_children(page_id)
        callouts = extract_callouts(children_data, NOTION_HEADERS)
        
        for callout in callouts:
            status, response = send_to_flomo(book_name, callout)
            print(f'Status: {status}, Response: {response}')
            if response['code'] == -1:
                exit()

if __name__ == "__main__":
    main()