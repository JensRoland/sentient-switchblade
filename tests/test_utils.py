import os

from switchbladecli.utils import hash_dir

def test_hash_a_folder_gives_correct_value():
    path_to_test_folder = os.path.join(os.path.dirname(__file__), "files", "hashing")
    expected_sha1 = "1c861420255f9e17c20eb6286eaa32832c14ea23"
    actual_sha1 = hash_dir(path_to_test_folder)
    assert actual_sha1 == expected_sha1
