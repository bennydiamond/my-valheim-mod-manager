# my-valheim-mod-manager
Little mod manager for Valheim I made for personnal use. Very much tailored to my needs.
Must be ran in gmae root folder (same location as valheim.exe)
Trying to keep exe size as small as possible to keep ability to upload directly to Discord channels.


# Features #

- Toggle between flatscreen and VR for VHVR

- Check if plugins folder contains exactly the files it expects, via a .properties containing a list of filenames and mathcing hashes.

- Move out of the way any extra files.


# TODO #

- Download and unzip modpack archive from http

- Offer users ability to force reinstall modpack

- Detect and automatically download modpack if file missing or file md5 mismatch

- Detect and update to a new modpack revision

- Check files md5 in "Valheim_Data" folder (for VHVR)

- Fix bugs(obviously)


# Limitations: #

- Works pretty much just for Windows due to paths referenced using backslashes.