from __future__ import print_function
import pickle
import os.path
import glob
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import yaml
import time
import logging

logging.basicConfig(filename='upload_backup.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

CONFIG_FILE = None

SCOPES = None
BACKUP_FILES_PATH = None
GOOGLE_DRIVE_BACKUP_FOLDER_ID = None
BACKUP_FILES_MIME_TYPE = None
MAX_BACKUPS_UPLOADED = None


with open('upload_backup_config.yml', 'r') as configFile:
    CONFIG_FILE = yaml.load(configFile)
SCOPES = [CONFIG_FILE["backup"]["scope"]]
BACKUP_FILES_PATH = CONFIG_FILE["backup"]["backups_file_path"]
GOOGLE_DRIVE_BACKUP_FOLDER_ID = CONFIG_FILE["backup"]["google_drive_backup_folder_id"]
BACKUP_FILES_MIME_TYPE = CONFIG_FILE["backup"]["backup_files_mime_type"]
MAX_BACKUPS_UPLOADED = CONFIG_FILE["backup"]["max_backups_uploaded"]


def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


GD_SERVICE = build('drive', 'v3', credentials=get_credentials())


def get_file_path_to_backup():
    list_of_files = glob.glob(BACKUP_FILES_PATH)
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def get_file_name_from_path(filepath):
    return os.path.basename(filepath)


def upload_file(service, filepath, filename, folderid, mimetype):
    file_metadata = {
        'name': filename,
        'parents': [folderid]
    }
    media = MediaFileUpload(filepath,
                            mimetype=mimetype)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    logging.info('File ID: %s' % file.get('id'))


def upload_chunk(request):
    status, response = request.next_chunk()
    if status:
        logging.info("Uploaded %d%%." % int(status.progress() * 100))
    logging.info("Upload chunk complete!")
    return status, response


def upload_file_resumable(service, filepath, filename, folderid, mimetype):
    file_metadata = {
        'name': filename,
        'parents': [folderid]
    }
    media = MediaFileUpload(filepath,
                            mimetype=mimetype,
                            resumable=True)
    request = service.files().create(body=file_metadata,
                                     media_body=media)
    response = None
    while response is None:
        try:
            status, response = upload_chunk(request)
        except HttpError as error:
            if error.resp.status in [404]:
                logging.error("Upload fails with 404 error... starting the upload all over again")
                upload_file_resumable(service, filepath, filename, folderid, mimetype)
            elif error.resp.status in [500, 502, 503, 504]:
                logging.error("Upload fails for %d error, sleeping 5 seconds and retrying to download the next chunk" % error.resp.status)
                time.sleep(5)
                status, response = upload_chunk(request)
            else:
                logging.error("Upload fails for some unknow reason... shit happens")

    return response


def list_files_from_gdrive_folder(service, folder_id):
    results = service.files().list(q="'{}' in parents and not trashed".format(folder_id),
                                   fields="nextPageToken, files(id, name, createdTime)",
                                   orderBy="createdTime desc",
                                   pageSize=10).execute()
    return results.get('files', [])


def print_files(title, list_files):
    if not list_files:
        logging.info('### {} IS EMPTY ###'.format(title))
    else:
        logging.info('### {} ###'.format(title))
        for item in list_files:
            logging.info(u'{0} ({1}) ({2})'.format(item['name'], item['id'], item['createdTime']))


def last_local_backup_uploaded(files, filename):
    return filename in [name['name'] for name in files]


def old_uploaded_backups_to_delete(files):
    return files[MAX_BACKUPS_UPLOADED-1:]


def delete_old_uploaded_backups(service, files):
    for file in files:
        service.files().delete(fileId=file['id']).execute()


def main():
    logging.info('### Starting remote backup script ###')
    last_backup_filepath = get_file_path_to_backup()
    last_backup_filename = get_file_name_from_path(last_backup_filepath)
    uploaded_backup_files = list_files_from_gdrive_folder(GD_SERVICE, GOOGLE_DRIVE_BACKUP_FOLDER_ID)

    print_files('UPLOADED FILES', uploaded_backup_files)

    if last_local_backup_uploaded(uploaded_backup_files, last_backup_filename):
        logging.info('### Last backup already uploaded ###')
    else:
        logging.info('### Lets upload this shit ###')
        upload_file_resumable(GD_SERVICE,
                    last_backup_filepath,
                    last_backup_filename,
                    GOOGLE_DRIVE_BACKUP_FOLDER_ID,
                    BACKUP_FILES_MIME_TYPE)

    uploaded_files_to_delete = old_uploaded_backups_to_delete(uploaded_backup_files)
    print_files('UPLOADED FILES TO DELETE', uploaded_files_to_delete)
    delete_old_uploaded_backups(GD_SERVICE, uploaded_files_to_delete)

if __name__ == '__main__':
    main()
