import hashlib
import os


def sha1OfFile(filepath, use_sha):
    with open(filepath, 'rb') as f:
        while True:
            block = f.read(2**10) # Magic number: one-megabyte blocks.
            if not block: break
            use_sha.update(block)
        return use_sha.hexdigest()

def hash_dir(dir_path, existing_sha=None):
    for path, dirs, files in os.walk(dir_path):
        sha = existing_sha or hashlib.sha1()
        for file in sorted(files): # we sort to guarantee that files will always go in the same order
            sha1OfFile(os.path.join(path, file), sha)
        for dir in sorted(dirs): # we sort to guarantee that dirs will always go in the same order
            hash_dir(os.path.join(path, dir), sha)
        break # we only need one iteration - to get files and dirs in current directory
    return sha.hexdigest()
