from pathlib import Path
from tqdm import tqdm
from google.cloud import storage

def upload_to_bucket(blob_name, path_to_folder, bucket_name):
    """ Upload data to a bucket"""
    storage_client = storage.Client.from_service_account_json(
        'creds/creds.json')
    bucket = storage_client.get_bucket(bucket_name)
    for text_file in tqdm(list(Path(f"{path_to_folder}/text").glob("*.txt"))):
        blob = bucket.blob(f"{blob_name}/text/{text_file.name}")
        blob.upload_from_filename(text_file)
    for title_file in tqdm(list(Path(f"{path_to_folder}/title").glob("*.title"))):
        blob = bucket.blob(f"{blob_name}/title/{title_file.name}")
        blob.upload_from_filename(title_file)
    for audio_file in tqdm(list(Path(f"{path_to_folder}/audio").glob("*.mp3"))):
        blob = bucket.blob(f"{blob_name}/audio/{audio_file.name}")
        blob.upload_from_filename(audio_file)

    # return blob.public_url

upload_to_bucket(blob_name="RFIFulfulde",
                 path_to_folder="Batch3",
                 bucket_name="cawoylel-storage")