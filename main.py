import os

import requests
from csv import reader
import json


def consume_api(api_url: str, data: list):
    response = requests.post(api_url, json=data)

    if response.status_code == 200:

        try:
            res_data = response.json()
            return res_data
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Decode Error occurred (response): {e.response}")
            print(f"JSON Decode Error occurred(raw): {e}")
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)
        return None


# read questions from csv and format them to be consumed by API
def read_from_csv(csv_file_name: str = 'h_market_latest.csv'):
    with open(f"raw/{csv_file_name}", 'r', encoding='utf-8', newline='') as q_file:
        # use csv reader function to read from csv file
        questions_data = []
        dataset = reader(q_file)

        #track title
        title_counts = {}
        counter = 1

        for row in dataset:
            original_title = row[0].strip()
            tag = row[3] or row[4].strip()
            category = row[2].strip()

            # check if title is in the title_counts
            if original_title in title_counts:
                # catch duplicate and update title
                title_counts[original_title] += 1
                counter += 1
                new_title = f"{original_title}: {category} - {tag} {title_counts[original_title]} {counter}"
            else:
                # if not a duplicate add it to title_counts for tracking
                title_counts[original_title] = 1
                new_title = f"{original_title} - {tag}"

            question = {
                'title': new_title,
                'body': row[1].strip(),
                'category': category,
                'tag': tag,
            }
            questions_data.append(question)

    return questions_data


# save questions into a json file
def save_to_json(data: list, filename: str = 'questions'):
    qns_data = {
        'data': data,
    }

    json_object = json.dumps(qns_data, indent=4)

    # write to JSON file
    with open(f"data/{filename}.json", "w") as json_file:
        json_file.write(json_object)


def read_from_json(filename: str = 'questions'):
    data = []
    with open(f"data/{filename}.json", "r") as json_file:
        json_object = json.load(json_file)

        for q in json_object['data']:
            data.append(q)

    return data


def process_batch(url: str, data: list, batch_size: int):
    processed_questions = 0

    while data and len(data)> 0:
        if len(data) < batch_size:
            batch = data
            data = []
        else:
            batch = data[:batch_size]
            data = data[batch_size:]

        try:
            print(f"current batch: {len(batch)}")
            response_data = consume_api(url, batch)
            # check if response was successful
            if not response_data['statusCode'] == 201:
                print(f"\nAn error occurred while processing the files.\n"
                      f"message: {response_data['message']}\n")
                print(response_data)
                exit()

            processed_questions += len(batch)
            try:
                print(f"\nUpdating json file with {len(data)} unprocessed.")
                save_to_json(data)
                print("\nUpdated json file.")
            except Exception as e:
                print("Error while trying to update json: \n")
                print(e)

            print(f"Processed {processed_questions}. Processing next batch...\n")
            print(response_data)
            batch = []

        except requests.exceptions.ConnectionError as ce:
            print(f"\n\nConnection Error: {ce}")

            print(f"A connection error occurred while processing data."
                  f"{processed_questions} Had Been Processed Successfully.\n\n")
            print("\nUpdating json file.")
            save_to_json(data)
            exit()

    print(f"\n\nCompleted uploading. {processed_questions} Processed Successfully.")


if __name__ == "__main__":
    url = 'https://writeessayscheap.org/api/json-ep'
    # read all data from the json file
    json_data = read_from_json()

    if len(json_data) == 0:
        print(f"There are no unprocessed questions. Enter a new csv file to process...\n")
        csv_file_name = input(f"Enter the name of the file to be processed: e.g, 'h_market_latest.csv'."
                              f"\n\nTHE FILE MUST BE IN THE 'raw' FOLDER..."
                              f"\n You should enter the file name in the following format: -> 'filename.csv' or "
                              f"'data_to_upload.csv'\n\n"
                              f"Leave blank to use the default file name 'h_market_latest.csv': ")
        if not csv_file_name:
            csv_file_name = 'h_market_latest.csv'
        # read scrapped data from csv file
        try:
            csv_data = read_from_csv(csv_file_name)
        except FileNotFoundError as err:
            print("The file you entered does not exist!!\n"
                  "Ensure the name is correct and the file exists in the 'raw' folder and try again!")
            exit()

        # format/prepare the data into a json file (api friendly data format)
        save_to_json(csv_data)

        json_data = read_from_json()

    print(f"Found {len(json_data)} questions. Processing...\n")
    # prepare it in batches of 50 items
    batch_size = 20
    process_batch(url, json_data, batch_size)
    print(f"Nothing to process!\n\nProgram Done.")
    exit()

    # once all items are processed, delete the json file and update the record for processed csv files
