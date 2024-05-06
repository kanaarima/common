

from ..database.repositories import releases
from typing import List

def fetch_hashes(version: int) -> List[str]:
    return [
        hash
        for release in releases.fetch_hashes(version) or []
        for file in release[0]
        for hash in file['md5']
    ]

def is_valid_client_hash(version: int, hash: str) -> bool:
    hashes = fetch_hashes(version)
    return hash in hashes
