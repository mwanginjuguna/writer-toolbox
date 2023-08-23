import requests
from csv import reader
import json


def consume_api(api_url: str, data: list):
    response = requests.post(api_url, json=data)

    if response.status_code == 200:
        print(response.text)
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
    with open(f"/raw/{csv_file_name}", 'r', encoding='utf-8', newline='') as q_file:
        # use csv reader function to read from csv file
        questions_data = []
        dataset = reader(q_file)

        for row in dataset:
            question = {
                'title': row[0].strip(),
                'body': row[1].strip(),
                'category': row[2].strip(),
                'tag': row[3].strip() or row[4].strip(),
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
    with open(f"{filename}.json", "r") as json_file:
        json_object = json.load(json_file)

        for q in json_object['data']:
            data.append(q)

    return data


def process_batch(url: str, data: list, batch_size: int):
    processed_questions = 0

    while data:
        if len(data) < batch_size:
            batch = data
        else:
            batch = data[:batch_size]
            data = data[batch_size:]

        try:
            response_data = consume_api(url, batch)
            processed_questions += len(batch)
            print(f"Processed {processed_questions}. Processing next batch...")
            print(response_data)
        except requests.exceptions.ConnectionError as ce:
            print(f"Connection Error: {ce}")
            print(f"A connection error occurred while processing data."
                  f"{processed_questions} Had Been Processed Successfully.")
            save_to_json(data)
            break
    print(f"Completed uploading. {processed_questions} Processed Successfully.")


if __name__ == "__main__":
    url = 'http://localhost:8888/api/json-ep'
    # read scrapped data from csv file
    csv_data = read_from_csv()
    # format/prepare the data into a json file (api friendly data format)
    save_to_json(csv_data)
    # read all data from the json file
    json_data = read_from_json()
    # prepare it in batches of 20 items
    batch_size = 20
    process_batch(url, json_data, batch_size)

    print(f"Nothing to process! Processed Successfully.")
    exit()

    # once all items are processed, delete the json file and update the record for processed csv files
