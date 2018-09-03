### IMPORT YOUR PACKAGES HERE ###

import requests
import json
import re
import copy
from PIL import Image
from io import BytesIO

#################################
from bs4 import BeautifulSoup
from pythonosc import osc_message_builder
from pythonosc import udp_client
#################################


def get_tags():
    data = {}
    with open('tags.json', 'r') as myfile:
        data = json.load(myfile)

    return data

def create_json():
    data = {}
    # TEMPLATE.json
    with open('TEMPLATE.json', 'r') as myfile:
        data = json.load(myfile)

    return data

def send_to_listener(message, addr='/', ip='localhost', port=8000):
    ''' This builds and sends your message over osc '''
    msgbuilder = osc_message_builder.OscMessageBuilder(address=addr)
    msgbuilder.add_arg(message)
    msg = msgbuilder.build()
    client = udp_client.SimpleUDPClient(ip, port)
    client.send(msg)


def make_soup(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def find_all_images(soup):
    imgs = soup.find_all('img')
    img_srcs = []
    for img in imgs:
        src = (img.get('src',None))

        # and src.find('.svg') == -1 and src.find('.tif') == -1
        if src :
            img_obj = {}
            title = (img.get('title',None))
            img_obj['title'] = title

            print(src)
            if src.find('https:') == -1:
                src = 'https:'+src

            img_obj['src'] = src
            img_srcs.append(img_obj)
    return img_srcs
    
def find_all_paragraphs(soup):
    paragraphs = soup.find_all('p')
    clean_paragraphs = []
    # all_text = ''
    for p in paragraphs:
        # if p.get('class') is not None:
            # if 'wp-caption-text' not in p.get('class'):
        clean_paragraphs.append(p.getText())

        # all_text += text

    return clean_paragraphs

def get_title(soup):
    return soup.title.getText()

def get_description(soup):
    desc = soup.find('description')
    return desc

### YOUR CODE GOES HERE ###

def main():
    web_url = 'https://en.wikipedia.org/wiki/Willow_pattern'
    response = requests.get(web_url)
    s = make_soup(response)
    image_objs = find_all_images(s)

    count = 0
    data = {}
    sample_frame = {}
    sample_history = {}

    trunc_title = re.sub(r'[\W+|\s]','',get_title(s))
    trunc_title = trunc_title[:25]

    tag_template = get_tags()
    all_tags = []

    # split out JSON template into the different types
    data = create_json()
    sample_frame = data["frames"][0]
    data["frames"].clear()
    sample_history = sample_frame["history"][0]
    sample_frame["history"].clear()

    # set general data for collection of frames
    data['frame-collection'] = get_title(s)
    data['description'] = get_description(s)
    data['citation'] = web_url

    # Add a text frame for body of text on web page


    paragraphs = find_all_paragraphs(s)

    print(paragraphs)

    for p in paragraphs:
        tags = []
        text_frame = copy.deepcopy(sample_frame)

        text_frame['frame-type'] = 'text'
        text_frame['title'] = get_title(s)
        text_frame['description'] = get_description(s)
        text_frame['citation'] = web_url

        # Add the text as a history element for the openframeworks read
        text_history = copy.deepcopy(sample_history)

        text_history['speculation-scale'] = 'fact'
        text_history['text'] = p
        text_history['citation'] = web_url


        p = p.lower()

        print(p)

        # Expand to check occurrence of words etc and use regex
        for tag in tag_template['tags']:
            tag = tag.lower()
            if p.find(tag) != -1:
                tags.append(tag)
                if tag not in all_tags:
                    all_tags.append(tag)


        text_frame['tags'] = tags

        text_frame['history'].append(text_history)
        
        # Add frame to frames list
        data['frames'].append(text_frame)


 

 
    # get all images and their titles to add to frames and save images
    for img in image_objs:
        
        try:
            image_response = requests.get(img['src'])
            byte_image = BytesIO(image_response.content)
            print(image_response)
            img = Image.open(byte_image)

            try:
                filename = trunc_title+'_'+str(count)+'.jpg'
                img.save(filename)

                img_frame = copy.deepcopy(sample_frame)

                img_frame['frame-type'] = 'image'
                img_frame['title'] = get_title(s)
                img_frame['description'] = get_description(s)
                img_frame['citation'] = web_url
                img_frame['file-name'] = filename
                img_frame['tags'] = all_tags

                data['frames'].append(img_frame)

                count += 1
                
            except:
                print('Image save failed!')
                pass
            
        except:
            print('Image rquest failed!')
            pass





    # print(data)

    # pretty = json.dumps(data, sort_keys=False, indent=4)
    with open(trunc_title+'.json', 'w') as f:
        json.dump(data, f)

    return
##########################
##########################
if __name__ == '__main__':
    main()
