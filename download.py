
import instagrapi

from os import makedirs

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

print("Logging into account.")
assert cl.login(user, passwrd), "Failed to log into the account."
print("Logged in.")

print("Scanning post collection - all items.")
try:
	last_pk = 0
	try:
		with open("failed.txt", "a") as file:
			last_pk = file.readlines()[-1]
		print("Starting from last failed media.")
	except:
		print("Could not find last failed item.")
	collection = cl.collection_medias('All Posts', amount=9999, last_media_pk=last_pk)
except Exception as e:
	print("Failed to get all posts - reason: ")
	print(e)

print("Downloading found media.")
for item in [ "photos", "videos", "album" ]:
	makedirs(item, exist_ok=True)

def download_media_item( item ) -> None:
	if item.media_type == 1:
		# photo
		cl.photo_download(item.pk, "photos")
	elif item.media_type == 2:
		# video
		cl.video_download(item.pk, "videos")
	elif item.media_type == 8:
		# album
		cl.album_download( item.pk, "album" )

print("Appending downloads to pool: ", len( collection ))

for index, item in enumerate(collection):
	try:
		print(index, ' / ', len(collection), ' - ', item.pk)
		download_media_item( item )
	except:
		with open("failed.txt", "a") as file:
			file.write(f"{item.pk} {item.media_type}\n")

print("Downloaded all media.")
