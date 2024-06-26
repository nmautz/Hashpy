# Author: Nathan M
# Desc: Hashes directory (recursivly) or file and saves results to be checked against. Depending on cli args it will do either hashing, checking hashes, or both

import hashlib
import os
import sys
import time

CURRENT_VERSION = "0.2"
SUPPORTED_VERSIONS = [CURRENT_VERSION, "0.1"]

def hash_file(filename):
    """This function returns the SHA-1 hash of the file passed into it"""
    # make a hash object
    h = hashlib.sha1()

    if save_load == 0:
        print(f"Hashing file of size {format_file_size(os.path.getsize(filename))}")

    # open file for reading in binary mode
    with open(filename, 'rb') as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # https://stackoverflow.com/questions/17731660/hashlib-optimal-size-of-chunks-to-be-used-in-md5-update
            chunk = file.read(65536)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def get_file_details(filepath):
    filehash = hash_file(filepath)
    file_size,modified_date = get_quick_file_details(filepath)
    return filehash, file_size, modified_date

def get_quick_file_details(filepath):
    file_size = os.path.getsize(filepath)
    modified_date = os.path.getmtime(filepath)
    return file_size, modified_date

def get_quick_directory_details(directory):
    """This function hashes all files in a directory and saves the results to a CSV file"""
    hashes = {}
    #check if file instead of dir
    if os.path.isfile(directory):
        file_size,modified_date = get_quick_file_details(directory)
        hashes[directory] = [file_size, modified_date]
        return hashes
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_size,modified_date = get_quick_file_details(filepath)
            hashes[filepath] = [file_size, modified_date]
    return hashes

def hash_directory(directory):
    """This function hashes all files in a directory and saves the results to a CSV file"""
    hashes = {}
    #check if file instead of dir
    if os.path.isfile(directory):
        filehash,file_size,modified_date = get_file_details(directory)
        hashes[directory] = [filehash, file_size, modified_date]
        return hashes
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            filehash,file_size,modified_date = get_file_details(filepath)
            hashes[filepath] = [filehash, file_size, modified_date]
    return hashes


def find_file(file_hash, file_size, target_dir_path):
    """This function finds a file in a directory by its hash"""
    for root, dirs, files in os.walk(target_dir_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            target_filesize = str(os.path.getsize(filepath))
            #if target_filesize == file_size:
            filehash = hash_file(filepath)
            if filehash == file_hash:
                return filepath
    return None

def save_hashes(hashes, filename):
    """This function saves the hashes to a CSV file"""
    with open(filename, 'w') as f:
        # Write the version number to the file
        f.write(f"{CURRENT_VERSION}\n")

        for filepath, file_details in hashes.items():
            filehash = file_details[0]
            file_size = file_details[1]
            modified_date = file_details[2]
            f.write(f"{filepath}::::{filehash}::::{file_size}::::{modified_date}\n")

def load_hashes(filename):
    """This function loads hashes from a CSV file"""
    hashes = {}
    with open(filename, 'r') as f:
        # read first line to get version number
        version_str = f.readline()
        version_str = version_str.strip()
        if not version_str in SUPPORTED_VERSIONS:
            print(f"Unsupported version: {version_str}")
            print(f"Supported versions: {SUPPORTED_VERSIONS}")
            exit(1)
        elif not version_str == CURRENT_VERSION:
            print(f"Warning: Hash version {version_str} is not the current version ({CURRENT_VERSION}). Latest features unavailible")
        for line in f:
            split_line = line.strip().split('::::')
            filepath = split_line[0]
            filehash = split_line[1]
            file_size = split_line[2] if len(split_line) > 2 else None
            modified_date = split_line[3] if len(split_line) > 3 else None
            hashes[filepath] = [filehash,file_size,modified_date]
    return hashes

def format_file_size(size_in_bytes):
    size_in_bytes = float(size_in_bytes)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    unit_index = 0
    while size_in_bytes >= 1024 and unit_index < len(units) - 1:
        size_in_bytes /= 1024
        unit_index += 1
    return "{:.2f} {}".format(size_in_bytes, units[unit_index])

def reckech_hashes(directory, original_hashes):
    """This function rechecks the hashes of files in a directory against the original hashes"""
    num_unchanged = 0
    changed_files = []
    current_hashes = hash_directory(directory)
    for filepath, file_details in current_hashes.items():
        original_file_details = original_hashes.get(filepath)
        if original_file_details is None:
            print(f"File {filepath} is new or moved.")
            changed_files.append(filepath)
        elif file_details is None:
            print(f"File {filepath} is deleted.")
            changed_files.append(filepath)
        else:
            filehash = file_details[0]
            original_filehash = original_file_details[0]

            if filehash == original_filehash:
                num_unchanged += 1
            else:
                print(f"File {filepath} has changed.")
                changed_files.append(filepath)


    print(f"{num_unchanged} files unchanged")
    return changed_files

def quick_recheck_hashes(directory, original_hashes):
    """This function rechecks the hashes of files in a directory against the original hashes"""
    num_unchanged = 0
    current_hashes = get_quick_directory_details(directory)
    changed_files = []
    for filepath, file_details in current_hashes.items():
        original_file_details = original_hashes.get(filepath)
        if original_file_details is None:
            print(f"File {filepath} is new or moved.")
            changed_files.append(filepath)
        elif file_details is None:
            print(f"File {filepath} is deleted.")
            changed_files.append(filepath)
        else:
            file_size = str(file_details[0])
            modified_date = str(file_details[1])
            original_file_size = original_file_details[1]
            original_modified_date = original_file_details[2]

            if file_size == original_file_size and modified_date == original_modified_date or (file_size != None and modified_date != None):
                file_size_human_readable = format_file_size(file_size)
                file_hash = hash_file(filepath)
                original_file_hash = original_file_details[0]
                if original_file_hash == file_hash:
                    num_unchanged += 1
                else:
                    print(f"File {filepath} has changed.")
                    changed_files.append(filepath)
            else:
                print(f"File {filepath} has changed.")
                changed_files.append(filepath)

    print(f"{num_unchanged} files unchanged")
    return changed_files

try:

    save_load = int(sys.argv[1])
    directory = sys.argv[2]
    hashes_file = sys.argv[3]
except:
    print("save_load: 0 - Hash all files in the directory and save the results")
    print("           1 - Load the original hashes and recheck")
    print("           2 - check hashes and update only changed values")
    print("           3 - Search for a specific hash(s) from a file")
    print("           4 - Search for specific file in directory")
    print("Usage: python hash.py <save_load> <directory> <hashes_file>")
    exit(1)

start_time = time.time()

if save_load == 1:
    try:
        quick_search = int(sys.argv[4])
    except:
        print("Quick search not specified, defaulting to 0 (Off)")
        quick_search = 0

if save_load == 0:

    # Hash all files in the directory and save the results
    hashes = hash_directory(directory)
    save_hashes(hashes, hashes_file)
elif save_load == 1:

    # Load the original hashes and recheck
    original_hashes = load_hashes(hashes_file)
    if quick_search == 1:
        quick_recheck_hashes(directory, original_hashes)
    else:
        reckech_hashes(directory, original_hashes)
elif save_load == 2:
    # check hashes and update only changed values
    original_hashes = load_hashes(hashes_file)
    changed_file_paths = reckech_hashes(directory, original_hashes)
    for filepath in changed_file_paths:
        if not os.path.exists(filepath):
            # File {filepath} is deleted
            original_hashes.pop(filepath)
        else:
            # File {filepath} has changed or is new or moved.
            filehash, file_size, modified_date = get_file_details(filepath)
            original_hashes[filepath] = [filehash, file_size, modified_date]
    print(f"Saving {len(changed_file_paths)} changed hashes...")
    save_hashes(original_hashes, hashes_file)

elif save_load == 3:
    # Search for a specific hash(s) from a file
    file_hash_path = directory
    target_dir_path = hashes_file
    file_hashs = load_hashes(file_hash_path)
    file_hashs = file_hashs.values()
    for file_obj in file_hashs:
        file_hash = file_obj[0]
        file_size = file_obj[1]
        filepath = find_file(file_hash, file_size, target_dir_path)
        if filepath is not None:
            print(f"File found at {filepath}")

elif save_load == 4:
    # Search for a matching file
    file_path = directory
    target_dir_path = hashes_file
    file_hash = hash_file(file_path)
    file_size = os.path.getsize(file_path)
    filepath = find_file(file_hash, file_size, target_dir_path)
    if filepath is not None:
        print(f"File found at {filepath}")
    else:
        print("File not found")



else:
    print("Invalid save/load option")
    exit(1)


def format_time(time):
    return f"{time:.2f}s"

end_time = time.time()

time_elapsed = end_time - start_time
formated_time_e = format_time(time_elapsed)
print(f"Time elapsed: {formated_time_e}")