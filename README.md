# movie-subtitler
*Movie Subtitle Downloader*
> A script to populate all folders containing
> movie files with best available subtitles 
> from opensubtitles.org

## How it Works:
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