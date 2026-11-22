import os
from pathlib import Path
from aiogram import Bot
from aiogram .types import PhotoSize
async def download_photo (bot :Bot ,photo :PhotoSize ,download_dir :str ="photos")->str :
    Path (download_dir ).mkdir (parents =True ,exist_ok =True )
    file =await bot .get_file (photo .file_id )
    file_path =os .path .join (download_dir ,f"{photo .file_id }.jpg")
    await bot .download_file (file .file_path ,file_path )
    return file_path
def format_duration (minutes :int )->str :
    if minutes <60 :
        return f"{minutes } мин"
    hours =minutes //60
    mins =minutes %60
    if mins ==0 :
        return f"{hours } ч"
    return f"{hours } ч {mins } мин"
def format_distance (km :float )->str :
    if km <1 :
        return f"{int (km *1000 )} м"
    return f"{km :.1f} км"