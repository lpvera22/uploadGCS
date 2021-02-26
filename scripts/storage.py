from google.cloud import storage


def upload_to_bucket(blob_name, path_to_file, bucket_name):
    """ Upload data to a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'firebasestorage-305919-ce0834d3d511.json')

    bucket = storage_client.get_bucket(bucket_name)
    # print('STORAGE ---->', list(storage_client.list_blobs(bucket)))

    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)

    # returns a public url
    return blob.public_url
