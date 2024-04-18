import urllib.request
import zipfile
import io

def downloadMasterData():
# Step 1: Download the zip file
    url = "https://api.shoonya.com/NFO_symbols.txt.zip"
    zip_file_path = "NFO_symbols.zip"  # Path to save the downloaded zip file

    urllib.request.urlretrieve(url, zip_file_path)

    # Step 2: Extract the contents
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall("extracted_files")  # Extract the contents to a directory

