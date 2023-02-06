#!/bin/env python3

import sqlite3
import os 
from datetime import datetime

class PlantDatabase():
    def __init__(self, db_name:str):
        home_dir = os.getenv("HOME")
        data_dir = f"{home_dir}/.local/state/water-plants/" 
        try:
            os.mkdir(data_dir)
        except FileExistsError:
            pass

        self.__db_path = data_dir + db_name
        self.__db = sqlite3.connect(self.__db_path)
        self.__db.isolation_level = None
        self.__create_tables()

    def __create_tables(self):
        try:
            self.__db.execute("BEGIN")
            self.__db.execute("CREATE TABLE Plants (id INTEGER PRIMARY KEY, name TEXT UNIQUE, species TEXT)")
            self.__db.execute("CREATE TABLE Waterings (id INTEGER PRIMARY KEY, plant_id REFERENCE Plants, date DATE)")
            self.__db.execute("COMMIT")
        except:
            pass

    def get_plant_id(self, plant_name):
        plant_id = self.__db.execute("SELECT p.id FROM Plants p WHERE p.name = ? LIMIT 1", [plant_name]).fetchone()
        if plant_id:
            plant_id = plant_id[0]
        else:
            plant_id = None
            print(f'Plant "{plant_name}" doesn\'t exist.')

        return plant_id 

    def create_plant(self, plant_name, plant_species):
        try:
            self.__db.execute("INSERT INTO Plants (name, species) VALUES (?, ?)", [plant_name, plant_species])
        except:
            print("Could not create plant.")

    def water_plant(self, plant_name:str):
        date = datetime.now().date()
        plant_id = self.get_plant_id(plant_name)

        self.__db.execute("INSERT INTO Waterings (plant_id, date) VALUES (?, ?)", [plant_id, date])

        return date

    def undo_watering(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)

        self.__db.execute("DELETE FROM Waterings WHERE id=(SELECT MAX(w.id) FROM Waterings w)")

    def delete_plant(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)

        self.__db.execute("DELETE FROM Plants WHERE id=?", [plant_id])
        self.__db.execute("DELETE FROM Waterings WHERE plant_id=?", [plant_id])

    def get_last_time_watered(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)

        date = self.__db.execute("SELECT w.date FROM Waterings w WHERE w.plant_id = ? LIMIT 1", [plant_id]).fetchone()

        if date:
            watering_date_str = date[0]
            watering_date = datetime.strptime(watering_date_str, "%Y-%m-%d").date()
        else:
            watering_date = None

        return watering_date
    
    def get_all_waterings(self, plant_name:str):
        plant_id = self.get_plant_id(plant_name)

        dates = self.__db.execute("SELECT w.date FROM Waterings w WHERE w.plant_id = ?", [plant_id]).fetchall()

        dates = [d[0] for d in dates]
        return dates 

    def get_all_plant_names(self):
        plants = self.__db.execute("SELECT p.name FROM Plants p").fetchall()

        plants = [p[0] for p in plants]
        return plants
    
    def quit(self):
        self.__db.commit()
        self.__db.close()


class PlantApp():
    def __init__(self):
        self.__db_filename = "plant.db"
        self.__plant_db = PlantDatabase(self.__db_filename)


    def print_instructions(self):
        print("[c] Create plant")
        print("[w] Water plant")
        print("[lw] Last watering")
        print("[ls] List plants")
        print("[u] Unwater plant")
        print("[d] Delete plant")
        print("[q] Quit")

    def list_plants(self):
            plant_names = self.__plant_db.get_all_plant_names()
            print("Plants:")
            for p in plant_names:
                print("  " + p)
            print()

    def list_last_times_watered(self):
            plants = self.__plant_db.get_all_plant_names()
            print("Last times watered:")
            for p_name in plants:
                watering_date = self.__plant_db.get_last_time_watered(p_name)
                if watering_date:
                    curr_date = datetime.now().date()
                    delta = curr_date - watering_date
                    delta = delta.days

                    print(f"  {p_name}: {watering_date} ({delta} days ago)")
                else:
                    print(f"  {p_name}: None")
            print()


    def run(self):
        try:
            self.__run()
        except KeyboardInterrupt:
            self.__plant_db.quit()

    def __run(self):
        while True:
            os.system("clear")
            self.print_instructions()
            command = input("> ")
            os.system("clear")

            if command == "c":
                print("Create plant\n")

                p_name = input("Plant name: ")
                p_species = input("Plant species: ")
                self.__plant_db.create_plant(p_name, p_species)

                print("plant created.")

            elif command == "w":
                print("Water plant\n")

                self.list_last_times_watered()
                p_name = input("Plant name: ")
                date = self.__plant_db.water_plant(p_name)

                print(f'Plant watered {date}.')

            elif command == "lw":
                print("Last waterings\n")
                self.list_last_times_watered()

            elif command == "ls":
                self.list_plants()

            elif command == "u":
                print("Undo last watering\n")
                self.list_last_times_watered()
                p_name = input("Plant name: ")
                self.__plant_db.undo_watering(p_name)

                print("Watering undone.")

            elif command == "d":
                self.list_plants()
                p_name = input("Plant name: ")
                self.__plant_db.delete_plant(p_name)

                print("plant deleted.")

            elif command == "q":
                self.__plant_db.quit()
                break
            
            else:
                continue

            input("Press [enter] to continue...")
            
                

if __name__ == "__main__":
    app = PlantApp()
    app.run()
