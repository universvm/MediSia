from preprocessor import preprocess
from user import * 
import json
import math



if __name__ == '__main__':
	indexdic = load_index_from_disk()
	docid_info = load_docinfo_from_disk()
	with open('processed_data/num_of_docs.txt','r', encoding = 'utf-8') as f:
		# N is the number of documents
		N = int(f.readline())
	while 1:
		option = input("Please just input the number 1 or 2 or 0: 1 is Boolean search, 2 is Tfidf, 0 is ending this program:\n")

		if option == '1':
			runBoolean(indexdic, docid_info, N)
		elif option == '2':
			runTfidf(indexdic, docid_info, N)
		elif option == '0':
			print('Goodbye!')
			break
		else:
			print("invalid input!\n")