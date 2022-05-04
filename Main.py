#Moudle Imports
import re
import tkinter
import tweepy
import tkinter as tk
from tkinter import*
import tkinter.messagebox
import configparser
import json
import pandas as pd
from datetime import datetime
import os
import sys

#########################################
############ API Access Keys ############
#########################################

#reading the config file
config = configparser.ConfigParser()
config.read('config.ini')

#Assigning the API tokens
api_key = config['Twitter'] ['api_key']
api_secret = config['Twitter'] ['api_secret']
access_token = config['Twitter'] ['access_token']
access_token_secret = config['Twitter'] ['access_token_secret']

#Linking the tokens to Tweepy
auth = tweepy.OAuthHandler(api_key,api_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#global variables
SearchWord = None
FullText = list()
Pcount = 0
Ncount = 0
PosPercentage = 0
NegPercentage = 0
limit = 400


##############################################
############ Twitter Search Query ############
##############################################

def SearchQuery(SearchWord): #function for searching the users keyword
    global FullText, limit
    
    filterRT = "-filter:retweets" #(this filter is a Twitter API operator)
    KeyWord = SearchWord + filterRT #adding the filter operator to the searchword
    tweets = tweepy.Cursor(api.search_tweets, q=KeyWord, count=limit, #same search query listed above, The search query has to 
                        tweet_mode='extended', lang='en').items(limit) #be written with every use in a function
    for tweet in tweets: #for all of the tweets found
        ft = tweet.full_text #ft = that tweet in full text
        FullText.append(ft) #append the global list FullText and add ft to it
                            #this way FullText will be a list that contains multiple tweets like so ["Tweet1","Tweet2", etc..]

    return SearchWord


###########################################
############ Handler Functions ############
###########################################

f = open('wordList.json') #opening the json file that contains the wordlist
wordList = json.load(f) #loading up the wordlist and linking it to the variable wordList


def PosCount():
    global Pcount #Postive count variable
    global FullText
    Pcount = 0
    Place = -1 #this variable is set to give every word a number and navigate through them (this is used for filtering purposes)
    for i in FullText: #for all every tweet in the search query
        ToLower = i.lower() #turning the input into lower case as the words in wordlist are all lower case
        splitter = ToLower.split() #spliting the tweet word by word
        for words in splitter: #for all of the words in every tweet
            Place +=1 #add +1 to place 
            if words in wordList['Positive']: #if it is in the positive wordlist
                Place -=1 #taking one out from place (this is to check the word before positive to ensure its not a reverse term)
                Pcount += 1 #add one to the count
                BeforePositive = splitter[Place]
                if BeforePositive in wordList['ReverseTerms']: #if BeforePositive is a reverse term like "Not"
                    Pcount -= 1 #take away the positive count ~ this is done so that phrases like "Im not Happy" get exterminated
        Place = -1   #setting back the place to the defult value
    return Pcount #return the value of the count

#Review the comments from Poscount, this below is the same function but for the Negative words count
def NegCount():
    global FullText, Ncount
    Place = -1
    for i in FullText: 
        ToLower = i.lower()
        splitter = ToLower.split() 
        for words in splitter: 
            Place +=1
            if words in wordList['negative']: 
                Place -=1
                Ncount += 1 #add one to the count
                BeforePositive = splitter[Place]
                if BeforePositive in wordList['ReverseTerms']:
                    Ncount -= 1
        Place = -1         
    return Ncount 

##############################################
############ Classifier Functions ############
##############################################

def Classifier(): 
    global NegPercentage, PosPercentage, Pcount, Ncount #importing global variables
    TotalWords = Pcount + Ncount #assiging a variable to add the counts together and use it to calculate the percentages
    if TotalWords == 0:
        NoResultsError()
    Ppw = 100/ TotalWords #Percentage Per Word = Ppw
    NegPercentage = float(Ppw * Ncount)  # Negative percentage = percentage per word * Negative count
    PosPercentage =  float(Ppw * Pcount) # Positive percentage = percentage per word * Positive count
    return NegPercentage, PosPercentage  #returning the values to the global variables


def SaveClassification(): #This function is to SAVE the results of the classification
    global SearchWord, limit #importing global variables

    DateNTime = datetime.now() #using an imported module to get the time and date of the user (the reasoning will be explained below)
    DnT = DateNTime.strftime(" (%Y-%m-%d %H-%M-%S)") #choosing the format of the date and time data 

    columns = ['Time', 'User', 'Tweet', 'Positive Words', 'Negative Words'] #setting up colomuns for the Csv file that would be saved
    data = []

    filterRT = "-filter:retweets" # (this filter is a Twitter API operator)
    KeyWord = SearchWord + filterRT #adding the filter operator to the searchword
    tweets = tweepy.Cursor(api.search_tweets, q=KeyWord, count=limit, #same search query listed above, The search query has to 
                        tweet_mode='extended', lang='en').items(limit) #be written with every use in a function

    for tweet in tweets: #for every tweet in the tweets imported
        Nlist = list() #creating a list for the Negative words found within the tweet
        Plist = list() #creating a list for the Positive words found within the tweet
        FullText = tweet.full_text #FUllTEXT is the tweet imported in full text
        splitter = FullText.split() #splitting the tweets
        for words in splitter:
            if words in wordList['negative']: #if it is in the negative wordlist add it to Nlist
                Nlist.append(words)
            elif words in wordList['Positive']: #if it is in the Positive wordlist add it to Nlist
                Plist.append(words)
        
        data.append([tweet.created_at, tweet.user.screen_name, tweet.full_text, Plist, Nlist]) #adding the variables to the coloumns
        df = pd. DataFrame(data, columns = columns)
        df.to_csv(SearchWord + str(DnT) + '.csv') #file name consisting of the search word and the date and time
                                                #The date&Time are used so that if the user searches two times using the same keyword
                                                #at different times, they would be able to identify both results using this data
    tkinter.messagebox.showinfo(title='Saving Done!', message='The file has been saved in the programs directory!') #display message 
                                                                                                #to notify the user of operation success


##########################################
############ Window Functions ############
##########################################

def ResultsWindow(): # a window function for results
    global ResWinLogo #importing a global variable
    ResWin = Toplevel() #using a tkinter operator to create the window 
    ResWin.title('Results') #naming the title of the window 
    ResWinCanvas = tk.Canvas(ResWin, height=700, width= 800).pack() #setting the diementions of the window

    #importing the tools's logo on the screen
    ResWinLogo = tk.PhotoImage(file='logo.png') 
    ResWinLogoLbl = tk.Label(ResWin, image = ResWinLogo)
    ResWinLogoLbl.place(relx = 0.1, rely = 0.01)

    #importing text
    ResTextLabel = tk.Label(ResWin, text= "The classification results for your search is:", font=("Arial Rounded MT Bold", 14))
    ResTextLabel.place(relx = 0.26, rely = 0.4)
    
    #importing the results in a textbox
    TextBox = tk.Text(ResWin, height=15, width=50, bg='gray', font=("Arial Rounded MT Bold", 12))
    TextBox.insert(INSERT, 'Positivity = %')
    TextBox.insert(INSERT,PosPercentage)
    TextBox.insert(INSERT, '\nNegativity = %')
    TextBox.insert(INSERT,NegPercentage)
    TextBox.insert(INSERT, '\nPositive Words Found = ')
    TextBox.insert(INSERT,Pcount)
    TextBox.insert(INSERT, '\nNegative Words Found = ')
    TextBox.insert(INSERT,Ncount)
    TextBox.place(relx = 0.17, rely = 0.45)

    def on_closing():
        restart()


    #creating a button to save the results
    SaveResultsBtn = tk.Button(ResWin, text='Save Classification', bg='#098107', fg='white', font=("Arial Rounded MT Bold", 14), 
    command =lambda: SaveClassification())
    SaveResultsBtn.place(relx= 0.2, rely= 0.85 ,height=40, width=200)

    #creating a button to view the tweets
    ViewTweetsBtn = tk.Button(ResWin, text='View Tweets', bg='#098107', fg='white', font=("Arial Rounded MT Bold", 14), 
    command =lambda: [ViewTweets()])
    ViewTweetsBtn.place(relx= 0.51, rely= 0.85 ,height=40, width=200)

    ResWin.protocol("WM_DELETE_WINDOW", on_closing)
    ResWin.mainloop()



def ViewTweets(): #a function for when the user presses the ViewTweets Button
    global FullText, ViewTwtLogo
    i = 1
    ViewTwtsWin = Toplevel() #using a tkinter operator to create the window 
    ViewTwtsWin.title('Tweets') #setting up the title of the window
    ViewTwtsWinCanvas = tk.Canvas(ViewTwtsWin, height=700, width= 800).pack() #setting the diementions of the window 

    #importing the tools's logo on the screen
    ViewTwtLogo = tk.PhotoImage(file='logo.png')
    ViewTwtLogoLbl = tk.Label(ViewTwtsWin, image = ViewTwtLogo)
    ViewTwtLogoLbl.place(relx = 0.1, rely = 0.01)

    #importing text
    ViewTwtLbl = tk.Label(ViewTwtsWin, text= "The classified tweets:", font=("Arial Rounded MT Bold", 14))
    ViewTwtLbl.place(relx = 0.02, rely = 0.4)

    #importing a textbox for the tweets to be in
    ViewTwtsInnerTextBox = tk.Text(ViewTwtsWin, height=25, width= 98, bg = 'gray', font=("Arial Rounded MT Bold", 10))

    #adding all of the tweets in the textbox
    for n in FullText:
        ViewTwtsInnerTextBox.insert(INSERT, i)
        ViewTwtsInnerTextBox.insert(INSERT, ":  ")
        ViewTwtsInnerTextBox.insert(INSERT, n)
        ViewTwtsInnerTextBox.insert(INSERT, "\n\n")
        i +=1
    
    ViewTwtsInnerTextBox.place(rely = 0.445, relx = 0.012)


def restart():
    os.execl(sys.executable, sys.executable, *sys.argv)



###########################################
############ Message Functions ############
###########################################

#error message for entry when its empty
def EntryCheck(entry):
    global SearchWord, Pcount, Ncount, PosPercentage, NegPercentage
    SearchWord = entry

    if len(entry) < 1:
        tkinter.messagebox.showerror(title="Search Error!", message="Please write your desired word in the search box")
    else: #if theres no error then run the following functions:
        SearchQuery(SearchWord)
        PosCount() 
        NegCount() 
        Classifier() 
        ResultsWindow()

def NoResultsError():
    tkinter.messagebox.showerror(title="No Results Error!", message="No Results found!")

#Help Message
def HelpMsg():
    tkinter.messagebox.showinfo(title='Help', message='To run the toolyou have to type your desired word \nor hashtagin the box.\n\n Please note that for hashtags you MUST\n write a hashtag Sign "#" before your desired hashtag.')

#info message that gives a background on what the tools is
def InfoMsg():
    tkinter.messagebox.showinfo(title='Info', message='HFTCT is a tool that classifies tweets on Twitter\nand reports back a summary of opinions in two categories Positive & Negative.')


##################################
############ GUI Code ############
##################################

#a function for the main window, this window is the entrance that the user would use to nevigate through all of HFTCT's functionalities
def HFTCTMainWindow(): 
    global Pcount, Ncount, PosPercentage, NegPercentage

    MainWindow= tk.Tk() #importing global variables
    MainWindow.title('Health-Focused Text Classification Tool (HFTCT)') #setting up the title of the window
    MWcanvas = tk.Canvas(MainWindow, height=700, width= 800).pack() #setting up the size of the window
    MWFrame= tk.Frame(MainWindow, height =300, width = 3, bg ='#1a222a').place(relx = 0.18, rely= 0.45) #this is a rectangle used for 
                                                                                                        #decoration purposes

    #importing the tool's logo
    Logo = tk.PhotoImage(file='logo.png')
    Logo_Lable = tk.Label(MainWindow, image = Logo)
    Logo_Lable.place(relx = 0.1, rely = 0.01)

    #adding Help button (pressing on this button would run the help function above)
    HelpBtn = tk.Button(MainWindow, text="Info", bg ='#098107', fg='White',font=("Arial Rounded MT Bold", 14), command=lambda: InfoMsg())
    HelpBtn.place(relx= 0.03, rely= 0.48 ,height=40, width=100)

    #adding INFO button (pressing on this button would run the Info function above)
    InfoBtn = tk.Button(MainWindow, text="Help", bg ='#098107', fg='White',font=("Arial Rounded MT Bold", 14), command=lambda: HelpMsg())
    InfoBtn.place(relx= 0.03, rely= 0.55 ,height=40, width=100)

    #Start Classification Button (pressing this button run the EntryCheck function which checks if the user inputed anything unvalid for a search)
    MWbutton = tk.Button(MainWindow, text="Start Classification", bg ='#098107', fg='White',font=("Arial Rounded MT Bold", 14), 
    command= lambda:[EntryCheck(KeyWordEntry.get())]) #### Here ###
    MWbutton.place(relx= 0.492, rely= 0.75 ,height=40, width=200)

    #Lables to import Text on the main window
    KeyWordLbl = tk.Label(MainWindow, text= "Search:", font=("Arial Rounded MT Bold", 14)).place(relx= 0.32, rely= 0.648)
    InfoLbl =  tk.Label(MainWindow, 
    text= "For a keyword search, type your desired word, for a hashtag search\n use a hashtag sign and type your desired hashtag in the searchbox below", 
    font=("Arial Rounded MT Bold", 13)).place(relx= 0.22, rely= 0.5)

    #importing an entry box (this is a box to take the user input)
    KeyWordEntry = tk.Entry(MainWindow, bg = 'gray', font= ('Arial', 12))
    KeyWordEntry.place(relx= 0.43, rely= 0.645 ,height=40, width=300)
    MainWindow.mainloop() #looping this window as it is the main window and it has to always be running


HFTCTMainWindow() #funciton call for the main window

