import os
import requests


def download_file(url, dest_folder, api_key):
    """Downloads a file from a URL to a destination folder, using authentication."""
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        filename = os.path.basename(url.split("?")[0])
        dest_path = os.path.join(dest_folder, filename)

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {url} to {dest_path}")
        return dest_path
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return None
