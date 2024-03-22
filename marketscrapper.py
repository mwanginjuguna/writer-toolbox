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
        print("Page downloaded!")
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
    if 'note-bank' in question_url:
        print("skipping note-bank.")
        return None
    # get data from question url and parse it into html using soup
    question_html = requests.get(question_url)
    question_soup = BeautifulSoup(question_html.content, 'html.parser')
    print(f"processing question: {question_url}")

    question_title = ''
    body = ''
    attachments = []
    attachment_file = ''
    attachment_content = ''
    category = ''
    tags = []

    # Get content from any attachments
    try:
        # returns the number of attached files
        attached_files_number=question_soup.find('div', class_="css-503bni").text.strip()[-2]
        attached_filenames_container = question_soup.find_all('li', class_="css-1ap3j0h")
        # find out whether specific filenames exist
        for attached_file in attached_filenames_container:
            attachments.append(attached_file.text)
            # get the content for this file
            attachment_content_containers = question_soup.find('div', class_="css-xss17j").findChildren(recursive=False)[1:]

            for attachment_filename, attachment_content_div in attachment_content_containers:
                if 'nstruction' in attachment_filename.text or 'ssignment' in attachment_filename.text or 'eek' in attachment_filename.text or 'wk' in attachment_filename.text or 'odule' in attachment_filename.text or 'ideline' in attachment_filename.text or 'inal' in attachment_filename.text or 'aper' in attachment_filename.text:
                    attachment_file = attachment_filename.text
                    attachment_content = attachment_content_div.text.strip()

        attachment_links = question_soup.find_all('li', class_="css-1960nst")

        for attachment_link in attachment_links:
            attachments.append(attachment_link.text)

    except AttributeError:
        attachment_content = ''


    # get title for each question
    try:
        question_title = question_soup.find('h1').text

        if 'response for' in question_title:
            return None

    except AttributeError:
        question_title = "Custom Solution - Writing Help by experts"

    # Get question text/description
    try:
        body = question_soup.find('div', class_="css-1lys3v9").text

        # ensure each question has more than x words of content
        if (len(body) - int(len(body.replace(" ", ""))) + 1 < 40) and len(attachment_content.replace(" ", "")) < 10:
            return None
    except AttributeError:
        return None

    # get question category/discipline
    try:
        categories = question_soup.find_all('a', class_="css-1al3bwk")
        category = categories[-1].text.replace('>', '').replace(' homework help', '').strip()
    except AttributeError:
        category = "Others"

    # get question tags or subcategory
    try:
        tagy = question_soup.find_all('a', class_="css-1xtj9tu")
        for tag in tagy:
            tags.append(tag.text.capitalize())
        if len(tags) == 0:
            tags = ['Solution']
    except AttributeError:
        tags = "Solutions"

    if len(question_title.replace(' ', '')) < 25:
        question_title = f"{question_title}: " + body[0:30].replace('\n', ' ') + f" | {category}"

    # get question data i.e. title, body, category, field, and 1 or more tags
    attachments_to_string = '|'.join(attachments)
    tags_to_string = '|'.join(tags)
    question_data = [question_title, body, attachments_to_string, attachment_file, attachment_content, category, tags_to_string, question_url]

    print(f"{len(question_data)} columns in question.")

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

    print("\nQuestions saved in format:"
          "\n'['title', 'body', 'attachments', 'attachment_file', "
          "'attachment_content', 'category', 'tags', 'question_url']'")
