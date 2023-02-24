import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image 

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import matplotlib
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk) 
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import os
import googleapiclient.discovery 

import re
import time

import io
import webbrowser
from urllib.request import urlopen 

root = tk.Tk()
style = ttk.Style()
style.theme_use('clam')

root.geometry("1000x700")
root.title("YouTube Comments Sentiment Analyser")
root.resizable(False, False)

# Global Variables
channelId = 0
channelAvatar = tk.PhotoImage()
channelName = ""
channelSubscriberCount = 0
validID = False
videoIdDict = {}
videoCommentsDict = {}
videoStatsDict = {}
videoVarianceDict = {}
videoAvgSentDict = {}
videoNumber = ""
graphDisplayed = False
quotaUsed = 0
selectMode = "number"

# Helper Functions
def replaceFrame(frame1, frame2, *args):
    frame1.forget()
    frame2.pack(expand = True, fill = tk.BOTH)

def closeApplication():
    root.destroy()

# Input: Channel ID of the user
# Calls the YouTube API and stores the channel Id, channel avatar, channel name and subscriber count
def getChannelData(userId):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "INSERT YOUR KEY HERE"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    request = youtube.channels().list(
        part="snippet,statistics",
        id = userId
    )
    try: 
        response = request.execute()
        name = response['items'][0]['snippet']['title']
        subCount = response['items'][0]['statistics']['subscriberCount']

        imgUrl = response['items'][0]['snippet']['thumbnails']['medium']['url']
        imgData = urlopen(imgUrl).read()
        imgObj = ImageTk.PhotoImage(Image.open(io.BytesIO(imgData)).resize((200,200)))
    
        global channelAvatar
        global channelName
        global channelSubscriberCount
        global validID
        global channelId
        channelId = userId
        channelAvatar = imgObj
        channelName = name
        channelSubscriberCount = subCount
        validID = True
    except Exception as e: print(e)
    # except: 
    #     tk.messagebox.showerror("Unrecognised Channel ID", "The Channel ID you have entered is unrecognised.")

# Main Frames
# The startup screen background for the application
welcomeFrame = tk.Frame(root)
welcomeFrame.pack(expand = True, fill = tk.BOTH)
welcomeFrameBgObj = ImageTk.PhotoImage(Image.open('welcome_background.jpg'))
welcomeCanvas = tk.Canvas(welcomeFrame)
welcomeCanvas.pack(expand = True, fill = tk.BOTH)
welcomeCanvas.create_image(0, 0, image = welcomeFrameBgObj, anchor = tk.NW)

# The home screen background for the application
homeFrame = tk.Frame(root)
homeFrameBgObj = ImageTk.PhotoImage(Image.open('home_background.jpg'))
homeFrameCanvas = tk.Canvas(homeFrame, bd = 0, highlightthickness = 0, relief='ridge')
homeFrameCanvas.pack(expand = True, fill = tk.BOTH)
homeFrameCanvas.create_image(0, 0, image = homeFrameBgObj, anchor = tk.NW)

# Home Screen Frames, Widgets & Functions
# Call the YouTube API and get all video Ids correspoinding to the user
def getAllVideos():
    global channelId
    global videoIdDict
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "INSERT YOUR KEY HERE"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    # Get playlist ID of the uploads playlist
    requestPlaylistId = youtube.channels().list(
        part="contentDetails",
        id = channelId
    )
    playlistIdResponse = requestPlaylistId.execute()
    playlistId_ = playlistIdResponse['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    #A dictionary to store video Ids {"YYYY-MM-DD" : a video id}
    videoIdDict = {}

    nextPageTokenExists = True
    nextPageToken = ""

    time1 = time.time()

    while nextPageTokenExists == True:
        # If this is the first set of videos to be called.
        if nextPageToken == "":
            # Call the first batch of uploads.
            requestPlaylistItems = youtube.playlistItems().list(
                part = "contentDetails",
                playlistId = playlistId_
            )
            playlistItemsResponse = requestPlaylistItems.execute()
            playlistItems = playlistItemsResponse['items']
            # Store each video id in the batch in the videoIdDict 
            for playlistItem in playlistItems:
                videoIdDict[playlistItem['contentDetails']['videoPublishedAt'][0 : 10]] = playlistItem['contentDetails']['videoId']
            # If there is no next page token, there are no more videos to be called, exit loop.
            if 'nextPageToken' not in playlistItemsResponse:
                nextPageTokenExists = False
            # Else if there is a next page token, store this and use it for the next loop.
            else:
                nextPageToken = playlistItemsResponse['nextPageToken']
        else:
            # Call the next batch of videos using the next page token.
            requestPlaylistItems = youtube.playlistItems().list(
                part = "contentDetails",
                playlistId = playlistId_,
                pageToken = nextPageToken
            )
            playlistItemsResponse = requestPlaylistItems.execute()
            playlistItems = playlistItemsResponse['items']
            # Store each video id in the batch in the videoIdDict 
            for playlistItem in playlistItems:
                videoIdDict[playlistItem['contentDetails']['videoPublishedAt'][0 : 10]] = playlistItem['contentDetails']['videoId']
            # If there is no next page token, there are no more videos to be called, exit loop.
            if 'nextPageToken' not in playlistItemsResponse:
                nextPageTokenExists = False
            # Else if there is a next page token, store this and use it for the next loop.
            else:
                nextPageToken = playlistItemsResponse['nextPageToken'] 
        print("Videos Aqcuired: " + str(len(videoIdDict.keys())), end = "\r")
    time2 = time.time()
    print("\n")
    print("Time taken: " + str(round(time2 - time1, 3)) + "s")

# Input: A video Id
# Call the YouTUbe API and get all top level comments posted under the video
def analyseVideoComments(id):
    global videoCommentsDict
    global videoNumber
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "INSERT YOUR KEY HERE"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=id,
        maxResults = 100
    )
    response = request.execute()
    commentContainer = response['items']

    # A dictionary to store comments and their sentiment {"Comment" : sentiment}
    commentsWithScores = {}

    analyser = SentimentIntensityAnalyzer()

    nextPageTokenExists = True
    nextPageToken = ""

    counter = 0

    # If there is a next page token and the number of comments analysed has not yet surpassed 2000
    while (nextPageTokenExists == True) and (counter < 2000):
        if nextPageToken == "":
            # Call the first batch of comments.
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=id,
                maxResults = 100
            )
            response = request.execute()
            commentContainer = response['items']
            # Filter each comment to remove new line characters and analyse the comment using VADER
            # Then store it in commentsWithScores
            for comment in commentContainer:
                counter = counter + 1
                filteredComment = comment['snippet']['topLevelComment']['snippet']['textOriginal'].replace("\n", " ")
                commentsWithScores[filteredComment] = analyser.polarity_scores(filteredComment)['compound']
                print("Video: " + videoNumber + " Number of comments analysed: " + str(counter), end = "\r")
            # If there is no next page token, there are no more comments to be called, exit loop.
            if 'nextPageToken' not in response:
                nextPageTokenExists = False
            # Else if there is a next page token, store this and use it for the next loop.
            else:
                nextPageToken = response['nextPageToken']
        else:
            # Call the next batch of comments using the next page token.
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=id,
                pageToken = nextPageToken,
                maxResults = 100
            )
            response = request.execute()
            commentContainer = response['items']
            # Filter each comment to remove new line characters and analyse the comment using VADER
            # Then store it in commentsWithScores
            for comment in commentContainer:
                counter = counter + 1
                filteredComment = comment['snippet']['topLevelComment']['snippet']['textOriginal'].replace("\n", " ")
                commentsWithScores[filteredComment] = analyser.polarity_scores(filteredComment)['compound']
                print("Video: " + videoNumber + " Number of comments analysed: " + str(counter), end = "\r")
            # If there is no next page token, there are no more comments to be called, exit loop.
            if 'nextPageToken' not in response:
                nextPageTokenExists = False
            # Else if there is a next page token, store this and use it for the next loop.
            else:
                nextPageToken = response['nextPageToken']
    #Store the dictionary of comments into the videoCommentsDict for the relevent video Id key.
    videoCommentsDict[id] = commentsWithScores
    return commentsWithScores
    
# Input: dictionary of comments with scores
# return a dictionary of the average sentiment and variance of the comment scores.
def getSentimentData(commentDict):
    sentimentData = {}
    if len(commentDict.keys()) == 0:
        sentimentData["average"] = 0
        sentimentData["variance"] = 0
        return sentimentData
    else:
        average = 0
        for comment in commentDict.keys():
            average = average + commentDict[comment]
        average = average / len(commentDict.keys())
        sentimentData["average"] = round(average, 2)
        variance = 0
        for comment in commentDict.keys():
            variance = variance + ((commentDict[comment] - average) ** 2)
        variance = variance / len(commentDict.keys())
        sentimentData["variance"] = round(variance, 2)
        return sentimentData

# Input: video Id of the corresponding video
# Calls the YouTube API and returns a dictionary containing statistics about the corresponging video
def getVideoStats(videoId):
    global videoStatsDict
    # If the video statistics have already been created and stored, return this.
    if videoId in videoStatsDict.keys():
        return videoStatsDict[videoId]
    else:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = "INSERT YOUR KEY HERE"

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = DEVELOPER_KEY)

        request = youtube.videos().list(
            part="snippet,statistics",
            id = videoId
        )
        response = request.execute()

        videoStats = {}

        thumbnailUrl = response['items'][0]['snippet']['thumbnails']['medium']['url']
        thumbnailData = urlopen(thumbnailUrl).read()
        thumbnailImg = ImageTk.PhotoImage(Image.open(io.BytesIO(thumbnailData)).resize((269,151)))
        videoStats["img"] = thumbnailImg
        videoStats["views"] = response['items'][0]['statistics']['viewCount']
        videoStats["likes"] = response['items'][0]['statistics']['likeCount']
        videoStatsDict[videoId] = videoStats
        return videoStatsDict[videoId]


# Input: the video id and the type of comment, either "positive" or "negative"
# Opens up a new window which displays either the most positive or most negative comment
def openCommentInfo(videoId, type):
    global videoCommentsDict
    commentWindow = tk.Toplevel(root)
    commentWindow.geometry("+200+200")
    
    commentWindow.attributes('-topmost', True)
    commentWindow.resizable(False, False)

    # Source: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
    # This removes emojis from the comment string as Tkinter cannot render emojis.
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U0001F1F2-\U0001F1F4"  # Macau flag
        u"\U0001F1E6-\U0001F1FF"  # flags
        u"\U0001F600-\U0001F64F"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U0001F1F2"
        u"\U0001F1F4"
        u"\U0001F620"
        u"\u200d"
        u"\u2640-\u2642"
        "]+", flags=re.UNICODE)

    if type == "positive":
        mostPositive = max(videoCommentsDict[videoId], key = videoCommentsDict[videoId].get)
        formatted = emoji_pattern.sub(r'', mostPositive)
        tk.Label(commentWindow, text = "Most Positive Comment (Rating: " + str(videoCommentsDict[videoId][mostPositive]) + "):" + "\n\n" + formatted, font = ("Arial", 16), wraplength = 400).pack()
    else:
        leastPositive = min(videoCommentsDict[videoId], key = videoCommentsDict[videoId].get)
        formatted = emoji_pattern.sub(r'', leastPositive)
        tk.Label(commentWindow, text = "Least Positive Comment (Rating: " + str(videoCommentsDict[videoId][leastPositive]) + "):" + "\n\n" + formatted, font = ("Arial", 16), wraplength = 400).pack()

# Input: the video Id of the corresponding video
# Opens the video using the user's default browser
def openVideo(videoId):
    url = "https://youtu.be/" + str(videoId)
    webbrowser.open_new(url)

# Input: the video Id of the corresponding video
# Opens up a new window displaying the video thumbnail and various statistics about the video
def openVideoStats(videoId):
    global videoCommentsDict
    global videoVarianceDict
    global videoAvgSentDict
    statsWindow = tk.Toplevel(root)
    statsWindow.geometry('700x420')
    statsWindow.geometry("+100+100")
    
    statsWindow.attributes('-topmost', True)
    statsWindow.resizable(False, False)

    videoStatsDict = getVideoStats(videoId)
    videoStatsCanvas = tk.Canvas(statsWindow)
    videoStatsCanvas.pack(expand = True, fill = tk.BOTH)
    videoStatsCanvas.create_image(0, 0, image = videoStatsBgObj, anchor = tk.NW)
    videoStatsCanvas.create_image(35, 35, image = videoStatsDict["img"], anchor = tk.NW)
    print(videoStatsDict["views"])
    videoStatsCanvas.create_text(45, 241, text = "Views: " + videoStatsDict["views"], font = ("Arial", 20), fill = "black", anchor = tk.NW)
    videoStatsCanvas.create_text(45, 271, text = "Likes: " + videoStatsDict["likes"], font = ("Arial", 20), fill = "black",anchor = tk.NW)
    videoStatsCanvas.create_text(45, 301, text = "Analysed comments: " + str(len(videoCommentsDict[videoId].keys())), font = ("Arial", 20), fill = "black",anchor = tk.NW)
    videoStatsCanvas.create_text(45, 321, text = "(Only includes top level comments)", font = ("Arial", 10), fill = "black",anchor = tk.NW)
    videoStatsCanvas.create_text(45, 331, text = "Sentiment Variance: " + str(videoVarianceDict[videoId]), font = ("Arial", 20), fill = "black",anchor = tk.NW)
    videoStatsCanvas.create_text(45, 361, text = "Average Sentiment: " + str(videoAvgSentDict[videoId]), font = ("Arial", 20), fill = "black",anchor = tk.NW)
    positiveButton = ttk.Button(videoStatsCanvas, text = "View Most Positive Comment", command = lambda : openCommentInfo(videoId, "positive"), width = 29)
    negativeButton = ttk.Button(videoStatsCanvas, text = "View Least Positive Comment", command = lambda : openCommentInfo(videoId, "negative"), width = 29)
    openUrlButton = ttk.Button(videoStatsCanvas, text = "Open Video In Browser", command = lambda : openVideo(videoId), width = 29)
    positiveButton.place(x = 363, y = 60)
    negativeButton.place(x = 363, y = 100)
    openUrlButton.place(x = 363, y = 330)
    # If the video has no comments posted, disable these buttons.
    if bool(videoCommentsDict[videoId]) == False:
        positiveButton["state"] = "disabled"
        negativeButton["state"] = "disabled"

# Input: X (an array of upload dates), Y (an array of average sentiments),
#       the dictionary containing the upload dates and video Ids of the analysed videos.
# Displays a graph of average sentiments over upload dates and creates buttons to access each video.
def displayGraph(x, y, videoIds):
    global sentimentGraph
    global dateFrame
    global graphDisplayed
    graphDisplayed = True
    sentimentGraph = tk.Frame(homeFrame, width = 900, height = 435)
    sentimentFigure = Figure(figsize = (7.6, 5.19), dpi = 100)
    sentimentLine = sentimentFigure.add_subplot(111)
    sentimentCanvas = FigureCanvasTkAgg(sentimentFigure, master = sentimentGraph)
    sentimentCanvasToolBar = NavigationToolbar2Tk(sentimentCanvas, window = sentimentGraph) 
    sentimentLine.set_ylabel('Average Sentiment')
    sentimentLine.set_xlabel('Upload Date')
    sentimentLine.axhline(y=0, color='r', linestyle='-')
    sentimentLine.axhspan(0, 1, facecolor='g', alpha=0.2)
    sentimentLine.axhspan(-1, 0, facecolor='r', alpha=0.2)
    sentimentLine.plot(x, y, marker='o')
    for i in range(len(x)):
        sentimentLine.text(x[i], y[i], round(y[i], 2))
    sentimentCanvas.draw()
    sentimentCanvasToolBar.update()
    sentimentGraph.place(x = 275, y = 250)
    sentimentCanvas.get_tk_widget().pack(expand = True, fill = tk.BOTH)

    dateFrame = tk.Frame(homeFrame, width = 150, height = 425)
    dateCanvas = tk.Canvas(dateFrame, width = 115, height = 425, bd = 0, highlightthickness = 0, relief = 'ridge', bg = "white")
    dateCanvasScrollBar = tk.Scrollbar(dateFrame, orient = "vertical", command = dateCanvas.yview)
    buttonFrame = tk.Frame(dateCanvas)
    for date in videoIds.keys():
        ttk.Button(buttonFrame, text = date, command = lambda date = date: openVideoStats(videoIds[date])).pack()
    dateCanvas.create_window(0, 0, anchor = 'nw', window = buttonFrame)
    dateCanvas.update_idletasks()
    dateCanvas.configure(scrollregion = dateCanvas.bbox('all'), yscrollcommand = dateCanvasScrollBar.set)
    dateCanvas.pack(fill = 'both', expand = True, side = 'left')
    dateCanvasScrollBar.pack(fill = 'y', side = 'right')
    dateFrame.place(x = 845, y = 250)

# Input: starting date, ending date
# Returns a dictionary of video Ids that are within the date range.
def getVideoIdsWithinRange(date1, date2):
    global videoIdDict
    if date1 == "" and date2 == "":
        tk.messagebox.showerror("Missing Dates", "You have not entered any dates.")
    elif date1 == "":
        tk.messagebox.showerror("Missing Start Date", "You have not entered a start date.")
    elif date2 == "":
        tk.messagebox.showerror("Missing End Date", "You have not entered an end date.")
    else:
        if bool(re.match(r"[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", date1)) == False and bool(re.match(r"[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", date2)) == False:
            tk.messagebox.showerror("Incorrect Format", "The both dates are not in the form YYYY-MM-DD")
        elif bool(re.match(r"[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", date1)) == False:
            tk.messagebox.showerror("Incorrect Format", "The start date is not in the form YYYY-MM-DD")
        elif bool(re.match(r"[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", date2)) == False: 
            tk.messagebox.showerror("Incorrect Format", "The end date is not in the form YYYY-MM-DD")           
        elif date1 > date2:
            tk.messagebox.showerror("Incorrect Dates", "The end date is after the start date.")
        else:
            videoIds = {}
            for date in videoIdDict.keys():
                if date < date1:
                    break
                else: 
                    if date <= date2:
                        videoIds[date] = videoIdDict[date]
            if bool(videoIds) == False:
                tk.messagebox.showerror("No Videos", "There are no videos uploaded within this range.")
            else:
                return videoIds

# Input: The number of latest videos to be called.
# Returns a dictionary of video ids of the most recent number of videos
def getLatestVideos(number):
    global videoIdDict
    dates = videoIdDict.keys()
    videoIds = {}
    if len(dates) == 0:
        tk.messagebox.showerror("No Videos", "You have not uploaded any videos.")
    elif int(number) > len(dates):
        return videoIdDict
    else:
        counter = 1
        for date in dates:
            if counter > int(number):
                break
            else:
                videoIds[date] =  videoIdDict[date]
                counter = counter + 1
        return videoIds

# Input: starting date and ending date or the number of latest videos
# Gets the relevent videos selected by the user, analyses them and displays them on the graph.
def getAnalysisAcrossVideos(date1, date2, num):
    global selectMode
    global videoVarianceDict
    global videoAvgSentDict
    global videoNumber
    videoIds = {}
    if selectMode == "date":
        videoIds = getVideoIdsWithinRange(date1, date2)
    else:
        videoIds = getLatestVideos(num)
    uploadDates = []
    sentiment = []
    if videoIds is not None:
        counter = 0
        time1 = time.time()
        temp = 0.0
        # For every video Id in the dictionary, calculate its average sentiment and variance and store it in the relevent dictionaries.
        for date in videoIds.keys():
            counter = counter + 1
            videoNumber = str(counter) + "/" + str(len(videoIds.keys()))
            uploadDates.append(date)
            sentimentData = getSentimentData(analyseVideoComments(videoIds[date]))
            videoVarianceDict[videoIds[date]] = sentimentData["variance"]
            videoAvgSentDict[videoIds[date]] = sentimentData["average"] 
            sentiment.append(sentimentData["average"])
        time2 = time.time()
        print("\n")
        print("Time taken: " + str(round(time2 - time1, 3)) + "s")
        # Reverses the array to earliest upload first then displays the graph.
        displayGraph(uploadDates[::-1], sentiment[::-1], videoIds)
        homeMenuDateConfirm["state"] = "disabled"
        homeMenuNumConfirm["state"] = "disabled"
        homeMenuClearDate['state'] = "enable"
        homeMenuClearNum['state'] = "enable"

# Switch the panel to using date selection
def switchToDate():
    global selectMode
    selectMode = "date"
    frame = homeMenuFrames[0]
    frame.tkraise()

# Switch the panel to using latest number of videos selection
def switchToNum():
    global selectMode
    selectMode = "number"
    frame = homeMenuFrames[1]
    frame.tkraise() 

# Clear the graph from the screen and re enable confirm buttons
def _clear():
    global graphDisplayed
    graphDisplayed = False
    sentimentGraph.destroy()
    dateFrame.destroy()
    homeMenuDateConfirm["state"] = "enable"
    homeMenuNumConfirm["state"] = "enable"
    homeMenuClearDate['state'] = "disabled"
    homeMenuClearNum['state'] = "disabled"

# Return to the home screen and reset all values related to the previous user Id.
def restart():
    global validID
    global videoIdDict
    global videoCommentsDict
    global videoStatsDict
    global sentimentGraph
    global dateFrame
    global graphDisplayed

    validID = False
    videoIdDict = {}
    videoCommentsDict = {}
    videoStatsDict = {}
    homeFrameCanvas.delete("hello")
    homeFrameCanvas.delete("subs")
    if graphDisplayed == True:
        sentimentGraph.destroy()
        dateFrame.destroy()
    homeMenuDateConfirm["state"] = "enable"
    homeMenuNumConfirm["state"] = "enable"
    homeMenuClearDate['state'] = "disabled"
    homeMenuClearNum['state'] = "disabled"
    replaceFrame(homeFrame, welcomeFrame)

# Tkinter widgets to render the home screen
homeAvatarLabel1 = tk.Label(homeFrame, border = 0)
homeAvatarLabel1.place(x = 25, y = 250)

homeMenuSelectDateImg = ImageTk.PhotoImage(Image.open("home_selection_background_date.jpg"))
homeMenuSelectNumImg = ImageTk.PhotoImage(Image.open("home_selection_background_num.jpg"))
videoStatsBgObj = ImageTk.PhotoImage(Image.open('video_stats.jpg'))

homeMenuDateFrame = tk.Frame(homeFrame, width = 700, height = 200)
homeMenuDateFrame.place(x = 275, y = 25)
homeMenuDateFrameBg = tk.Label(homeMenuDateFrame, image = homeMenuSelectDateImg, borderwidth = 0)
homeMenuDateFrameBg.pack(expand = True, fill = tk.BOTH)

homeMenuStartDate = ttk.Entry(homeMenuDateFrame, width = 28)
homeMenuStartDate.place(x = 50, y = 90)
homeMenuEndDate = ttk.Entry(homeMenuDateFrame, width = 28)
homeMenuEndDate.place(x = 400, y = 90)
homeMenuDateConfirm = ttk.Button(homeMenuDateFrame, text = "Confirm", width = 10, command = lambda : getAnalysisAcrossVideos(homeMenuStartDate.get(), homeMenuEndDate.get(), None))
homeMenuDateConfirm.place(x = 202, y = 120)
homeMenuClearDate = ttk.Button(homeMenuDateFrame, text = "Clear", width = 10, command = lambda : _clear())
homeMenuClearDate.place(x = 400, y = 120)
homeMenuClearDate['state'] = "disabled"
homeMenuSwitchToNum = ttk.Button(homeMenuDateFrame, text = "Switch To Number Selection")
homeMenuSwitchToNum.place(x = 1, y = 169)

homeMenuNumFrame = tk.Frame(homeFrame, width = 700, height = 200)
homeMenuNumFrame.place(x = 275, y = 25)
homeMenuNumFrameBg = tk.Label(homeMenuNumFrame, image = homeMenuSelectNumImg, borderwidth = 0)
homeMenuNumFrameBg.pack(expand = True, fill = tk.BOTH)

numOptions = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
numVar = tk.StringVar(homeMenuNumFrame)
homeMenuNumSelect = ttk.OptionMenu(homeMenuNumFrame, numVar, numOptions[0], *numOptions)
homeMenuNumSelect.config(width = 25)
homeMenuNumSelect.place(x = 225, y = 85)
homeMenuNumConfirm = ttk.Button(homeMenuNumFrame, text = "Confirm", width = 10, command = lambda : getAnalysisAcrossVideos(None, None, numVar.get()))
homeMenuNumConfirm.place(x = 225, y = 125)
homeMenuClearNum = ttk.Button(homeMenuNumFrame, text = "Clear", width = 10, command = lambda : _clear())
homeMenuClearNum.place(x = 377, y = 125)
homeMenuClearNum['state'] = "disabled"
homeMenuSwitchToDate = ttk.Button(homeMenuNumFrame, text = "Switch To Date Selection")
homeMenuSwitchToDate.place(x = 1, y = 169)

homeMenuFrames = [homeMenuDateFrame, homeMenuNumFrame]

homeMenuSwitchToNum.config(command = lambda : switchToNum())
homeMenuSwitchToDate.config(command = lambda : switchToDate())

homeMenuRestartButton = ttk.Button(homeFrame, text = "Restart", command = lambda : restart(), width = 20)
homeMenuRestartButton.place(x = 25, y = 645)


# Welcome Screen Frames, Widgets & Functions
# Switches the window from the start up (welcome) screen to the home screen only if the video Id is valid.
def welcomeFrameToHomeFrame():
    global validID
    global channelSubscriberCount
    if validID == True:
        getAllVideos()
        homeFrameCanvas.create_text(25, 175, text = "Hello " + channelName + "!", font = ("Arial", 20), fill = 'white', anchor = tk.NW, width = 200, justify = tk.CENTER, tag = "hello") 
        homeAvatarLabel1.config(image = channelAvatar)
        homeFrameCanvas.create_text(25, 475, text = "Subscribers:  " + channelSubscriberCount, font = ("Arial", 20), fill = 'white', anchor = tk.NW, width = 200, justify = tk.CENTER, tag = "subs") 
        replaceFrame(welcomeFrame, homeFrame)

# Opens up a window telling the user how to get their channel Id.
def welcomeFrameHelpMenu():
    helpWindow = tk.Toplevel(root)
    helpWindow.geometry('700x500')
    helpWindow.title("YCSA Help")

    helpWindow.attributes('-topmost', True)
    helpWindow.resizable(False, False)

    helpWindowLabel = tk.Label(helpWindow, image = helpWindowImgObj)
    helpWindowLabel.pack(expand = True, fill = tk.BOTH)
    
# Tkinter widgets to render the start up (welcome) screen.
helpWindowImgObj = ImageTk.PhotoImage(Image.open('help_image_1.jpg'))
welcomeCanvas.create_text(170, 220, text = "Welcome!", font = ("Arial", 150), fill = 'white', anchor = tk.NW)
welcomeCanvas.create_text(370, 397, text = "Enter your channel ID below.", font = ("Arial", 20), fill = 'white', anchor = tk.NW)

startupEntry = ttk.Entry(welcomeFrame)
startupEntry.place(x = 165, y = 425, width = 670)

welcomeHelpButtonImg = ImageTk.PhotoImage(Image.open('button.jpg'))
welcomeHelpButton = tk.Button(welcomeFrame, image = welcomeHelpButtonImg, command = lambda : welcomeFrameHelpMenu())
welcomeHelpButton.place(x = 950, y = 650)

startupButton = ttk.Button(welcomeFrame, text = "Confirm", command = lambda : [getChannelData(startupEntry.get()), welcomeFrameToHomeFrame()])
startupButton.place(x = 165, y = 445, width = 670)

root.mainloop()
