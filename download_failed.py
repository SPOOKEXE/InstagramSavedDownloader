import instagrapi

from os import makedirs
from concurrent import futures

with open("failed.txt", "r") as file:
	lines = [ line for line in file.readlines() if line.strip() != "" ]

def get_credentials( ) -> tuple:
	try:
		with open("credentials", "r") as file:
			return tuple( file.readlines() )
	except Exception as exception:
		print("Failed to read credentials file.")
		print( exception )
	return (None, None)

user, passwrd = get_credentials()

cl = instagrapi.Client()

def download_media_item( pk, media_type ) -> None:
	pk = int(pk)
	media_type = str(media_type)
	if media_type == "1":
		# photo
		cl.photo_download(pk, "photos")
	elif media_type == "2":
		# video
		cl.video_download(pk, "videos")
	elif media_type == "8":
		cl.album_download( pk, "album" )

for item in [ "photos", "album", "videos" ]:
	makedirs(item, exist_ok=True)

pool = futures.ThreadPoolExecutor(max_workers=12)

print("Appending downloads to pool: ", len( lines ))
items = [ ]
for index, line in enumerate(lines):
	pk, media_type = tuple( line.split(" ") )
	print(index, pk)
	try:
		download_media_item( pk, media_type )
	except:
		with open("failed_again.txt", "a") as file:
			file.write(f"{pk} {media_type}\n")
