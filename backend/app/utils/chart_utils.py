import random
import numpy as np
import colorsys

def generate_purple_colors(n):
    
    base_colors = ["#4a148c", "#6a1b9a", "#7b1fa2", "#8e24aa", 
        "#9c27b0", "#ab47bc", "#ba68c8", "#ce93d8",
        "#e1bee7", "#f3e5f5", "#311b92", "#512da8"]
    if n<=len(base_colors):
        return base_colors
    colors=base_colors.copy()
    needed=n-len(base_colors)
    for i in range(n):
        hue=0.75+(i/needed)*0.1
        saturation=random.uniform(0.6,0.9)
        value=random.uniform(0.7,1.0)
        rgb=colorsys.hsv_to_rgb(hue,saturation,value)
        hex_color='#{:02x}{:02x}{:02x}'.format(
            int(rgb[0]*255),
            int(rgb[1]*255),
            int(rgb[2]*255),
            
        )
        colors.append(hex_color)
    return colors

def generate_colors_palette(n,hue_start=0.0,hue_end=1.0):
    colors = []
    for i in range(n):
        hue =hue_start+(i/n)*(hue_end-hue_start)
        saturation = 0.7
        value = 0.9
        
        #HSV to RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
        colors.append(hex_color)
    
    return colors

def calculate_bins(data_points):
    if data_points < 30:
        return max(2, data_points // 5)
    elif data_points > 1000:
        return 50
    else:
        return max(2, min(int(np.sqrt(data_points)), 30))