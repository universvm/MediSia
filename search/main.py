from inverted_index import *
from tfidf import run_tfidf
from bool import run_boolean
import os

if __name__ == '__main__':

    if not os.path.exists('./processed_data'):
        # If this is the first time to run this system, it will generate the
        # inverted index file and other related files.
        os.mkdir(os.getcwd() + '\\processed_data')
        # Change the path to use other dataset
        source_file_path = 'datasets/biopapers_sample_w_abstract.jsonl'
        words_index, docid_info = create_alphabetical_inverted_index(
            source_file_path)
        write_index_to_disk(words_index)
        write_docinfo_into_disk(docid_info)
        write_numbers_of_docs_into_disk(docid_info)
        print('Inverted index builder is finished')

    indexdic = load_index_from_disk()
    docid_info = load_docinfo_from_disk()
    with open('processed_data/num_of_docs.txt', 'r', encoding='utf-8') as f:
        # doc_numbers is the number of documents
        doc_numbers = int(f.readline())
    while True:
        option = input(
            "Please just input the number 1 or 2 or 0: 1 is Boolean search, 2 is Tfidf, 0 is ending this program:\n")

        if option == '1':
            run_boolean(indexdic, docid_info, doc_numbers)
        elif option == '2':
            run_tfidf(indexdic, docid_info, doc_numbers)
        elif option == '0':
            print('Goodbye!')
            break
        else:
            print("invalid input!\n")
