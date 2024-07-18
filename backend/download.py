import os
import zipfile
import tarfile
import urllib.request
import logging
import sys
import yaml

from tqdm import tqdm


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def update_progress(pbar, block_size):
    pbar.update(block_size)


def download_file(url, local_filename):
    if os.path.exists(local_filename):
        logging.info(f"Local exist {local_filename} already, would not download it again.")
    else:
        logging.info(f"Downloading {local_filename}, please waiting...")
        response = urllib.request.urlopen(url)
        file_size = int(response.getheader("Content-Length"))
        with tqdm(total=file_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
            urllib.request.urlretrieve(url, local_filename, reporthook=lambda blocks, block_size, total_size: update_progress(pbar, block_size))
        logging.info(f"Download {local_filename} success.")


def extract_zipfile(zip_file, extract_folder=""):
    if zip_file.endswith(".zip"):
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            with tqdm(total=len(zip_ref.namelist()), unit="file", desc="Extracting") as pbar:
                for file in zip_ref.namelist():
                    zip_ref.extract(file, extract_folder)
                    pbar.update(1)
    elif zip_file.endswith(".tar.gz"):
        with tarfile.open(zip_file, 'r:gz') as tar_ref:
            with tqdm(total=len(tar_ref.getnames()), unit="file", desc="Extracting") as pbar:
                for file in tar_ref.getnames():
                    tar_ref.extract(file)
                    pbar.update(1)
    logging.info(f"Extract {zip_file} to {extract_folder} success.")


def read_yaml(yaml_path):
    with open(yaml_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    return yaml_data


if __name__ == "__main__":
    yaml_path = sys.argv[1]
    download_path = sys.argv[2]
    yaml_data = read_yaml(yaml_path=yaml_path)

    for key in yaml_data:
        yaml_value = yaml_data[key]
        for file_name in yaml_value.keys():
            url = yaml_value[file_name]["url"]
            extract_path = yaml_value[file_name]["extract_path"]
            local_filepath = os.path.join(download_path, file_name)
            download_file(url, local_filepath)
            if not extract_path:
                extract_path = download_path
            extract_zipfile(local_filepath, extract_path)
