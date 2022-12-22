import os
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential
import zipfile
import argparse
import io

token_credential = ClientSecretCredential("tenant-id", "client-id", "client-secret")

OAUTH_STORAGE_ACCOUNT_NAME = "prodeastus2data"
oauth_url = f"https://{OAUTH_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"

blob_service_client = BlobServiceClient(account_url=oauth_url, credential=token_credential)


def get_blob_list():
    '''Extracts list of files named with a specific prefix and date.'''

    dr_dir = blob_service_client.get_container_client(namespace.container_name)
    blob_list = [x for x in dr_dir.list_blobs(name_starts_with="raw/" + namespace.prefix)
                  if namespace.filter_date in (x.name).replace('_','')]
    if not blob_list:
        print(f"There are no files which starts with raw/{namespace.prefix}"
              f" and includes date {namespace.filter_date}.")
    return blob_list


def unpack_rename_files(blob_list):
    '''Extracts csv file to clipboard, renames if needed and saves it in dropdir/sasb/sics folder.'''

    dr_dir = blob_service_client.get_container_client(namespace.container_name)
    for blob in blob_list:
        blob_name = blob.name
        print(f"{blob_name} file found and unpacking process started.")
        blob = blob_service_client.get_blob_client(namespace.container_name, blob_name)
        with io.BytesIO() as b:
            download_stream = blob.download_blob(0)
            download_stream.readinto(b)
            with zipfile.ZipFile(b, compression=zipfile.ZIP_LZMA) as z:
                for filename in z.namelist():
                    if filename.endswith('csv'):
                        basename, extension = os.path.splitext(filename)
                        system_name, feed1, feed2, some_date, version = basename.split('_')
                        if len(some_date) < 8:
                            some_date = '20' + some_date
                            correct_filename = ("{}_{}_{}_{}_{}{}".format(system_name, feed1, feed2,
                                                                          some_date, version, extension))
                        
                        with z.open(filename, mode='r', pwd=b'') as f:                            

                            if dr_dir.get_blob_client("dropdir/sasb/sics/" + correct_filename).exists():                                
                                print(f"{correct_filename} already exists" 
                                      f"in {namespace.container_name}/dropdir/sasb/sics.")
                            else:
                                dr_dir.get_blob_client("dropdir/sasb/sics/" + correct_filename).upload_blob(f)
                                print(f"{correct_filename} uploaded successfully.")
                

def create_parser():
    ''' Reads and adds argument values from the command line.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('filter_date')
    parser.add_argument('prefix')
    parser.add_argument('container_name')
    return parser


if __name__ == "__main__":

    parser = create_parser()
    namespace = parser.parse_args()
    blob_list = get_blob_list()
    unpack_rename_files(blob_list)
