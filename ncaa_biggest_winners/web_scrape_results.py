import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_event_name(url):
    # Step 1: Fetch the web page
    response = requests.get(url)
    html_content = response.text

    # Step 2: Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    li_tag = soup.find("li", class_="breadcrumb-item active")

    if li_tag:
        text_content = li_tag.get_text().strip()
        return text_content
    else:
        print("No <li> tag with class 'breadcrumb-item active' found.")
        return None


def scrape_results(url):
    # Step 1: Fetch the web page
    response = requests.get(url)
    html_content = response.text

    # Step 2: Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Step 3: Find the table
    # You can find the table by looking for the <table> tag, or by its id or class if it's specified
    table = soup.find("table", {"id": "events"})
    if table is None:
        table = soup.find("table", {"id": "multitotalscores"})

    # Step 4: Extract rows and columns
    rows = table.find_all("tr")

    # Extract headers
    headers = [header.text.strip() for header in rows[0].find_all("th")]

    # Extract data rows
    data = []
    for row in rows[1:]:
        columns = row.find_all("td")
        data.append([column.text.strip() for column in columns])

    # Step 5: Convert to DataFrame
    df = pd.DataFrame(data, columns=headers)

    return df.drop(columns=[""])
