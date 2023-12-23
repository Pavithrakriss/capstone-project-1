#importing libraries:
from googleapiclient.discovery import build
import pandas as pd
import streamlit as st
import pymongo
import pymysql
import plotly.express as px
from streamlit_option_menu import option_menu
from PIL import Image

#connecting to mysql & creating "youtube_project" database:
mydb=pymysql.connect(host='127.0.0.1',
                user='root',
                password='pavi@2002',
                port=3306,database="youtube_project")
cur=mydb.cursor() 


#connecting sidebar for option menu
with st.sidebar:
           icon = Image.open(r"C:\Users\DELL\Desktop\Logo_of_YouTube_(2015-2017).svg.png")
           st.image(icon,width=100)
           st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")   
           st.header(":blue[ABOUT]")
           st.subheader("The webapp created by Pavithra for capstone project in Data Science course")
           
           choosen= option_menu("Menu", 
                                  ["Home","Extract & Transform","View"],
                                  icons=["house-door-fill","tools","card-text"],
                                  default_index=0,
                                  orientation="vertical",
                                  styles={"nav-link": {"font-size": "15px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#FFCCBB"},
                                   "icon": {"font-size": "15px"},
                                   "container" : {"max-width": "2000px"},
                                   "nav-link-selected": {"background-color": "#F85C4D"}}) 
           

#API key connection

def Api_connect():
    Api_Id="AIzaSyB3noLtF3rj42QOCBDfJLQQ6ZBKHkpLSWY"

    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube=Api_connect()


# FUNCTION TO GET CHANNEL DETAILS
def get_channel_details(channel_id):
    ch_data = []
    request = youtube.channels().list(part = 'snippet,contentDetails,statistics',
                                     id= channel_id)
    response=request.execute()

    for i in response['items']:
        data = dict(Channel_id = i['id'],
                    Channel_name = i['snippet']['title'],
                    Playlist_id = i['contentDetails']['relatedPlaylists']['uploads'],
                    Subscribers = i['statistics']['subscriberCount'],
                    Views = i['statistics']['viewCount'],
                    Total_videos = i['statistics']['videoCount'],
                    Description = i['snippet']['description'],
                    Publish_Date=i['snippet']['publishedAt']
                    )
        ch_data.append(data)
    return ch_data


#FUNCTION TO GET VIDEO IDS
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, 
                                           part='snippet', 
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids


# FUNCTION TO GET VIDEO DETAILS
def get_video_details(v_ids):
    video_stats = []
    
    for i in v_ids:
        response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=i).execute()
        for video in response['items']:
            video_details = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id = video['snippet']['channelId'],
                                Video_id = video['id'],
                                Title = video['snippet']['title'],
                                Tags = video['snippet'].get('tags'),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                Description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'],
                                Duration = video['contentDetails']['duration'],
                                Views = video['statistics']['viewCount'],
                                Likes = video['statistics'].get('likeCount'),
                                Comments = video['statistics'].get('commentCount'),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                               )
            video_stats.append(video_details)
    return video_stats


#FUNCTION TO GET COMMENT DETAILS
def get_comments_details(v_id):
    comment_data = []
    try:
        for video_id in v_id:
            response = youtube.commentThreads().list(part="snippet,replies",
                                                    videoId=video_id,
                                                    maxResults=50).execute()
            for cmt in response['items']:
                data = dict(Comment_id = cmt['id'],
                            Video_id = cmt['snippet']['videoId'],
                            Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_posted_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                            Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                            Reply_count = cmt['snippet']['totalReplyCount']
                           )
                comment_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except:
        pass
    return comment_data



#upload to MongoDB
client=pymongo.MongoClient("mongodb://localhost:27017")
db=client["Youtube_project"]

#functions to get channels names from mongodb
def channel_names():
    ch_name = []
    for i in db.channel_details.find({},{"_id":0}):
          ch_name.append(i['Channel_name'])
    return ch_name    


#if "HOME" is selected
if choosen == "Home":
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header(":blue[Project Overview]")
    st.subheader(":blue[Domain:]")
    st.write("**Social Media**")
    st.subheader(":blue[Skills used:]")
    st.write("**# Youtube Data API**")
    st.write("**# Python**")
    st.write("**# MongoDB**")  
    st.write("**# MySql**")
    st.write("**# Streamlit**")
    st.subheader(":blue[Overview:]")
    st.write("**Retrieving Youtube channels data from the Google API and storing it in MongoDB as a data lake then transforming data into SQL then querying the data and displaying it in the Streamlit app**")
    

#if "EXTRACT AND TRANSFORM" is selected
if choosen == "Extract & Transform":
    st.subheader(":blue[Extracting and Transforming Details]")
    option = st.radio("Choose",("Extract","Transform"))

      # EXTRACT option to get channel details
    if(option == "Extract"):
        st.markdown("#    ")
        st.write("**:blue[Enter YouTube Channel_ID:]**")
        ch_id = st.text_input("Hint : Goto channel's home page > Right click > View page source > Find channel_id").split(',')

        if ch_id and st.button("Extract Data"):
                ch_details = get_channel_details(ch_id)
                st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
                st.table(ch_details)

        if st.button("Upload to MongoDB"):
                with st.spinner('Please Wait...'):
                   ch_details = get_channel_details(ch_id)
                   v_ids = get_channel_videos(ch_id)
                   vid_details = get_video_details(v_ids)
                   comm_details = get_comments_details(v_ids)

                   collections1 = db.channel_details
                   collections1.insert_many(ch_details)

                   collections2 = db.video_details
                   collections2.insert_many(vid_details)

                   collections3 = db.comments_details
                   collections3.insert_many(comm_details)

                   st.success("Transfer to MongoDB Completed")

#TRANSFORM option to transfer datas to SQL
    if(option == "Transform"):     
            st.markdown("#   ")
            st.markdown("**:blue[Select a channel to Transfer into SQL]**")
            ch_names = channel_names()  
            user_inp = st.selectbox("**Select channel**",options= ch_names)   


#creating channels table in SQL:
def channel_table():
    try:
        create_table='''create table if not exists Channels(Channel_id varchar(50) primary key,
                     Channel_name varchar(100),Playlist_id varchar(50),Subscribers bigint,
                     Views bigint,Total_videos bigint,Description varchar(1000),
                     Publish_Date varchar(50))'''
        cur.execute(create_table)
        mydb.commit()
    except:
        print("Channels table already exists ")   

    #converting mongodb
    collections1 = db.channel_details
    ch_name = [] 
    for i in collections1.find({},{"_id":0}):
        ch_name.append(i)

    df=pd.DataFrame(ch_name)

    #inserting values to channel table:
    query = """insert ignore into Channels(Channel_id,Channel_name,Playlist_id,Subscribers,
                        Views,Total_videos,Description,Publish_Date)
                        values(%s,%s,%s,%s,%s,%s,%s,%s)"""
    for i in range(0,len(df)):
            cur.execute(query,tuple(df.iloc[i]))
            mydb.commit()


#creating videos table in SQL:
def videos_table(): 
    try:
        create_vtable='''create table if not exists Videos(Channel_name varchar(100),
                      Channel_id varchar(50),Video_id varchar(50) primary key,Title varchar(500),
                      Tags text,Thumbnail text,Description text,Published_date varchar(50),
                      Duration time,Views bigint,Likes bigint,Comments bigint,
                      Favorite_count int,Definition varchar(50),Caption_status varchar(50))'''
        cur.execute(create_vtable)
        mydb.commit()
    except:
        print("Videos table already exists ")    

    #mongodb connection:
    client = pymongo.MongoClient('mongodb://localhost:27017')
    db = client["Youtube_project"]

    #Function to get video ids from MongoDB
    collections2 = db.video_details
    vid_name = []
    for i in collections2.find({},{"id":0}):
            vid_name.append(i)

    df2=pd.DataFrame(vid_name)   

    #inserting values in table:
    query1 =  """insert ignore into Videos(Channel_name,Channel_id,Video_id,Title,Tags,Thumbnail,
                 Description,Published_date,Duration,Views,Likes,Comments,Favorite_count,
                 Definition,Caption_status)
                 values(%s,%s,%s,%s,%a,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    
    for i in range(0,len(df2)):
        cur.execute(query1, tuple(df2.iloc[i]))           
        mydb.commit()



#creating comments table in SQL:
def comments_table():
    try:
        create_cmtable='''create table if not exists Comments(Comment_id varchar(100) primary key,
                          Video_id varchar(100),Comment_text text,Comment_author varchar(100),
                          Comment_posted_date date,Like_count int,Reply_count int)'''
        cur.execute(create_cmtable)
        mydb.commit()
    except:
        print("Comments table already exists ")  


    #converting mongodb collection to dataframe:
    collections3 = db.comments_details
    comments = []  
    for i in collections3.find({},{"_id":0}):
        comments.append(i) 

    df3=pd.DataFrame(comments)

    #inserting values to comments_table
    collections1 = db.video_details   
    collections2 = db.comments_details
    query2 = """insert ignore into Comments(Comment_id,Video_id,Comment_text,Comment_author,
                Comment_posted_date,Like_count,Reply_count)
                values(%s,%s,%s,%s,%s,%s,%s)"""
    
    for vid in collections1.find({},{'_id' :0}):
        for i in collections2.find({'Video_id': vid['video_id']},{'_id' : 0}):
            cur.execute(query2,tuple(i.values()))
            mydb.commit()

#wrapping all table creation function in "tables" function
    if st.button("Submit"):
        try:
            channel_table()
            videos_table()
            comments_table()
            st.success("Successfully inserted into tables")
        except:
            st.error("Channel details already transformed")


#VIEW PAGE
if choosen == "View": 


#To show channels dataframe in streamlit as a table
    def streamlit_channels():
        collections1 = db.channel_details
        ch_name = []
        for i in collections1.find({},{"_id":0}):
            ch_name.append(i)

        df=st.dataframe(ch_name)
        return df
    

 #To show videos dataframe in streamlit as a table
    def streamlit_videos():
        collections2 = db.video_details
        vid_name = []
        for i in collections2.find({},{"_id":0}):
                vid_name.append(i)

        df2=st.dataframe(vid_name)
        return df2    
    
 #To show comments dataframe in streamlit as a table
    def streamlit_comments():
        collections3 = db.comments_details
        comments = []
        for i in collections3.find({},{"_id":0}):
            comments.append(i)

        df3=st.dataframe(comments)
        return df3    
    

    #showing tables in streamlit
    tables_op=st.radio("SELECT TABLES TO VIEW",("Channels","Videos","Comments"))
    if tables_op=="Channels":
        st.subheader(":blue[Channels table]")
        streamlit_channels() #calling dataframe function
    elif tables_op=="Videos":
        st.subheader(":blue[Videos table]")
        streamlit_videos()
    elif tables_op=="Comments":
        st.subheader(":blue[Comments table]")
        streamlit_comments()    

st.write("## :orange[Select any question to get Insights]")
questions = st.selectbox('Questions',
['1. What are the names of all the videos and their corresponding channels?',
'2. Which channels have the most number of videos, and how many videos do they have?',
'3. What are the top 10 most viewed videos and their respective channels?',
'4. How many comments were made on each video, and what are their corresponding video names?',
'5. Which videos have the highest number of likes, and what are their corresponding channel names?',
'6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
'7. What is the total number of views for each channel, and what are their corresponding channel names?',
'8. What are the names of all the channels that have published videos in the year 2022?',
'9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
'10. Which videos have the highest number of comments, and what are their corresponding channel names?'])              
if questions == '1. What are the names of all the videos and their corresponding channels?':
         cur.execute('''select Title as Videoname,
                     Channel_name from videos order by Channel_name;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Video Name","Channel Name"])
         st.write(df)

elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
         cur.execute('''select Channel_name,
                     Total_videos from channels order by Total_videos desc;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Total Video count"])
         st.write(df)
         st.write("### :green[Number of videos in each channel :]")
         fig = px.bar(df,
                     x="Channel Name",
                     y="Total Video count",
                     orientation='v',
                     color="Channel Name"
                    )
         st.plotly_chart(fig,use_container_width=True)    

elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
         cur.execute('''select Channel_name,Title,Views from videos 
                     order by Views desc limit 10;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Video Name","Total Views"])
         st.write(df)
         st.write("### :green[Top 10 most viewed videos :]")
         fig = px.bar(df,
                     x="Video Name",
                     y="Total Views",
                     orientation='v',
                     color="Channel Name"
                    )
         st.plotly_chart(fig,use_container_width=True)

elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
         cur.execute('''select v.Title as Video_name,v.Video_id, count(Comment_id) as Total_comments
                     from videos v right join comments c on v.Video_id=c.Video_id
                    group by c.Video_id order by Total_comments desc;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Video Name","Video ID","Total Comments"])
         st.write(df)   

elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
         cur.execute('''select Channel_name, Title, Likes from videos where Likes is not null order by Likes desc limit 10;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Video Name","Likes"])
         st.write(df)
         st.write("### :green[Top 10 most liked videos :]")
         fig = px.bar(df,
                     x="Video Name",
                     y="Likes",
                     orientation='v',
                     color="Channel Name"
                    )
         st.plotly_chart(fig,use_container_width=True) 

elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
         cur.execute('''select Channel_name,Title,Likes from videos order by Likes desc;''') 
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Video Name","Likes"])
         st.write(df)

elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
         cur.execute('''select Channel_name,Views from channels order by Views desc;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Views"])
         st.write(df)   
         st.write("### :green[Channels vs Views :]")
         fig = px.bar(df,
                     x="Channel Name",
                     y="Views",
                     orientation='v',
                     color="Channel Name"
                    )
         st.plotly_chart(fig,use_container_width=True)

elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
         cur.execute('''select Channel_name,Title,Published_date from videos where year(Published_date)="2022";''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Video","Pub_Date"])
         st.write(df)   

elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
         cur.execute('''select Channel_name , avg(Duration) as Duration from videos group by Channel_name;''')
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel_name","Duration"])
         st.write(df)  

elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
         cur.execute('''select v.channel_name,c.video_id,v.Title as video_name,count(comment_id) as comments_count
                     from comments c join videos v on c.video_id=v.video_id group by c.video_id 
                     order by comments_count desc;''') 
         mydb.commit()
         df = pd.DataFrame(cur.fetchall(),columns=["Channel Name","Video ID","Video Name","Comments Count"])
         st.write(df)   
         st.write("### :green[Videos with most comments :]")
         fig = px.bar(df,
                     x="Video Name",
                     y="Comments Count",
                     orientation='v',
                     color="Channel Name"
                    )
         st.plotly_chart(fig,use_container_width=True)                   
         
