
from typing import Union
from instagrapi.types import Media, Collection
from concurrent import futures

import time
import os
import traceback
import instagrapi
import json

def get_credentials_from_input() -> Union[tuple, None]:
	try:
		print("Enter your username and password separated by a space.")
		items = input().split(" ")
		assert len(items) == 2
		return tuple( items )
	except:
		print("Invalid credentials input. Separate the username and password by a space.")
		return (None, None)

def get_credentials_from_file( filepath : str ) -> Union[tuple, None]:
	try:
		with open(filepath, "r") as file:
			items = file.readlines()
		assert len(items) == 2, "Invalid credentials file. Separate username and password by a new line."
		return tuple( items )
	except Exception as exception:
		print("Failed to read credentials file.")
		print( exception )
	return (None, None)

def attempt_login( username : str, password : str ) -> Union[instagrapi.Client, None]:
	try:
		client = instagrapi.Client()
		client.login( username=username, password=password )
		print("Successfully logged into account")
		return client
	except:
		print("Failed to login with these credentials.")
		return None

def download_media_item( client : instagrapi.Client, item : Media, directory : str ) -> tuple[bool, Media]:
	success : bool = True
	if item.media_type == 1: # photo
		try:
			client.photo_download(item.pk, directory)
		except Exception as e:
			traceback.print_exception(e)
			success = False
	elif item.media_type == 2: # video
		try:
			client.video_download(item.pk, directory)
		except Exception as e:
			traceback.print_exception(e)
			success = False
	elif item.media_type == 8: # album
		try:
			client.album_download(item.pk, directory)
		except Exception as e:
			traceback.print_exception(e)
			success = False
	time.sleep(2)
	return (success, item)

def bulk_download_media( client : instagrapi.Client, media : list[Media], directory : str, processes : int = 1 ) -> list[Media]:
	'''Any media that failed to download will be returned.'''
	pool = futures.ProcessPoolExecutor(processes)

	for item in media:
		os.makedirs( os.path.join(directory, str(item.media_type)), exist_ok=True )

	threads = [ pool.submit(download_media_item, client, item, os.path.join(directory, str(item.media_type))) for item in media ]

	total_items : int = len(media)
	counter : int = 1

	print(f'Queued {total_items} downloads from collection.')
	failed : list[Media] = []
	for item in futures.as_completed( threads ):
		print(counter, '/', total_items)
		counter += 1
		success, media_item = item.result()
		if success is False:
			failed.append(media_item)
	return failed

def bulk_download_collections( client : instagrapi.Client, collections : list[Collection] ) -> dict[str, list[Media]]:
	failed: dict[str, list[Media]] = {}
	for item in collections:
		failed[item.name] = []
		print(f'Downloading collection {item.name} with a total of {item.media_count} media items.')
		# Initialize the primary key (last_pk) to fetch the first media item
		chunk_size : int = 32
		total : int = 0
		last_pk = 0
		while True:
			# Fetch the next media item using the last_pk
			media: list[Media] = client.collection_medias(item.name, chunk_size, last_media_pk=last_pk)
			if not media:
				# If there are no more media items to download, break the loop
				break
			total += len(media)
			print(f'{total} / {item.media_count}')
			# Process the media item (download it)
			failed_items: list[Media] = bulk_download_media(client, media, "downloads", processes=1)
			# Update the last_pk to the last media item's pk
			last_pk = media[-1].pk
			# Add any failed downloads to the failed list
			failed[item.name].extend(failed_items)
	return failed

if __name__ == '__main__':

	user, password = get_credentials_from_input()
	if user is None or password is None: exit()

	os.system('cls')

	print("Logging into account.")
	client = attempt_login( user, password )
	if client is None: exit()

	#whitelist : list[str] = ["All Posts"]
	#collections : list[Collection] = [ item for item in client.collections() if item.name in whitelist ]
	collections = client.collections()
	failed_downloads : dict[str, list[Media]] = bulk_download_collections( client, collections )

	for name, media in failed_downloads.items():
		media_dumps : list[str] = [ item.model_dump_json(indent=4) for item in media ]
		with open(f'{name}_FAILED.json', 'w') as file:
			file.write( json.dumps(media_dumps, indent=4) )
