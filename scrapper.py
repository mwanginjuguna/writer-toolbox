from bs4 import BeautifulSoup
import requests
from csv import writer
import json


def link_builder():
    links = []
    while True:
        try:
            starter = int(input('Starting Date: '))
            stopper = int(input('Last Date: '))
            year = int(input('Year: '))
            month = input('Month: ')  # Consider validating month format as well (e.g., month name or number)
            break  # Exit loop if inputs are valid integers
        except ValueError:
            print("Invalid input. Please enter valid integers for dates and year.")

    if starter > stopper:
        print("Error: Starting date cannot be after the stopping date.")
        return []  # Return empty list if date range is invalid

    for day in range(starter, (stopper + 1)):
        lnk = f"https://www.sweetstudy.com/archive/{year}/{month}/{day}"
        links.append(lnk)
    print(f"({len(links)}) page links built: {links}. Call manual_links to save to links.json.")
    return links


def manual_links(links: list, filename="links/links.json"):  # Added filename parameter
    json_links = {
        'link_list': links,
    }
    json_object = json.dumps(json_links, indent=4)

    try:
        with open(filename, "w") as json_file:  # Use filename parameter
            json_file.write(json_object)
        return f"{len(links)} Links saved on {filename} file"  # Updated message
    except IOError as e:
        return f"Error saving links to {filename} file: {e}"  # Updated message


def link_getter(filename="links/links.json"):  # Added filename parameter
    links = []
    try:
        with open(filename, "r") as json_file:  # Use filename parameter
            json_object = json.load(json_file)
            for x in json_object["link_list"]:
                links.append(x)
        print(f'found links in {filename}: {len(links)}')  # Updated message
    except FileNotFoundError:
        print(f"No {filename} file found.")  # Updated message
    except IOError as e:  # Catch other potential file reading errors
        print(f"Error reading {filename} file: {e}")  # Updated message
    return links


def page_scrapper(page_url):
    question_links = []
    try:
        page_results = requests.get(page_url)
        print("Page downloaded!")
        page_soup = BeautifulSoup(page_results.content, "html.parser")
        question_containers = page_soup.find_all("li", class_="css-qq6fb7")

        for container in question_containers:
            question_link_extension = container.a["href"]
            question_url = f"https://www.sweetstudy.com{question_link_extension}"
            question_links.append(question_url)
        print(f"Found {len(question_links)} question links on {page_url}.\n")
    except requests.exceptions.ConnectionError as e:  # More specific exception
        print(f"Connection error for {page_url}: {e}. Check internet-connection and try again.")
        return None  # Or return [], depending on desired behavior in scrape() - None signals error
    return question_links


# scrape individual questions
import requests
from bs4 import BeautifulSoup

def question_scrapper(question_url: str):
    if 'note-bank' in question_url:
        print(f"Skipping {question_url} because it's a note-bank URL.")
        return None

    question_html = requests.get(question_url)
    question_soup = BeautifulSoup(question_html.content, 'html.parser')
    print(f"\nProcessing question: {question_url}")

    question_title = ''
    body = ''
    attachments = []
    attachment_file_names = []
    attachment_content_string = ''  # Use attachment_content_string consistently
    category = ''
    tags = []

    # Get content from file attachments
    try:
        attached_files_number_container = question_soup.find('div', class_="css-503bni")
        if attached_files_number_container:
            attached_files_number_text = attached_files_number_container.text.strip()
            if attached_files_number_text and attached_files_number_text[-2].isdigit():
                attached_files_number = int(attached_files_number_text[-2])
                print(f"Found {attached_files_number} file attachments.")
                attached_filenames_container = question_soup.find_all('li', class_="css-1ap3j0h")
                attachment_content_containers_parent = question_soup.find('div', class_="css-xss17j")
                attachment_content_divs = []
                if attachment_content_containers_parent:
                    attachment_content_divs = attachment_content_containers_parent.findChildren(recursive=False)[1:]

                if attached_filenames_container:
                    for index, attached_file_element in enumerate(attached_filenames_container):
                        attachment_filename = attached_file_element.find('h2').text.strip() # Filename from h2 tag
                        attachments.append({'filename': attachment_filename, 'content': None})
                        attachment_file_names.append(attachment_filename)

                        if index < len(attachment_content_divs):
                            content_container_div = attachment_content_divs[index].find('div', class_="css-j3mg6j") # Content div using css-j3mg6j
                            if content_container_div:
                                content = content_container_div.text.strip()
                                attachments[index]['content'] = content
                                attachment_content_string += f"\n{attachment_filename}\n{content}\n"

    except AttributeError as e:
        print(f"AttributeError during file attachment processing for {question_url}: {e}")
        attachment_content_string = '' # Correctly initialize attachment_content_string in except block

    # Get attachment links (rest of your code for attachment links, title, body, category, tags, etc. remains the same)
    try:
        attachment_links = question_soup.find_all('li', class_="css-1960nst")
        if attachment_links:
            print(f"Found {len(attachment_links)} links for attachments.")
            for attachment_link in attachment_links:
                attachments.append({'filename': 'link', 'content': attachment_link.text})
                attachment_file_names.append(attachment_link.text) # Still add link filenames to attachment_file_names

    except AttributeError as e:
        print(f"AttributeError during attachment link processing for {question_url}: {e}")
        pass  # Link processing is not critical, so pass if fails


    # get title for each question
    try:
        question_title = question_soup.find('h1').text

        if 'esponse for' in question_title.lower() or 'respond' in question_title.lower() or 'response to' in question_title.lower():
            print(f"Skipping {question_url} because it's likely a response question.")
            return None

    except AttributeError:
        question_title = "Custom Solution - Writing Help by experts"

    # Get question text/description
    try:
        body = question_soup.find('div', class_="css-1lys3v9").text

        body_word_count = len(body.split())
        attachment_word_count = len(attachment_content_string.split()) # Use attachment_content_string here
        if (body_word_count + attachment_word_count) < 40:
            print(
                f"Skipping {question_url}. Combined word count: {body_word_count + attachment_word_count} (less than 40).")
            return None
    except AttributeError:
        body = attachment_content_string # Use attachment_content_string here


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
        tags = ["Solutions"]

    if len(question_title) < 25:
        body_snippet = body[0:40].replace('\n', ' ')
        if len(body) > 40:
            body_snippet = body_snippet[:body_snippet.rfind(' ')] + '...'
        question_title = f"{question_title}: {body_snippet} | {category}"

    # Build attachment_file and attachments_string
    content_attachment_files = []
    for attachment in attachments:
        if attachment['content']:
            content_attachment_files.append(attachment['filename'])
    attachment_file_string = '|'.join(content_attachment_files)
    attachments_string = '|'.join(attachment_file_names)
    tags_to_string = '|'.join(tags)

    question_data = {
        'title': question_title,
        'body': body,
        'attachments_string': attachments_string,
        'attachment_file': attachment_file_string, # Filenames of attachments with content
        'attachment_content': attachment_content_string.strip(), # String of filenames and content
        'category': category,
        'tags_string': tags_to_string,
        'question_url': question_url
    }

    print(f"{len(body)} => body and {len(attachment_content_string)} attachment_content in question.") # Use attachment_content_string here

    return question_data

def save_question_to_csv(question_data, csv_file_name='raw/h_market_latest.csv'):  # csv_file_name as parameter
    try:  # Add try-except for file operations
        with open(csv_file_name, 'a', encoding='utf-8', newline='') as q_file:  # Still append mode for now
            the_writer = writer(q_file)
            print("Saving question to file...")
            the_writer.writerow(question_data.values()) # Save dictionary values as row
        print("Saved to file...\n")  # Keep print for user feedback
        return None  # Standard return for functions that don't return a value
    except IOError as e:
        print(f"Error saving to CSV file {csv_file_name}: {e}")
        return None


def scrape(page_links):  # Renamed parameter to page_links for clarity
    print(f"{len(page_links)} page links ready for processing.")
    if page_links:  # Only proceed if there are page links
        print(f"Processing page links: \n Starting page link: {page_links[0]}\nLast Page Link on list: {page_links[-1]}")
        # First, process page links to extract question links and save to questions.json
        page_counter = 0
        page_links_copy = page_links[:]  # Iterate over a copy
        for page_url in page_links_copy:
            page_counter += 1
            print(f"Currently processing page link {page_counter}/{len(page_links)}: {page_url}...")
            try:
                question_urls_from_page = page_scrapper(page_url=page_url)  # Get question links from page
                if question_urls_from_page:  # Check if question links were extracted
                    existing_question_links = link_getter(filename="links/questions.json")  # Get existing question links
                    updated_question_links = existing_question_links + question_urls_from_page  # Append new question links
                    manual_links(links=updated_question_links,
                                filename="links/questions.json")  # Save ALL question links to questions.json
                    print(f"Extracted and saved {len(question_urls_from_page)} question links from {page_url} to questions.json.")
                else:
                    print(f"No question links found or error during page scrapping for {page_url}.")

                if page_url in page_links:  # Ensure page_url is still in the original list before removing
                    page_links.remove(page_url)  # Remove processed page link from page_links list
                manual_links(links=page_links, filename="links/links.json")  # Update links.json with remaining page links

            except requests.exceptions.ConnectionError as e:
                print(f'Connection problem processing page link {page_url}: {e}. Page link will be retried.')
                manual_links(links=page_links, filename="links/links.json")  # Save page links in case of error
                break
            except Exception as e:
                print(f"Unexpected error processing page link {page_url}: {e}. Page link will be retried.")
                manual_links(links=page_links, filename="links/links.json")  # Save page links in case of error
                break  # Exit the loop to stop processing
        print("Done processing page links...")

    # Now, process question links from questions.json
    question_links = link_getter(filename="links/questions.json")  # Load question links from questions.json
    if not question_links:
        print("No question links to scrape in questions.json. Page link processing complete (or no initial page links).")
        return print("Done processing.")  # Exit if no question links

    print(f"\n{len(question_links)} question links ready for scraping.")
    print(f"Scrapping question links: \n Starting question link: {question_links[0]}\nLast Question Link on list: {question_links[-1]}")

    question_counter = 0
    question_links_copy = question_links[:]  # Iterate over a copy
    while question_links: # Changed loop condition to while question_links is not empty - process until questions.json is empty
        question_url = question_links[0] # Get the first question link from the list
        print(f"Currently scraping question {question_counter + 1}/{len(question_links_copy)}: {question_url}...") # Use question_links_copy for total count
        try:
            q_data = question_scrapper(question_url=question_url)  # Scrape question data
            if q_data:  # Check if question data was successfully scraped
                save_question_to_csv(question_data=q_data)  # Save to CSV
                question_links.remove(question_url) # Remove the processed question link from the beginning of the list
                manual_links(links=question_links, filename="links/questions.json")  # Update questions.json
                print(f"Successfully scraped and saved question {question_counter + 1}/{len(question_links_copy)}: {question_url}. Removed from questions.json.")
            else:
                print(f"Skipped or error scraping question {question_url}. Removing from questions.json (no retry).")
                question_links.remove(question_url) # REMOVE URL even if scraping was skipped or failed
                manual_links(links=question_links, filename="links/questions.json")

        except requests.exceptions.ConnectionError as e:
            print(f'Connection problem scraping question {question_url}: {e}. Exiting script gracefully after saving progress.')
            manual_links(links=question_links, filename="links/questions.json")  # Save question links in case of error
            break  # Exit the while loop to stop scraping
        except Exception as e:
            print(f"Unexpected error scraping question {question_url}: {e}. Question link will be retried.")
            manual_links(links=question_links, filename="links/questions.json")  # Save question links in case of error
        finally: # Increment counter in finally block to ensure it runs even if there are errors
            question_counter += 1

    # RM? : manual_links(links=[], filename="links/questions.json")
    return print("Done scraping questions from questions.json...")


# on startup
if __name__ == "__main__":
    question_links = link_getter(filename="links/questions.json")  # Get existing question links FIRST

    if question_links:  # If there are question links, scrape them immediately
        print("Resuming question scraping from questions.json...")
        scrape(page_links=[])  # Call scrape with empty page_links to ONLY process question links
    else: # If no question links, check for page links
        print("No question links found in questions.json. Checking for page links in links.json...")
        page_links = link_getter(filename="links/links.json")  # Get page links

        if page_links:  # If page links exist, process them to extract questions
            print("Page links found in links.json. Starting page link processing to extract questions...")
            scrape(page_links=page_links)  # Call scrape with page_links to process page links
        else: # If no page links either, prompt user to build new ones
            print("No page links found in links.json or file does not exist.")
            build_new_links_choice = input("Do you want to build new page links? (yes/no): ").lower()
            if build_new_links_choice == 'yes':
                new_page_links = link_builder()
                if new_page_links:
                    manual_links(links=new_page_links, filename="links/links.json")  # Save new page links to links.json
                    page_links = new_page_links  # For informational message below
                    print(f"{len(page_links)} new page links built and saved to links.json.")
                    scrape(page_links=page_links) # Start scraping pages immediately after building
                else:
                    print("No new page links were built. Exiting.")
                    exit()
            else:
                print("Exiting without scraping.")
                exit()

    print("\nQuestions saved in format:"
          "\n'['title', 'body', 'attachments', 'attachment_file', "
          "'attachment_content', 'category', 'tags', 'question_url']'")