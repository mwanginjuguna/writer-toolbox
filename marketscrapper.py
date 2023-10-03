from bs4 import BeautifulSoup
import requests
from csv import writer
import json


def link_builder():
    links = []
    # collect user input to build links
    starter = int(input('Starting Date: '))
    stopper = int(input('Last Date: '))
    month = input('Month: ')
    year = int(input('Year: '))
    for day in range(starter, (stopper + 1)):
        lnk = f"https://www.sweetstudy.com/archive/{year}/{month}/{day}"
        links.append(lnk)
    print(f"({len(links)}) links: {links}. Make sure you call manual links to save the links to file.")
    # dates = f"Previous Start Date: {starter} & Previous stop Date: {stopper}"
    return links


def manual_links(links: list):
    # save all links to a JSON - Just in case the scrapping is terminated in the process, we can resume from a
    # specific date
    json_links = {
        'link_list': links,
    }

    json_object = json.dumps(json_links, indent=4)

    # write to JSON file
    with open("links/links.json", "w") as json_file:
        json_file.write(json_object)

    return f"{len(links)} Links saved on links.json file"


def link_getter():
    links = []
    try:
        with open("links/links.json", "r") as json_file:
            json_object = json.load(json_file)
            for x in json_object["link_list"]:
                links.append(x)
        print(f'found links: {len(links)}')
    except FileNotFoundError:
        print("No links file")
    return links


def page_scrapper(page_url):
    """This function takes a page url and returns all sub-urls to individual questions on a page."""
    question_links = []
    try:
        # Connect to server and download the page
        page_results = requests.get(page_url)
        # get url extension for each question from all the 'containers' parses received html response from
        # server into a soup data structure to traverse html as if it were a json data type.
        page_soup = BeautifulSoup(page_results.content, "html.parser")

        # get all html objects containing the link question
        question_containers = page_soup.find_all("li", class_="css-qq6fb7")

        for container in question_containers:
            question_link_extension = container.a["href"]

            # create a new question url
            question_url = f"https://www.sweetstudy.com{question_link_extension}"
            question_links.append(question_url)
    except ConnectionError:
        print("There was a connection error. Check internet-connection and try again.")

    return question_links


# scrape individual questions
def question_scrapper(question_url: str):
    # get data from question url and parse it into html using soup
    question_html = requests.get(question_url)
    question_soup = BeautifulSoup(question_html.content, 'html.parser')

    # get title for each question
    try:
        question_title = question_soup.find('h1').text
    except AttributeError:
        question_title = "Gateway Assignment - Custom writing services by experts"

    # Get question text/description
    try:
        body = question_soup.find('div', class_="css-1lys3v9").text

        # ensure each question has more than x words of content
        if len(body) - int(len(body.replace(" ", ""))) + 1 < 40:
            return None
    except AttributeError:
        return None
    # get question category/discipline
    try:
        categories = question_soup.find_all('a', class_="css-1al3bwk")
        category = categories[1].text.replace('>', '').replace(' homework help', '')
        field = categories[-1].text.replace('>', '').replace(' homework help', '')
    except AttributeError:
        category = "Others"
        field = "Others"

    # get question tags or subcategory
    try:
        tags = []
        tagy = question_soup.find_all('a', class_="css-1xtj9tu")
        for tag in tagy:
            tags.append(tag.text)
    except AttributeError:
        tags = "Original Solutions"

    # get question data i.e. title, body, category, field, and 1 or more tags
    question_data = [question_title, body, category, field]
    question_data += tags

    return question_data


def save_question_to_csv(question_data):
    csv_file_name = f'raw/h_market_latest.csv'
    with open(csv_file_name, 'a', encoding='utf-8', newline='') as q_file:
        # use csv writer function to write to file
        the_writer = writer(q_file)
        print("Saving question to file...")
        # write question data to csv as a row
        the_writer.writerow(question_data)
    return print("Saved to file...")


# on startup
def scrape(links):
    print(f"{len(links)} links ready for scrapping.")
    # notify first and last links in the list
    print(f"scrapping the following links: \n Starting link: {links[0]}\nLast Link on list: {links[-1]}")
    counter = 0
    # now that we have all links we need, next is to start scrapping
    # Url to scrape from
    for page_url in links:
        counter += 1
        print(f"Currently scrapping {page_url}...")
        try:
            # get urls
            question_urls = page_scrapper(page_url=page_url)
            for question_link in question_urls:
                # get question data
                q_data = question_scrapper(question_url=question_link)
                # save question data to csv file
                if q_data is not None:
                    save_question_to_csv(question_data=q_data)
            print(f"Finished scrapping link{counter}\n({page_url}).\nRemoving it from list...")
            links.remove(page_url)
            # update the links in links.json
            manual_links(links=links)
        except ConnectionError:
            # update links.json in case of an error
            manual_links(links=links)
            print('A connection problem was encountered. Try again')
    manual_links(links=links)
    return print("Done scrapping...")


if __name__ == "__main__":
    # manual_links(links=link_builder())
    # read files already in links.json file
    links = link_getter()
    if len(links) == 0:
        print("No Links in json file. Let's change that by setting dates for scrapping...")
        manual_links(links=link_builder())
    links = link_getter()
    # scrape as long as there are links in the links.json
    while len(links) > 0:
        scrape(links)
