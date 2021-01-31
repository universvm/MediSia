## There are two files we need to run for the whole process
1. builder.py: We could run this file to generate our json file of inverted index and some other files. These files should be generated before starting our system.
2. main.py: If we run this file, information retrival system will start. For now, it only offer two functions: Boolean (AND, OR, NOT AND, NOT OR) and TFIDF.


#### If you just want to see the demo and the result, You just need to run the main.py. No need to run builder.py since I have kept the generated files. 

#### If you want to change the dataset, remember to change the value of the variable 'filepath' which is at the bottom of builder.py, then run builder.py firstly to generate updated files.

## Later work
About changing the method to vectorization, all processes related to inverted index creation is in the file builder.py. After leo and me finish it, I will adjust the code of other functions according to the updated index's structure to make our system run without problem.

#### There are still many places needed to improve, so I am still working on this. Sorry about some misunderstanding variable or function names. Please feel free to improve and change the code and correct mistakes :)

#### Thanks a lot!


