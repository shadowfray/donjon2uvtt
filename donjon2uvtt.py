import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image
from PIL import Image, ImageOps
import base64
import json
from tkinter import filedialog as fidia
import os

black = 256
white = 0
debug_mode = False

def split_list(lst, size):
    return list(zip(*[iter(lst)] * size))

def init_cells():
    #Empty White Cell
    basic_cell = np.full((256, 256), black)

    #Secret Door
    secret_door = np.full((256, 256), black)
    secret_door[:,20:235] = np.full((256, 215), white)

    #Door
    door = np.full((256, 256), white)
    door[:, 118:138] = np.full((256,20), black)

    #Archway
    archway = door.copy()
    archway[50:206, :] = np.full((156,256), white)

    #Portcullis
    portc = door.copy()
    for i in range(1,8):
        portc[25*i+28:(25*i+16+28),:] = np.full((16,256), white)

    #Stairs
    stairs = np.full((256,256), black)
    for i in range(16):
        stairs[:, 16*i:16*i+8] = np.full((256,8), white)

    return [basic_cell, secret_door, door, archway, portc, stairs]


def get_los(bb_dungeon):
    '''Takes the baby dungeon, returns lines that are the walls'''
    los_corners = []
    real_corners = []

    #Bigger version of map for easier corner finding
    corner_map = np.repeat(np.repeat(bb_dungeon, 2, axis = 0), 2, axis = 1)

    #Find each of the corners on the map
    for i in range(corner_map.shape[0]):
        for j in range(corner_map.shape[1]):
            
            if np.sum(corner_map[i:i+2, j:j+2]) in (1,3):
                real_corners.append(((i + 1)//2, (j + 1)//2 ))


    #for each first index just pair the values in groups of 2
    v_pairings = []
    h_pairings = []
    
    for i in range(bb_dungeon.shape[0]):
        vlist = []
        
        for j in range(bb_dungeon.shape[1]):
            hlist = []
            
            for c in real_corners:
    
                if c[0] == i and c not in vlist: #Avoid multiple copies due to loop nature
                    vlist.append(c)
                    if c[0] == c[1]: #Deal with elif case of repeat digits
                        hlist.append(c)
                elif c[1] == i:
                    hlist.append(c)
                    
            if hlist not in h_pairings and len(hlist) > 0:
                h_pairings.append(hlist)
                
        if vlist not in v_pairings and len(vlist) > 0:
                v_pairings.append(vlist)


    final_list = []
    
    #Break them into pairs within each list
    for vline in v_pairings:
        for v in split_list(vline, 2):
            final_list.append(v)
    for hline in h_pairings:
        for h in split_list(hline, 2):
            final_list.append(h)
  
    return final_list


def place_door(dungeon_value, #the value of a given Donjon tile
               filter_list, #list of values that denote this object
               idx, #Tuple of (i, j) marking current position
               dungn, #the dungeon data object
               img #the image to be placed
               ):
    '''
    Returns: True if a detection was made else False,
                image to be placed,
                Bool: True if rotated
    '''

    i, j = idx
    walls = (16, 0) #Walls values, change if walls change value
    
    if type(filter_list) == int:
        filter_list = (filter_list, -100) #dummy value for later logic

    if dungn[idx] in filter_list:
        if dungn[i, j-1] in walls and dungn[i, j+1] in walls:
            return True, np.rot90(img), True
        else:
            return True, img, False

    else:
        return False, 0, False
    
        
def make_dungeon_array(dungeon):
    '''
    dungeon: the input array from a Donjon Dungeon json
    '''

    #Initialize tiles
    basic_cell, secret_door, door, archway, portc, stairs = init_cells()

    #init values for JSON
    map_size = {"x": dungeon.shape[1], "y": dungeon.shape[0]}
    format_version = 0.3
    los_corners = []
    portals = []

    #Rescale background image: Pixels are 256
    dungeon_png = np.zeros((dungeon.shape[0]*256,dungeon.shape[1]*256))
    #Baby dungeon for corners
    bb_dungeon = np.zeros(dungeon.shape)

    #Add a grid
    for i in range(dungeon.shape[0]):
        dungeon_png[256*i:256*i+2,:] = np.full((2, dungeon.shape[1] * 256), 128)
        for j in range(dungeon.shape[1]):
            dungeon_png[:, 256*j:256*j+2] = np.full((dungeon.shape[0] * 256, 2), 128)

    dp = dungeon_png.copy()

    secret_doors = [] #Note the secret doors so we can add walls later
    portals = [] #for placing doors

    
    #Make a picture of the dungeon, both high def and low rez
    for i in range(dungeon.shape[0]):
        for j in range(dungeon.shape[1]):

            #Fill in walls
            if int(dungeon[i,j]) in (16, 0):
                bb_dungeon[i, j] = 1
                dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = basic_cell

            #Fill in Secret Doors
            flg, dimg, rot = place_door(dungeon[i,j], 1048580, (i, j), dungeon, secret_door)
            if flg:
                dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = dimg
        
                if rot: #Logic to add secret doors as walls - TODO: Rotation
                    secret_doors.append([{"y": i, "x": j}, {"y": i, "x": j + 1}])
                    secret_doors.append([{"y": i + 1, "x": j}, {"y": i + 1, "x": j + 1}])
                else:
                    secret_doors.append([{"y": i, "x": j}, {"y": i + 1, "x": j}])
                    secret_doors.append([{"y": i, "x": j + 1}, {"y": i + 1, "x": j + 1}])


            #Fill in Doors - We don't distinguish door types to players
            flg, dimg, rot = place_door(dungeon[i,j],
                                        (36, 262148, 131076, 524292),
                                        (i, j),
                                        dungeon,
                                        door)
            if flg:
                dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = dimg
                door_data = {"rotation": 0, "closed": True, "freestanding": False}
                door_data['position'] = {"y": i + 0.5, "x": j + 0.5}

                if rot:
                    bounds = [{"y": i + 0.5, "x": j}, {"y": i + 0.5, "x": j + 1}]
                else:
                    bounds = [{"y": i, "x": j + 0.5}, {"y": i + 1, "x": j + 0.5}]
                door_data['bounds'] = bounds
                portals.append(door_data)


            #Fill in Portcullis
            flg, dimg, rot = place_door(dungeon[i,j],
                                        2097156,
                                        (i, j),
                                        dungeon,
                                        portc)
            if flg:
                dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = dimg
                door_data = {"rotation": 0, "closed": True, "freestanding": False}
                door_data['position'] = {"y": i + 0.5, "x": j + 0.5}

                if rot:
                    bounds = [{"y": i + 0.5, "x": j}, {"y": i + 0.5, "x": j + 1}]
                else:
                    bounds = [{"y": i, "x": j + 0.5}, {"y": i + 1, "x": j + 0.5}]
                door_data['bounds'] = bounds
                portals.append(door_data)



            #Archways
            if dungeon[i,j] == 65540:
                if dungeon[i,j-1] in (16, 0) and dungeon[i,j+1] in (16, 0):
                    dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = np.rot90(archway)
                else:
                    dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = archway

            

            #Stairs - No up/down distinguishment
            if dungeon[i,j] in (4194308, 8388612):
                if dungeon[i,j-1] in (16, 0) and dungeon[i,j+1] in (16, 0):
                    dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = np.rot90(stairs)
                else:
                    dungeon_png[256*i:256*(i+1), 256*j:256*(j+1)] = stairs

     

    if debug_mode == True:
        plt.imshow(dp, cmap = 'Greys')
        plt.show()
    
        plt.imshow(dungeon_png, cmap = 'Greys')
        plt.show()

    #Pad if uneven
    if bb_dungeon.shape[0] % 2 == 1:
        bb_dungeon = np.pad(bb_dungeon, ((0,1), (0,0)), mode = 'edge')
    if bb_dungeon.shape[1] % 2 == 1:
        bb_dungeon = np.pad(bb_dungeon, ((0,0), (0,1)), mode = 'edge')

    #get walls
    los_final = []
    los_pairs = get_los(bb_dungeon)

    #Turn wall data into wall pairs
    for end_pts in los_pairs:
        line = []
        for e in end_pts:
            line.append({"y": e[0], "x": e[1]})
        los_final.append(line)

    #Add secret doors to wall data
    for s in secret_doors:
        los_final.append(s)

    #Resolution for format
    resolution = {}
    resolution['map_origin'] = {'x':0, 'y':0}
    resolution['map_size'] = map_size
    resolution['pixels_per_grid'] = 256

    #save the image as a png in the same directory
    im = Image.fromarray(dungeon_png)
    im = im.convert('RGB')  
    im = ImageOps.invert(im)

    cwd = os.path.dirname(os.path.realpath(__file__))
    im.save(f'{cwd}\dungeon_map.png')

    with open(f'{cwd}\dungeon_map.png', "rb") as im_file:
        d_image = im_file.read()

    base64_bytes = base64.b64encode(d_image)
    base64_string = base64_bytes.decode('utf-8')

        #Save JSON format
    final = {"format" : 0.3,
             "resolution" : resolution,
             "line_of_sight" : los_final,
             "objects_line_of_sight" : [],
             "portals" : portals,
             "environment": {"baked_lighting": True, "ambient_light": "ffffffff"},
             "lights" : [],
             "image" : base64_string
             }


    return dungeon_png, final


def main(path):
    '''
    path: the path to a Donjon dungeon json file (5e?)
    '''
    cwd = os.path.dirname(os.path.realpath(__file__))

    #Read the data
    dfile = open(path)
    ddata = json.load(dfile)

    d_key = ddata['cell_bit'] #Add 4 to get real value
    
    dungeon = np.array(ddata['cells'])
    dungeon_png, final_json = make_dungeon_array(dungeon)

    with open(f'{cwd}\your_dungeon.dd2vtt', 'w', encoding = 'utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent = 4)


donjon_filename = fidia.askopenfilename()
main(donjon_filename)
