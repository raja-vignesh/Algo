import urllib.request
import zipfile
import ssl

def downloadMasterData():
    # Step 1: Download the zip file
    url = "https://api.shoonya.com/NFO_symbols.txt.zip"
    zip_file_path = "NFO_symbols.zip"  # Path to save the downloaded zip file

    # Create an SSL context that does not verify the certificate
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Download the ZIP file using the custom SSL context
    with urllib.request.urlopen(url, context=context) as response:
        with open(zip_file_path, 'wb') as out_file:
            out_file.write(response.read())

    # Step 2: Extract the contents
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall("extracted_files")  # Extract the contents to a directory

