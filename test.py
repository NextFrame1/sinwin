import os


def caller():
	for root, dirs, files in os.walk(os.getcwd(), topdown=True):
		for file in files:
			if file.endswith('.tmp'):
				print(os.remove(os.path.join(root, file)))


caller()
