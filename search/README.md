## There are two files we need to run for the whole process
1. builder.py: We could run this file to generate our json file of inverted index and some other files. These files should be generated before starting our system.
2. main.py: If we run this file, information retrival system will start. For now, it only offer two functions: Boolean (AND, OR, NOT AND, NOT OR) and TFIDF.


#### (1) If you just want to see the demo and the result, please download the generated data from the link:
```
https://uoe-my.sharepoint.com/:f:/r/personal/s2042303_ed_ac_uk/Documents/processed_data?csf=1&web=1&e=1wGSxy
```
#### Download the folder to the current directory, then You just need to run the main.py and no need to run builder.py. 

#### (2) If you want to change the dataset, remember to change the value of the variable 'filepath' which is at the bottom of builder.py, then run builder.py firstly to generate updated files.

#### For the generated data files, the test dataset is a 300-line jsonlines file. The link of this dataset folder is as below:
```
https://uoe-my.sharepoint.com/:f:/r/personal/s2042303_ed_ac_uk/Documents/datasets?csf=1&web=1&e=WeLiHG
```

## Later work
About changing the method to vectorization, all processes related to inverted index creation is in the file builder.py. After leo and me finish it, I will adjust the code of other functions according to the updated index's structure to make our system run without problem.

#### There are still many places needed to improve, so I am still working on this. Sorry about some misunderstanding variable or function names. Please feel free to improve and change the code and correct mistakes :)

#### Thanks a lot!

