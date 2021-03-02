from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tqdm import tqdm
import json
import random
import os
import cv2
import numpy as np

"""
Noise generateing from
https://www.cnblogs.com/wojianxin/p/12499928.html
"""


class Generator:
    def __init__(self):
        self.configPath = "cfg.json"
    
    def config(self):
        if not os.path.isfile(self.configPath):
            raise FileNotFoundError("Cofigure file NOT found")
        self.settings = json.load(open(self.configPath, 'r'))

    def check(self):
        if os.listdir(self.settings["datasetPicsDir"]):
            print("Output dir NOT Empty")
            print("Enter Y to clear dir and proceed:", end = '')
            if input().strip() == 'Y':
                for item in os.listdir(self.settings["datasetPicsDir"]):
                    os.remove(os.path.join(self.settings["datasetPicsDir"], item))
            else:
                raise FileNotFoundError("Output dir NOT Empty")
        if not os.path.isfile(self.settings["textPath"]):
            raise FileNotFoundError("Plain text source NOT Found")
        for each in self.settings["fontFiles"]:
            if not os.path.isfile(each):
                raise FileNotFoundError("Font file %s NOT Found" % each)
        self.labelFile = open(self.settings["labelPath"],'w', encoding='utf-8')
        
        

        
    def prepare(self):
        self.text = ''.join(open(self.settings["textPath"], 'r', encoding='utf-8').readlines()).replace('\n', '').replace('\t', '').replace('\r', '').replace(' ', '')
        self.textLength = len(self.text)


    def generateRandomText(self):
        length = random.randint(self.settings['txtLengthLower'], self.settings['txtLengthUpper'])
        i = random.randint(0, self.textLength - length)
        text = self.text[i:i+length]
        return length, text
        
    def generateOne(self, text:str):

        # choose random font with random font size
        font = ImageFont.truetype(random.choice(self.settings['fontFiles']), size=random.choice(self.settings["fontSize"]), encoding="utf-8")

        if not self.settings["isFontRotate"]:
            # no char rotation required
            im = Image.new('RGB', size=font.getsize(text=text), color=tuple(random.choice(self.settings["picBackgroundColor"])))
            imd = ImageDraw.Draw(im)
            imd.text(xy=(0,0), text=text, font=font, fill=random.choice(self.settings["fontColor"]))
            # ready for return im & text

        elif self.settings["isFontRotate"]:
            if self.settings["isHorizontaVertical"]:
                lineDirection = random.randint(0, 1)
            else:
                lineDirection = 1
                # defalut for Horizontal
            
            charList = []
            backgroundColor = tuple(random.choice(self.settings["picBackgroundColor"]))
            fontColor = tuple(random.choice(self.settings["fontColor"]))

            # generate cahr by char
            for char in text:
                imTmp = Image.new('RGB', size=font.getsize(text=char), color=backgroundColor)
                imTmpd = ImageDraw.Draw(imTmp)
                imTmpd.text(xy=(0,0), text=char, font=font, fill=fontColor)
                charList.append(imTmp)

            # rotating
            if not self.settings["isEachFontRotate"]:
                rotatingAngle = random.choice(self.settings["rotatingAngle"])
            
            for i in range(len(charList)):
                if self.settings["isEachFontRotate"]:
                    rotatingAngle = random.choice(self.settings["rotatingAngle"])
                charList[i] = charList[i].rotate(angle=rotatingAngle, expand=True, fillcolor=backgroundColor)

            
            if lineDirection:
                backgroundWidth = sum([imTmp.width for imTmp in charList])
                backgroundHeight = max([imTmp.height for imTmp in charList])
            else:
                backgroundWidth = max([imTmp.width for imTmp in charList])
                backgroundHeight = sum([imTmp.height for imTmp in charList])
            
            im = Image.new('RGB', size=(backgroundWidth, backgroundHeight), color=backgroundColor)
            cursorWidth, cursorHeight = 0, 0
            for charpic in charList:
                im.paste(charpic, box=(cursorWidth, cursorHeight))
                if lineDirection:
                    # if line is horizontal
                    cursorWidth += charpic.width
                else:
                    cursorHeight += charpic.height
            # ready to return
        return im

    def addNoise(self, pic:Image.Image):
        if self.settings["gasussNoiseMean"] or self.settings["gasussNoiseVar"] or self.settings["saltPepperNoiseProb"]:
            picArray = np.asarray(pic)
            if self.settings["gasussNoiseMean"] or self.settings["gasussNoiseVar"]:
                picArray = self.gasussNoise(picArray, self.settings["gasussNoiseMean"], self.settings["gasussNoiseVar"])
            if self.settings["saltPepperNoiseProb"]:
                picArray = self.saltPepperNoise(picArray, self.settings["saltPepperNoiseProb"])
            pic = Image.fromarray(picArray)
        return pic

    def addLine(self, pic:Image.Image):
        lineType = 0
        if self.settings["allowUnderline"]:
            # prob 1/2
            lineType = random.randint(0, 1)
            if self.settings["allowLinebox"] and not lineType:
                # prob 1/4
                lineType = random.randint(0, 1) * 2
        if lineType:
            picDraw = ImageDraw.Draw(pic)
            if self.settings["lineColor"]:
                lineColor = tuple(random.choice(self.settings["lineColor"]))
            else:
                lineColor = tuple(255 - np.array(pic.getpixel((0,0))))
            if lineType == 1:
                y = pic.height * 0.95
                x0 = pic.width * 0.05
                x1 = pic.width * 0.95
                picDraw.line((x0, y, x1, y), lineColor)
            elif lineType == 2:
                x0 = pic.width * 0.05
                x1 = pic.width * 0.95
                y0 = pic.height * 0.05
                y1 = pic.height * 0.95
                picDraw.line((x0, y0, x1, y0), lineColor)
                picDraw.line((x1, y0, x1, y1), lineColor)
                picDraw.line((x1, y1, x0, y1), lineColor)
                picDraw.line((x0, y1, x0, y0), lineColor)
        elif lineType == 0:
            return pic
        return pic

    def addBlur(self, pic:Image.Image):
        if self.settings["GaussianBlurRadius"]:
            pic = pic.filter(ImageFilter.GaussianBlur(self.settings["GaussianBlurRadius"]))
        if self.settings["BoxBlurRadiux"]:
            pic = pic.filter(ImageFilter.BoxBlur(self.settings["BoxBlurRadiux"]))
        return pic

    def save(self, index:int, pic:Image.Image, text:str):
        picPath = "%s%d.png" % (self.settings["datasetPicsDir"], index)
        pic.save(picPath)
        self.labelFile.write("%s %s\n" % (picPath, text))  
        self.labelFile.flush()  

    def generate(self, amount:int):
        for _ in tqdm(range(amount)):
            # generate string of random length
            length, text = self.generateRandomText()
            pic = self.generateOne(text=text)
            pic = self.addLine(pic)
            pic = self.addNoise(pic)
            pic = self.addBlur(pic)
            self.save(_, pic, text)

    def saltPepperNoise(self, image:np.ndarray, prob=0):
        '''
        添加椒盐噪声
        prob:噪声比例
        '''
        output = np.zeros(image.shape,np.uint8)
        thres = 1 - prob
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                rdn = random.random()
                if rdn < prob:
                    output[i][j] = 0
                elif rdn > thres:
                    output[i][j] = 255
                else:
                    output[i][j] = image[i][j]
        return output

    def gasussNoise(self, image:np.ndarray, mean=0, var=0.001):
        '''
            添加高斯噪声
            mean : 均值
            var : 方差
        '''
        image = np.array(image/255, dtype=float)
        noise = np.random.normal(mean, var ** 0.5, image.shape)
        out = image + noise
        if out.min() < 0:
            low_clip = -1.
        else:
            low_clip = 0.
        out = np.clip(out, low_clip, 1.0)
        out = np.uint8(out*255)
        #cv.imshow("gasuss", out)
        return out

    def main(self):
        self.config()
        self.check()
        self.prepare()
        self.generate(100)


Generator().main()