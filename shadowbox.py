from tkinter import *
from PIL import ImageTk, Image, ImageOps
import os
from datetime import datetime
import subprocess
import sqlite3
from sqlite3 import Error
import io
import time

class ShadowBox():
    def __init__(self):
        self.end_time = "08" # Finish at 20:00 hours
        self.myLoc = os.path.realpath(os.path.dirname(__file__))
        return
   
    def getUptime(self):
        subprocess_instance = subprocess.Popen(['uptime', '-p'], stdout=subprocess.PIPE, universal_newlines=True)
        cmd_out, _error = subprocess_instance.communicate()
        list_of_strings = cmd_out.split(" ")
        return list_of_strings[1], list_of_strings[2][0:4]

    def getNTPStatus(self):
        subprocess_instance = subprocess.Popen(['timedatectl'], stdout=subprocess.PIPE, universal_newlines=True)
        cmd_out, _error = subprocess_instance.communicate()

        list_of_parts = cmd_out.split('\n')
        string_val = list_of_parts[4].strip()
        list_of_strings = string_val.split(":")
        string_val = list_of_strings[1].strip()
        if string_val == "yes":
            return True
        else:
            return False
        
    def writeToLog(self, topic):
        path = self.myLoc + "/log.txt"
        f = open(path, "a")
        line = topic
        f.write(line)
        f.write("\n")
        f.close()
        return

    def determineStatus(self):
        current_time = str(datetime.now())[11:13]
        if current_time == self.end_time:
            self.writeToLog("It is time...")
            if self.getNTPStatus():
                x, y =  self.getUptime()
                self.writeToLog(str(x))
                self.writeToLog(y)
                self.writeToLog("-----------")
                if y  == "hour" and int(x) > 1:
                    self.writeToLog("Shuting down")
                    #os.system("sudo shutdown -P now")
                else:
                    self.writeToLog("Not shuting down")
        return

class SlideShow():
    def __init__(self, index):
        self.myShadowBox = ShadowBox()
        self.myIndex = index
        self.start_time = time.time()
        self.period = 300 # Duration of each slideshow in seconds
        self.connection = None
        self.myPicture = None
        self.window = Tk()
        self.window.title("ShadowBox")
        self.window.bind("<Escape>", self.handler)
        
        #self.window.attributes('-fullscreen',True)
        #self.window.configure(bg='black', cursor="none")

        self.window.geometry("800x800")

        # get the size of the screen

        # getting screen's height in pixels
        self.sheight = self.window.winfo_screenheight()
        
        # getting screen's width in pixels
        self.swidth = self.window.winfo_screenwidth()
   
        self.myLoc = os.path.realpath(os.path.dirname(__file__))
        self.create_connection(self.myLoc + "/master.db")

        self.mylabel=Label(self.window,justify='center')
        self.myText = Label(self.window,justify='center')

        self.mylabel.pack()
        self.myText.pack()
        self.window.after(1000, self.clock)
        self.window.mainloop()
   
    def handler(self, e):
        self.window.quit()
        return

    def create_connection(self,path):
        try:
            self.connection = sqlite3.connect(path)
        except Error as e:
            print(f"The error '{e}' occurred")
        return 

    def clock(self):
        end = time.time()
        elapsed_time = int(end - self.start_time)
        if elapsed_time > self.period:
            self.window.destroy()
            return

        self.myShadowBox.determineStatus()

        # Check if any events have been triggered
        self.scan()

        self.getPictureInfo()
        
        if self.myPicture == None:
            self.myIndex = 1
            self.getPictureInfo()

        original_image = Image.open(io.BytesIO(self.myPicture[5]))
        original_image = ImageOps.exif_transpose(original_image)
        width, height = original_image.size
        factor = min(self.swidth/width, self.sheight/height)
        width_new = int(width * factor)
        height_new = int(height * factor)
        resized_image = original_image.resize((width_new,height_new), Image.LANCZOS)
        my_image = ImageTk.PhotoImage(resized_image)
        self.mylabel.configure(image=my_image)
        self.mylabel.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        self.mylabel.image = my_image
        when = self.myPicture[1]
        city = self.myPicture[2]
        state = self.myPicture[3]
        country = self.myPicture[4]
        if when == "NA":
            when = ""
        if city == "NA":
            city = ""
        if state == "NA":
            state = ""
        if country == "NA":
            country = ""
        if when != "" or city != "" or state != "" or country != "":
            text_to_display = when + " " + city + "  " + state + " " + country
            self.myText.configure(text= text_to_display, background='black', foreground='white')
        
        self.myIndex = self.myIndex + 1
    
        # Wait for 7 seconds
        self.window.after(7000, self.clock)  

    def getPictureInfo(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT Name, DateTaken, City, State, Country, Image FROM PictureInfo WHERE rowid = " + str(self.myIndex))
            myPic = cursor.fetchone()
            cursor.close()
            self.myPicture = myPic
            return 
        except:
            cursor.close()
            return None

    def sendMsg(self, topic):
        path = self.myLoc + "/status.txt"
        f = open(path, "a")
        line = topic
        f.write(line)
        f.write("\n")
        f.close()
        return

    def scan(self):
        path = self.myLoc + "/flag.txt"
        if os.path.isfile(path):
            f = open(path, "r")
            line = f.readline()
            if line.strip() == "Move":
                self.start_time = time.time()
                self.sendMsg("Movement has occured at " + str((datetime.now())) + " Start time is now: " + str(self.start_time))  
            elif line.strip() == "Stop":
                self.sendMsg("Stop is rquested") 
            elif line.strip() == "Next":
                self.sendMsg("Next is rquested")    
            elif line.strip() == "Previous":
                self.sendMsg("Previous is rquested")    
            elif line.strip() == "Annotate":
                self.sendMsg("Annotate is rquested")    
            elif line.strip() == "Search":
                self.sendMsg("Search is rquested")    
            elif line.strip() == "Resume":
                self.sendMsg("Resume is rquested")    
            elif line.strip() == "Listen":
                self.sendMsg("Listen is rquested")    
            os.remove(path)
        return

class BlankScreen():

    def __init__(self):
        self.myShadowBox = ShadowBox()
        self.window = Tk()
        self.window.title("BlankScreen")
        self.window.bind("<Escape>", self.handler)
        self.myLoc = os.path.realpath(os.path.dirname(__file__))
 
        #self.window.attributes('-fullscreen',True)
        #self.window.configure(bg='black', cursor="none")
        
        self.window.configure(bg='black')
        self.window.geometry("800x800")
 
        self.window.after(1000, self.clock)
        self.window.mainloop()
   
    def handler(self, e):
        self.window.quit()
        return
    
    def scan(self):
        path =  self.myLoc + "/flag.txt"
        if os.path.isfile(path):
            f = open(path, "r")
            line = f.readline()
            if line.strip() == "Move":
                self.window.destroy()
                return
            elif line.strip() == "Stop":
                self.sendMsg("Stop is rquested") 
            elif line.strip() == "Next":
                self.sendMsg("Next is rquested")    
            elif line.strip() == "Previous":
                self.sendMsg("Previous is rquested")    
            elif line.strip() == "Annotate":
                self.sendMsg("Annotate is rquested")    
            elif line.strip() == "Search":
                self.sendMsg("Search is rquested")    
            elif line.strip() == "Resume":
                self.sendMsg("Resume is rquested")    
            elif line.strip() == "Listen":
                self.sendMsg("Listen is rquested")    
            os.remove(path)
        return
    
    def clock(self):

        self.myShadowBox.determineStatus()

        # Check if any events have been triggered
        self.scan()

        # Wait for 5 seconds
        self.window.after(5000, self.clock)  
    
    def sendMsg(self, topic):
        path = self.myLoc + "/status.txt"
        f = open(path, "a")
        line = topic
        f.write(line)
        f.write("\n")
        f.close()
        return

def main():
    # Main program   
    # Create ShadowBox & BlankScreen
    index = 1
    while True:
        slideshow = SlideShow(index)
        index = slideshow.myIndex
        del slideshow
        blankscreen = BlankScreen()
        del blankscreen

if __name__ == '__main__':
    main()
