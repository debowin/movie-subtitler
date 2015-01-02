"""
movie-subtitler
Movie Subtitle Downloader
A script to populate all folders containing movie files with best available subtitles from opensubtitles.org

How it Works:
1. Go through all contents of MOVIE_DIR.
2. Query opensubtitles.org for each movie and download LANGUAGE subtitles from trusted uploaders.
3. Extract the subtitle zipfile to the movie folder.
4. Rename the subfile as 'movie_filename.srt' for easy association.
5. Rename the movie folder's name in standard form i.e NAME [YEAR].

NOTE:
* Uses wget to download. (Add it to PATH)
* Uses 7z to extract. (Add it to PATH)

TO ADD:
* Lots of additional exception handling.
* OOP features.
"""

import subprocess
import os
import re
import shutil
import requests
import json
import BSXPath

# For silencing the output of subprocess calls.
FNULL = open(os.devnull, 'w')
LANG_ID_DICT = {
    'All': 'all',
    'English': 'eng'
}  # Maybe add some more popular ones

# CONFIG

HOST = 'http://www.opensubtitles.org'

TEMP_ZIP_DIR = "C:\\temp"

AJAX_URL = HOST + "/libs/suggest.php"

# If true, existing subtitles will be overwritten by new found ones.
OVERWRITE_EXISTING = True

FULL_TEXT_URL = HOST + \
    "/en/search2/sublanguageid-all/fulltextuseor-on/fixinput-on/moviename-"

# the super directory that contains all movies.
MOVIE_DIR = "C:\\AndroidSDK\\sdk\\extras"

# refer LANG_ID_DICT for valid keys.
LANGUAGE = "English"

# If True, only trusted subs will be downloaded.
# Note: If False, trusted subs will still be preferred.
TRUSTED = False

# If True, only HI subs will be downloaded.
HEARING_IMPAIRED = False

OPENSUB_URL = HOST + "/en/search/sublanguageid-%s/idmovie-" % LANG_ID_DICT[
    LANGUAGE]

MOVIE_FILE_FORMATS = ['.mkv', '.mp4', '.avi']

# XPATH
MOVIE_XPATH = "//a[@class='bnone']"
SUB_XPATH = "//tr[@class='change even expandable' or @class='change odd expandable']"
DOWNLOAD_XPATH = "//div[@class='download']/a"


def enclose(movie_path):
    """
    Takes a path to a file and encloses it in a folder of the same name. 
    """
    movie_folder_name = os.path.splitext(os.path.basename(movie_path))[0]
    os.makedirs(os.path.join(MOVIE_DIR, movie_folder_name))
    shutil.move(movie_path, os.path.join(MOVIE_DIR, movie_folder_name))


def get_movie_info(movie_filename):
    """
    Use the opensubtitles AJAX call to look for the movie.
    Return movie_id, name, year if the movie is found.
    """
    payload = {
        'format': 'json3',
        'MovieName': movie_filename
    }
    response = requests.get(AJAX_URL, params=payload)
    try:
        response_dict = json.loads(response.text)
    except ValueError:
        return None, None, None
    name = response_dict[0]['name']
    year = response_dict[0]['year']
    movie_id = str(response_dict[0]['id'])
    return movie_id, name, year


def full_text_search(movie_filename):
    """
    get movie_id using full text search in case AJAX call fails.
    """
    query = movie_filename.replace(' ', '+')
    response = requests.get(FULL_TEXT_URL + query)
    xsoup = BSXPath.BSXPathEvaluator(response.text)
    movie_tag = xsoup.getFirstItem(MOVIE_XPATH)
    movie_id_match = re.search(r'idmovie-(\d+)', movie_tag['href'])
    name_year_match = re.search(r'(.+)\s+\((\d+)\)', movie_tag.text)
    if movie_id_match is not None:
        return movie_id_match.group(1), name_year_match.group(1).strip(), name_year_match.group(2)
    return None, None, None


def get_sub(movie_id):
    """
    get trusted subtitles for given movie id
    """
    response = requests.get(OPENSUB_URL + movie_id)
    xsoup = BSXPath.BSXPathEvaluator(response.text)
    sub_tag_list = xsoup.getItemList(SUB_XPATH)
    if len(sub_tag_list) == 0:
        return None
    for sub_tag in sub_tag_list:
        if sub_tag.find(title='Subtitles from trusted source') is None:
            continue
        if HEARING_IMPAIRED and sub_tag.find(title='Subtitles for hearing impaired') is None:
            continue
        link = HOST + sub_tag.find(
            'a', href=re.compile(r'subtitleserve'))['href']
        uploader = sub_tag.findAll('td')[-1].a.text
        return link, uploader
    if not TRUSTED:
        print "No trusted subtitles found. Trying an untrusted one."
        sub_tag = sub_tag_list[0]
        link = HOST + \
            sub_tag.find('a', href=re.compile(r'subtitleserve'))['href']
        uploader = sub_tag.findAll('td')[-1].a.text
        return link, uploader
    return None


def download_sub(movie_filename, sub_link):
    """
    downloads the subtitle from given link,
    saving it as movie_filename.zip in TEMP_ZIP_DIR
    """
    zipfile_path = os.path.join(TEMP_ZIP_DIR, '%s.zip' % movie_filename)
    subprocess.call(['wget', sub_link, '-O', zipfile_path],
                    stdout=FNULL, stderr=subprocess.STDOUT)


def unzip_sub(movie_path, movie_filename):
    """
    unzip the archive to movie_dir
    delete archive
    """
    archive_path = os.path.join(TEMP_ZIP_DIR, '%s.zip' % movie_filename)
    subprocess.call(['7z', 'e', archive_path, '-o' + movie_path],
                    stdout=FNULL, stderr=subprocess.STDOUT)

    os.remove(archive_path)


def rename_movie_folder(movie_path, name, year):
    """
    rename the movie folder to a readable format
    'name[year]'
    """
    new_movie_path = os.path.join(
        os.path.dirname(movie_path), "%s [%s]" % (name, year))
    os.rename(movie_path, new_movie_path)


def rename_sub(movie_path, movie_filename):
    """
    rename the srt inside the movie folder
    to match the movie filename
    """
    srt_path = [os.path.join(movie_path, entity) for entity in os.listdir(
        movie_path) if entity.endswith('.srt') or entity.endswith('.sub')][0]
    os.rename(srt_path,
              os.path.join(movie_path, '%s.srt') % movie_filename)


def process_movie_file(movie_path):
    """
    if movie entity is a movie file,
    drop it into a folder of same name.
    return filename if movie file, None otherwise.
    """
    movie_entity = os.path.basename(movie_path)
    if os.path.splitext(movie_entity)[1] in MOVIE_FILE_FORMATS:
        print "%s is a movie file. Putting it in a directory." % movie_entity
        enclose(movie_path)
        movie_filename = os.path.splitext(movie_entity)[0]
        return movie_filename
    else:
        return None


def process_movie_folder(movie_path):
    """
    if movie entity is a directory,
    look for movie file and sub inside it.
    if sub found, rename if needed, return None.
    if movie file found, return filename, None otherwise.
    """
    movie_entity = os.path.basename(movie_path)
    print "%s is a directory." % movie_entity
    sub_filename = ""
    movie_filename = ""
    for filename in os.listdir(movie_path):
        file_size = os.path.getsize(os.path.join(movie_path, filename))
        if filename.endswith('.srt') or filename.endswith('.sub'):
            print "Subtitles already present."
            if OVERWRITE_EXISTING:
                os.remove(os.path.join(movie_path, filename))
                print "Overwriting."
            else:
                sub_filename = os.path.splitext(filename)[0]
        if os.path.splitext(filename)[1] in MOVIE_FILE_FORMATS and file_size > 1024 * 1024 * 100:
            # if filetype is correct and size is greater than 100
            # MiB(filter out samples)
            movie_filename = os.path.splitext(filename)[0]
    if movie_filename == "":
        print "No movie file found. Moving on."
        return None
    if sub_filename != "":
        if sub_filename != movie_filename:
            rename_sub(movie_path, movie_filename)
            print "Renamed existing subtitles."
        if re.match(r'.+?\[\d+\]', movie_entity) is None:
            movie_id, name, year = get_movie_info(movie_filename)
            rename_movie_folder(movie_path, name, year)
            print "Renamed movie folder."
        print "Moving on."
        return None
    return movie_filename


def main():
    """
    main function
    """
    for movie_entity in os.listdir(MOVIE_DIR):
        print ""
        movie_path = os.path.join(MOVIE_DIR, movie_entity)
        if os.path.isfile(movie_path):
            movie_filename = process_movie_file(movie_path)
            if movie_filename is None:
                continue
            movie_path = os.path.join(MOVIE_DIR, movie_filename)
        else:
            movie_filename = process_movie_folder(movie_path)
            if movie_filename is None:
                continue
        movie_id, name, year = get_movie_info(movie_filename)
        if movie_id is None:
            print "Unable to detect movie by AJAX call. Trying Full Text Search."
            movie_id, name, year = full_text_search(movie_filename)
            if movie_id is None:
                print "Unable to detect movie. Check the filename. Moving on."
                continue
        print "Detected Movie: %s [%s]" % (name, year)
        print "ID(on opensubtitles.org): %s" % movie_id
        sub = get_sub(movie_id)
        if sub is None:
            print "No suitable subtitles found. Moving on."
            rename_movie_folder(movie_path, name, year)
            continue
        print "Downloading %s subtitles by %s." % (LANGUAGE.upper(), sub[1])
        sub_link = sub[0]

        download_sub(movie_filename, sub_link)
        unzip_sub(movie_path, movie_filename)
        rename_sub(movie_path, movie_filename)
        rename_movie_folder(movie_path, name, year)

if __name__ == "__main__":
    main()
    FNULL.close()
