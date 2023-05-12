To run the project on your pc you should have following for the basic setup:

1. Install python 3.9.* on your pc from
	https://www.python.org/downloads/release/python-3911/

2. Install pytorch if you have cpu only system select cpu otherwise choose cuda 11.7 or    similar if you have a GPU from
	https://pytorch.org/

3. Install all libraries mentioned in the requirements.txt file.
   Note: you might get an error installing libraries using requirements.txt file then 
   you will just ignore that file and install manually by seeing all imports in both 
   python scripts i.e., backend.py and voicebot.py
   
4. Download the necessary files to the root directory of the app 
	ClassesSentimentModel.tar.gz    --> https://mega.nz/file/skFV3LxI#T4uYyXY_6Cr_-RZVaYVMl51PZSdNhLt72wQYDn5UVcM
	DomainSentimentalModel.tar.gz   --> https://mega.nz/file/ok0HkbJa#RsblNFVp7Mf_BdfpThoKA5ZOSX3h1QNd3zkmEF1I2vY
	model.tar.gz                    --> https://mega.nz/file/E1F3GKBI#-zZFdfgFVfQMAHSHsTmZTJgJKx7LC3PhrOGmgymNeFg

5. After performing above steps and you received no error between them now you can unzip
   tar.gz files by using winrar or by cmd command.
	
	(a). If you are using winrar then just right click on each of the tar.gz file
	     and press right click. Choose option Extract Here and voila you are ready to go.
	(b). If you want to use cmd open Windows file Explorerthen goto the root folder of the application which will be /voicebot. 
	     Click on the directory toolbar and write cmd and hit enter. After that put command 
	     "tar -xzvf model.tar.gz", and hit enter
 	     then "tar -xzvf ClassesSentimentModel.tar.gz", and hit enter 
	     then "tar -xzvf DomainSentimentalModel.tar.gz" and hit enter

6. Now from your IDE goto the the backend.py and run. you will see a 127.0.0.1 link showing. Click this link and you wil be redirected to the browser. Enjoy the App    Now!!!
