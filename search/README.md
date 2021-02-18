## Main code structure
There are two files we need to run for the whole process:
1. preprocess.py: This file contains functions related to pre-process.
2. inverted_index: This file contains functions used to create inverted index file. The structure of the inverted index written to disk is dict {'term':{'doc_id':[position1,position2]}}
3. bool.py: This file contains functions used to do the Boolean search.
4. tfidf.py: This file contains functions used to do the TFIDF rank search.
5. main.py: Run this file to start the information retrieval system.


## Dataset
The test dataset can be downloaded from the following link:
```
https://uoe-my.sharepoint.com/:f:/r/personal/s2042303_ed_ac_uk/Documents/datasets?csf=1&web=1&e=WeLiHG
```
Make sure the dataset file is in the folder named 'datasets'.

If you want to change the dataset, you need to change the value of the variable 'source_file_path' in main.py.
## Run
Run the file 'main.py'.
If this is the first time to run the file, it will firstly generate the inverted index file. After the first time, it will directly start search function.

## Later work
About changing the method to vectorization, all processes related to inverted index creation is in the file builder.py. After leo and me finish it, I will adjust the code of other functions according to the updated index's structure to make our system run without problem.

#### There are still many places needed to improve, so I am still working on this. Sorry about some misunderstanding variable or function names. Please feel free to improve and change the code and correct mistakes :)

#### Thanks a lot!


