from preprocessor import preprocess
import jsonlines
import json

def create_wordsRepo_docid_info(filepath):
    '''
    This part creates the prototype of inverted index.
    It also create a dictionary storing information we want to show and filter.
    I think changing method to vectorizing is in this part.
    '''
    
    #All of the count (including the docid and term_position) starts from 0 instead of 1.


    # create the dictionary of wordsRepo:
    wordsRepo = {}
    lower_letters = [chr(i) for i in range(97, 123)] #The result is [a-z]
    for alphabet in lower_letters:
        wordsRepo[alphabet]={}
    wordsRepo['num']={} # When the first letter of the term is not [a-z], it will be assigned into this dictionary of wordsRepo['num'] 
    # 'wordsRepo' will be transformed into inverted index in the function 'write_index_to_disk()'.

    #create the dictionary of 'docid_info' 
    docid_info = {}
    '''
    Structure of 'docid_info': {docid:[]}, the reason why I use list is because the memory of list is smaller than dict.
    We could put everything we want to extract from our original file into the list in a specific order, 
    so we could use index (like docid[0] means 'doi_url') to represent different attribute. 
    '''

    with open(filepath, "r+", encoding="utf8") as f:
        for docid, item in enumerate(jsonlines.Reader(f)): #docid counts from 0
            content = preprocess(str(item['title'])+str(item['abstract']))

            ################ Start the process for docinfo#############
            '''
            docid_info[docid][0]: doi_url
            docid_info[docid][1]: title
            docid_info[docid][2]: abstract
            '''
            docid_info[docid]=[]
            docid_info[docid].append(str(item['doi_url']))
            docid_info[docid].append(str(item['title']))
            if len(item['abstract'])<=300: #Control the abstract only display around 300 characters
                docid_info[docid].append(str(item['abstract']))
            else:
                position = 300
                while item['abstract'][position] != ' ':
                    position+=1
                if position+1 == len(item['abstract']):
                    docid_info[docid].append(item['abstract'])
                else:
                    docid_info[docid].append(item['abstract'][:position]+' ...')
            #################End the process for docinfo#################

            #################Start the process for wordsRepo (inverted index)###########
            for term_pos,term in enumerate(content):
                if term[0] in lower_letters:
                    if term not in wordsRepo[term[0]].keys():
                        wordsRepo[term[0]][term]={}
                    if docid not in wordsRepo[term[0]][term].keys():
                        wordsRepo[term[0]][term][docid]=[term_pos]
                    else:
                        wordsRepo[term[0]][term][docid].append(term_pos)
                else:
                    if term not in wordsRepo['num'].keys():
                        wordsRepo['num'][term]={}
                    if docid not in wordsRepo['num'][term].keys():
                        wordsRepo['num'][term][docid]=[term_pos]
                    else:
                        wordsRepo['num'][term][docid].append(term_pos)
              #############End the process for wordsRepo#############
    return wordsRepo, docid_info


def write_index_to_disk(wordsRepo):
    '''
    Process our 'wordsRepo' to an inverted index.
    Then save the inverted index as a json file, so we can easily load it from disk as dictionary
    '''
    inverted_index = {}
    for single_part in wordsRepo.values():
        inverted_index.update(single_part)
    with open('processed_data/index.json', 'w',encoding='utf-8') as f:
        json.dump(inverted_index,f)

def write_docinfo_into_disk(docid_info):
    '''    
    Write the dictionary 'docid_info' into disk as a json file
    '''
    with open('processed_data/docid_info.json', 'w',encoding='utf-8') as f:
        json.dump(docid_info, f)

def write_numbers_of_docs_into_disk(docid_info):
    '''    
    Write the number of documents into disk as txt file
    The reason why I do this is because I think we don't need to calculate the number while running our system,
    and it's easy for us when updating our datasets. 
    '''
    N = len(docid_info.keys())
    with open('processed_data/num_of_docs.txt','w',encoding='utf-8') as f:
        f.write(str(N))


filepath = 'datasets/biopapers_sample_w_abstract.jsonl'
wordsRepo, docid_info = create_wordsRepo_docid_info(filepath)
write_index_to_disk(wordsRepo)
write_docinfo_into_disk(docid_info)
write_numbers_of_docs_into_disk(docid_info)
print('Builder is finished')