from splinter import Browser
from time import sleep
from datetime import datetime, timedelta
import os, sys
import urllib
import cv2
import numpy as np
from PIL import Image
import imutils
import csv

class Scraper():
    start_date = datetime(2018, 1, 8)
    url = 'http://spaceweather.com/'

    def scrape(self):
        self.browser = Browser('firefox')
        self.browser.driver.set_page_load_timeout(60)
        self.browser.visit(self.url)
        for day in self.get_days():
            self.scrape_day(day)

    def scrape_day(self, day):
        self.browser.select('month', day.strftime('%m'))
        self.browser.select('day', day.strftime('%d'))
        self.browser.select('year', day.strftime('%Y'))
        button = self.browser.find_by_name('view')
        button.click()
        text = self.browser.find_by_css('.solarWindText')[4].text
        number = int(text.split(' ')[2].strip())
        link = self.browser.find_link_by_partial_href('images{}/'.format(day.strftime('%Y')))['href']
        folder_name = "data/{}{}{}".format(day.strftime('%Y'), day.strftime('%m'), day.strftime('%d'))
        image_name = "{}/image.gif".format(folder_name)
        txt_name = "{}/data.txt".format(folder_name)
        os.mkdir(folder_name)
        urllib.urlretrieve(link, image_name)
        img = Image.open(image_name)
        img.save("{}/image.png".format(folder_name), 'png', optimize=True, quality=70)
        txt_file = open(txt_name, 'w')
        txt_file.write(str(number))
        txt_file.close()
        print("Downloaded data for {}, sunspots: {}".format(day.strftime('%m/%d/%Y'), number))


    def get_days(self):
        days = []
        for i in range(0, 8):
            base = self.start_date + timedelta(days=7 * i)
            first = base
            second = base + timedelta(days=2)
            third = base + timedelta(days=4)
            days.append(first)
            days.append(second)
            days.append(third)
        return days

class Entry():
    folder = None
    date = None
    sunspots = -1
    image_path = None
    counted_sunspots = 0
    sections = [0, 0, 0, 0]

    def nothing(self, *arg):
        pass

    def __init__(self, folder, date, sunspots, image_path):
        self.folder = folder
        self.date = date
        self.sunspots = sunspots
        self.image_path = image_path

    def process(self):
        frame = cv2.imread(self.image_path)
        height, width, channels = frame.shape
        frameBGR = cv2.GaussianBlur(frame, (1, 1), 0)
        hsv = cv2.cvtColor(frameBGR, cv2.COLOR_BGR2HSV)
        
        colorLow = np.array([0,90,80])
        colorHigh = np.array([10,255,255])
        mask = cv2.inRange(hsv, colorLow, colorHigh)
        result = cv2.bitwise_and(frame, frame, mask=mask)
        image_edged = cv2.Canny(mask, 50, 100)
        image_edged = cv2.dilate(image_edged, None, iterations=1)
        image_edged = cv2.erode(image_edged, None, iterations=1)
        cnts = cv2.findContours(image_edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
        image_contours = cv2.bitwise_not(result)

        self.counted_sunspots = 0
        self.sections = [0, 0, 0, 0]
        section_1_start, section_1_end = 0, height/4
        section_2_start, section_2_end = height/4, height/4 * 2
        section_3_start, section_3_end = height/4 * 2, height/4 * 3
        section_4_start, section_4_end = height/4 * 3, height/4 * 4
        cv2.line(image_contours, (0, section_1_end), (width, section_1_end), (0, 0, 0), 5)
        cv2.line(image_contours, (0, section_2_end), (width, section_2_end), (0, 0, 0), 10)
        cv2.line(image_contours, (0, section_3_end), (width, section_3_end), (0, 0, 0), 5)
        cv2.circle(image_contours, (width/2, height/2), width/2, (0, 0, 0), 5)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image_contours, self.date.strftime('%a %b %d'), (20, 50), font, 2, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(image_contours, self.date.strftime('SSN: {}'.format(self.sunspots)), (20, 100), font, 1.5, (0, 0, 0), 2, cv2.LINE_AA)

        for c in cnts:
            if cv2.contourArea(c) < 5:
                continue
            (x,y),radius = cv2.minEnclosingCircle(c)
            x = int(x)
            y = int(y)
            radius = int(radius)
            cv2.circle(image_contours, (x, y), radius, (100, 100, 255), -1)

            self.counted_sunspots = self.counted_sunspots + 1
            if y >= section_1_start and y <= section_1_end:
                #cv2.putText(image_contours, '1', (x, y - 10), font, 0.8, (100, 100, 255), 2, cv2.LINE_AA)
                self.sections[0] = self.sections[0] + 1
            elif y >= section_2_start and y <= section_2_end:
                #cv2.putText(image_contours, '2', (x, y - 10), font, 0.8, (100, 100, 255), 2, cv2.LINE_AA)
                self.sections[1] = self.sections[1] + 1
            elif y >= section_3_start and y <= section_3_end:
                #cv2.putText(image_contours, '3', (x, y - 10), font, 0.8, (100, 100, 255), 2, cv2.LINE_AA)
                self.sections[2] = self.sections[2] + 1
            elif y >= section_4_start and y <= section_4_end:
                #cv2.putText(image_contours, '4', (x, y - 10), font, 0.8, (100, 100, 255), 2, cv2.LINE_AA)
                self.sections[3] = self.sections[3] + 1
        print('Counted sunspots: {}'.format(self.counted_sunspots))
        print(self.sections)
        cv2.putText(image_contours, 'Section 1: {}'.format(self.sections[0]), (20, 130), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(image_contours, 'Section 2: {}'.format(self.sections[1]), (20, 160), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(image_contours, 'Section 3: {}'.format(self.sections[2]), (20, 190), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(image_contours, 'Section 4: {}'.format(self.sections[3]), (20, 220), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

        colorLow = np.array([0,0,90])
        colorHigh = np.array([0,0,255])
        mask = cv2.inRange(hsv, colorLow, colorHigh)
        image_contours[mask > 0] = (0, 0, 0)
        vis = np.concatenate((frame, image_contours), axis=1)

        cv2.imwrite('out/images/{}.png'.format(self.folder), vis)

class Processor():
    entries = []
    
    def load(self):
        folders = os.listdir("data")
        for folder in folders:
            year = int(folder[:4])
            month = int(folder[4:6])
            day = int(folder[6:8])
            date = datetime(year, month, day)
            image_name = "data/{}/image.png".format(folder)
            txt_name = "data/{}/data.txt".format(folder)
            txt_file = open(txt_name, 'r')
            content = txt_file.readlines()
            txt_file.close()
            number = int(content[0])
            print(folder)
            entry = Entry(folder, date, number, image_name)
            entry.process()
            self.entries.append(entry)
        self.entries.sort(key=lambda x: x.date, reverse=False)

    def compute(self):
        for section in range(0, 4):
            total = 0
            for entry in self.entries:
                total += entry.sections[section]
            average = float(total) / float(len(self.entries))
            print('-------[Section {}]-------'.format(section + 1))
            print('Total: {}'.format(total))
            print('Average: {}'.format(average))
        total = 0
        sections_data = [["date", "section_1", "section_2", "section_3", "section_4"]]
        numbers_data = [["date", "reported", "visible"]]
        for entry in self.entries:
            total += entry.counted_sunspots
            sections_data.append([entry.date.strftime("%Y/%m/%d")] + entry.sections)
            numbers_data.append([entry.date.strftime("%Y/%m/%d")] + [entry.sunspots, entry.counted_sunspots])
        average = float(total) / float(len(self.entries))
        print('---------[TOTAL]---------')
        print('Total: {}'.format(total))
        print('Average: {}'.format(average))
        csv_file = open('out/sections.csv', 'w')
        writer = csv.writer(csv_file)
        writer.writerows(sections_data)
        csv_file.close()
        csv_file = open('out/numbers.csv', 'w')
        writer = csv.writer(csv_file)
        writer.writerows(numbers_data)
        csv_file.close()

scraper = Scraper()
scraper.scrape()
processor = Processor()
processor.load()
processor.compute()