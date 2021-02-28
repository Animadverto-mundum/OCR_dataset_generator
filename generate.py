from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tqdm import tqdm
import json
import random
import os
import cv2


class Generator:
    def __init__(self):
        self.configPath = "cfg.json"
    
    def config(self):
        if not os.path.isfile(self.configPath):
            raise FileNotFoundError("Cofigure file NOT found")
        self.settings = json.load(open(self.configPath, 'r'))

    def check(self):
        if os.listdir(self.settings["datasetPicsDir"]):
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
            self.save(_, pic, text)

    def main(self):
        self.config()
        self.check()
        self.prepare()
        self.generate(10)


Generator().main()