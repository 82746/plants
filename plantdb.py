#!/bin/env python3

import sqlite3
import os 
from datetime import *

class PlantDatabase():
    def __init__(self, db_name:str):
        home_dir = os.getenv("HOME")
        data_dir = f"{home_dir}/.local/state/water-plants/" 
        try:
            os.mkdir(data_dir)
        except FileExistsError:
            pass
        except FileNotFoundError:
            print("Cannot init database at {data_dir}. (FileExistsError)")

        self.__db_path = data_dir + db_name
        self.__db = sqlite3.connect(self.__db_path)
        self.__db.isolation_level = None
        self.__create_tables()

    def __create_tables(self):
        try:
            self.__db.execute("PRAGMA foreign_keys = ON")
            self.__db.execute("BEGIN")
            self.__db.execute("CREATE TABLE Plants (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
            self.__db.execute("CREATE TABLE Waterings (id INTEGER PRIMARY KEY, plant_id REFERENCE Plants ON DELETE CASCADE, date DATE)")
            self.__db.execute("COMMIT")
        except:
            pass

    def get_plant_id(self, plant_name):
        plant_id = self.__db.execute("SELECT p.id FROM Plants p WHERE p.name = ?", [plant_name]).fetchone()
        if plant_id:
            plant_id = plant_id[0]
        else:
            plant_id = None
            print(f'Plant "{plant_name}" doesn\'t exist.')

        return plant_id 

    def create_plant(self, plant_name):
        try:
            self.__db.execute("INSERT INTO Plants (name) VALUES (?)", [plant_name])
            return True

        except:
            print("Could not create plant.")
            return None

    def water_plant(self, plant_name:str, date:str):
        """
        date in isoformat
        """
        plant_id = self.get_plant_id(plant_name)
        if plant_id == None:
            return None

        self.__db.execute("INSERT INTO Waterings (plant_id, date) VALUES (?, ?)", [plant_id, date])

        return True

    def undo_watering(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)
        if plant_id == None:
            return None

        self.__db.execute("DELETE FROM Waterings WHERE id=(SELECT MAX(w.id) FROM Waterings w WHERE w.plant_id = ?)", [plant_id])

        return True

    def delete_plant(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)
        if plant_id == None:
            return None

        self.__db.execute("DELETE FROM Plants WHERE id=?", [plant_id])
        self.__db.execute("DELETE FROM Waterings WHERE plant_id=?", [plant_id])

        return True

    def get_last_time_watered(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)
        if plant_id == None:
            return None

        date = self.__db.execute("SELECT w.date FROM Waterings w WHERE w.plant_id = ? ORDER BY date DESC LIMIT 1", [plant_id]).fetchone()[0]

        if date:
            watering_date_str = date
            #watering_date = datetime.strptime(watering_date_str, "%Y-%m-%d").date()
            watering_date = datetime.fromisoformat(watering_date_str).date()
        else:
            watering_date = None

        return watering_date
    
    def get_all_waterings(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)
        if plant_id == None:
            return None

        dates = self.__db.execute("SELECT w.date FROM Waterings w WHERE w.plant_id = ? ORDER BY date DESC", [plant_id]).fetchall()

        dates = [d[0] for d in dates]
        return dates 

    def get_all_plant_names(self):
        plants = self.__db.execute("SELECT p.name FROM Plants p").fetchall()

        plants = [p[0] for p in plants]
        return plants
    
    def quit(self):
        self.__db.commit()
        self.__db.close()

    def undo_changes(self):
        self.__db.rollback()

    def save_change(self):
        self.__db.commit()
