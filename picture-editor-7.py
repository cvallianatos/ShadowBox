from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import ImageTk, Image, ImageOps
import os
from datetime import datetime
import sqlite3
from sqlite3 import Error
import reverse_geocoder as rg
from exif import Image as exifImage
import glob
import shutil
import io

class PictureEditor():
    
    def __init__(self):

        self.myIndex = 0
        self.connection = None
        self.myPicture = None
        self.dataHasChanged = False

        self.myLoc = os.path.realpath(os.path.dirname(__file__))
        self.myLoc = self.myLoc + "/test.db"

        self.createConnection()

        self.window = Tk()
        self.window.title("ShadowBox Picture Editor v.2.0")

        # Frames

        self.content = ttk.Frame(self.window, padding=(3,3,12,12))
        self.frame = ttk.Frame(self.content, width=500, height=800)

        # Labels
        self.databaseLabel = ttk.Label(self.content, text="Database: " + self.myLoc)
        dateLabel = ttk.Label(self.content, text="Date")
        cityLabel = ttk.Label(self.content, text="City")
        stateLabel = ttk.Label(self.content, text="State")
        countryLabel = ttk.Label(self.content, text="Country")

        # Entry fields

        self.date = ttk.Entry(self.content)
        self.city = ttk.Entry(self.content)
        self.state = ttk.Entry(self.content)
        self.country = ttk.Entry(self.content)

        # Maintenance buttons

        self.changeDB = ttk.Button(self.content, text="Change DB", command=self.changeDatabase)
        self.load = ttk.Button(self.content, text="Load", command=self.loadPictures)
        self.delete = ttk.Button(self.content, text="Delete", command=self.deletePicture)
        self.confirm = ttk.Button(self.content, text="Confirm", command=self.conifrmChange)

        # Navigation buttons

        self.previous = ttk.Button(self.content, text="Previous", command= lambda: self.findPicture(-1))
        self.next = ttk.Button(self.content, text="Next", command= lambda: self.findPicture(1))
        self.exit = ttk.Button(self.content, text="Exit", command = self.window.quit)
        
        # Picture display location

        self.picLabel = ttk.Label(self.frame)

        # Geometry management

        # Row 0
        self.content.grid(column=0, row=0, sticky=(N, S, E, W))
        self.databaseLabel.grid(column=0, row=0, columnspan=3)

        # Row 1
        self.frame.grid(column=0, row=1, columnspan=4, rowspan=2, sticky=(N, S, E, W))
        self.picLabel.grid(column=0, row=1)

        # Row 4

        dateLabel.grid(column=0, row=4)
        cityLabel.grid(column=1, row=4)
        stateLabel.grid(column=2, row=4)
        countryLabel.grid(column=3, row=4)

        # Row 5

        self.date.grid(column=0, row=5, sticky=(N, S, E, W))
        self.city.grid(column=1, row=5, sticky=(N, S, E, W))
        self.state.grid(column=2, row=5, sticky=(N, S, E, W))
        self.country.grid(column=3, row=5, sticky=(N, S, E, W))

        # Row 6

        self.changeDB.grid(column=0, row=6)
        self.load.grid(column=1, row=6)
        self.delete.grid(column=2, row=6)
        self.confirm.grid(column=3, row=6)
        
        # Row 7

        self.previous.grid(column=1, row=7)
        self.next.grid(column=2, row=7)
        self.exit.grid(column=3, row=7)

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=3)
        self.content.columnconfigure(1, weight=3)
        self.content.columnconfigure(2, weight=3)
        self.content.columnconfigure(3, weight=3)
        self.content.rowconfigure(1, weight=1)

        self.swidth = self.frame.winfo_reqwidth()
        self.sheight= self.frame.winfo_reqheight()

        self.frame.bind('<Configure>', self.handler)

        self.findPicture(1)

        self.window.mainloop()

    def findPicture(self, incr):
        cursor = self.connection.cursor()
        cursor.execute("SELECT MIN(rowid), MAX(rowid) FROM PictureInfo")
        minMaxId = cursor.fetchone()
        cursor.close()
        self.myPicture = None
        while self.myPicture == None:
            self.myIndex = self.myIndex + incr
            if incr == -1:
                if self.myIndex < minMaxId[0]:
                    self.myIndex = minMaxId[1]
            else:
                if self.myIndex > minMaxId[1]:
                    self.myIndex = minMaxId[0]
            self.getPictureInfo()
        self.showPicture()
        return 

    def showPicture(self):
 
        # Default entry values

        whenPic = self.myPicture[1]
        cityPic = self.myPicture[2]
        statePic = self.myPicture[3]
        countryPic = self.myPicture[4]

        self.date.delete(0,"end")
        self.date.insert(0, whenPic)

        self.city.delete(0,"end")
        self.city.insert(0, cityPic)
        
        self.state.delete(0,"end")
        self.state.insert(0, statePic)
        
        self.country.delete(0,"end")
        self.country.insert(0, countryPic)


        original_image = Image.open(io.BytesIO(self.myPicture[5]))
        original_image = ImageOps.exif_transpose(original_image)
        width, height = original_image.size
        factor = min(self.swidth/width, self.sheight/height)
        width_new = int(width * factor)
        height_new = int(height * factor)
        resized_image = original_image.resize((width_new,height_new), Image.LANCZOS)
        my_image = ImageTk.PhotoImage(resized_image)
        self.picLabel.configure(image=my_image)
        self.picLabel.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        self.picLabel.image = my_image
        return
    
    def createConnection(self):
        try:
            self.connection = sqlite3.connect(self.myLoc)
        except Error as e:
            print(f"The error '{e}' occurred")
        return 

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

    def handler(self, e):
        # Handler to respond on <Esc> key press
        self.swidth = self.frame.winfo_width()
        self.sheight = self.frame.winfo_height()
        self.showPicture()
        return

    def conifrmChange(self):
        newDate = self.date.get()
        newCity = self.city.get()
        newState = self.state.get()
        newCountry = self.country.get()

        sql = ''' UPDATE PictureInfo
            SET DateTaken = ?, City = ?, State = ?, Country = ?
            WHERE rowid = ?'''
        data =   (newDate, newCity ,newState, newCountry, self.myIndex)
        cursor = self.connection.cursor()
        cursor.execute(sql, data)
        self.connection.commit()
        cursor.close()
        return
    
    def changeDatabase(self):
        fileName = fd.askopenfilename(title='Open a Database',initialdir='.')

        if fileName != "":
            self.myLoc = fileName
            self.createConnection()
            self.myIndex = 1
            self.databaseLabel.configure(text=fileName)
        return 
    
    def deletePicture(self):
        sql = "DELETE FROM PictureInfo WHERE rowid = " + str(self.myIndex)
        
        print(sql)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        self.connection.commit()
        return

    def format_dms_coordinates(self, coordinates):
        return f"{coordinates[0]}° {coordinates[1]}\' {coordinates[2]}\""

    def dms_coordinates_to_dd_coordinates(self, coordinates, coordinates_ref):
        decimal_degrees = coordinates[0] + \
                        coordinates[1] / 60 + \
                        coordinates[2] / 3600
        
        if coordinates_ref == "S" or coordinates_ref == "W":
            decimal_degrees = -decimal_degrees
        
        return decimal_degrees

    def pictureExist(self, Name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM PictureInfo WHERE Name = " + "'" + Name + "'")
        result = cursor.fetchone()
        if result == None:
            return False
        else:
            return True

    def loadPictures(self):
        pictureFolderName = fd.askdirectory(title='Open a picture folder',initialdir='.')
        if pictureFolderName == "":
            return
        for filename in glob.iglob(pictureFolderName + '**/*.*'):
            if not os.path.isdir(filename):
                Name = os.path.basename(filename)
                flag = False

                if not self.pictureExist(Name):
                    print("************* NEW PICTURE ***************")
                    print(Name)
                    try:
                        image = exifImage(filename)
                        flag = True
                    except:
                        flag = False

                if flag and hasattr(image, "gps_latitude") and hasattr(image, "gps_latitude_ref") and hasattr(image, "gps_longitude") and hasattr(image, "gps_longitude_ref"):
                    Lat = image.gps_latitude
                    GPSLatitude = ''.join(map(str, Lat))
                    LatitudeRef = image.gps_latitude_ref
                    LatitudeDegrees = self.dms_coordinates_to_dd_coordinates(Lat, LatitudeRef)
                    Lon = image.gps_longitude
                    GPSLongitude = ''.join(map(str, Lon))
                    LongitudeRef = image.gps_longitude_ref
                    LongitudeDegrees = self.dms_coordinates_to_dd_coordinates(Lon, LongitudeRef)

                    coordinates =(LatitudeDegrees, LongitudeDegrees)
                    location_info = rg.search(coordinates,mode=1)[0]
                    City = location_info['name']
                    State = location_info['admin1']
                    Country = location_info['cc']
                else:
                    GPSLatitude =  "NA"
                    LatitudeRef = "NA"
                    LatitudeDegrees = "NA"
                    GPSLongitude = "NA"
                    LongitudeRef = "NA"
                    LongitudeDegrees = "NA"    
                    City = "NA"
                    State = "NA"
                    Country = "NA"

                if flag and hasattr(image, "datetime_original"):
                    datetime_object = datetime.strptime(image.datetime_original, '%Y:%m:%d %H:%M:%S')
                    DateTaken = datetime_object.date().strftime("%B %d, %Y")
                    TimeTaken = datetime_object.time().strftime("%H:%M:%S")
                else:
                    DateTaken = "NA"
                    TimeTaken = "NA"

                myBlob = self.convertToBinaryData(filename)

                print("----------------------------------")
                print(LatitudeRef, " ", GPSLatitude, " ---> ", LatitudeDegrees)
                print(LongitudeRef, " ", GPSLongitude, " ---> ", LongitudeDegrees)
                print("Taken on: ", DateTaken, " and time was: ", TimeTaken)
                print(City, State, Country )
            
                if flag:
                    pic = (Name, DateTaken, TimeTaken, GPSLatitude, LatitudeRef, GPSLongitude, LongitudeRef, LatitudeDegrees, LongitudeDegrees, City, State, Country, myBlob)
                    self.addPicture(pic)

        return

    def convertToBinaryData(self, filename):
    # Convert digital data to binary format
        with open(filename, 'rb') as file:
            blobData = file.read()
        return blobData
    
    def addPicture(self, pic):
        sql = """
            INSERT INTO
                PictureInfo (Name, DateTaken, TimeTaken, GPSLatitude, LatitudeRef, GPSLongitude, LongitudeRef, LatitudeDegrees, LongitudeDegrees, City, State, Country, Image)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        cursor = self.connection.cursor()
        cursor.execute(sql, pic)
        self.connection.commit()
        return cursor.lastrowid

# Create picture editor
editor = PictureEditor()