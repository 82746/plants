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


class PlantApp():
    def __init__(self):
        self.__db_filename = "plant.db"
        self.__plant_db = PlantDatabase(self.__db_filename)
        self.__changes_list = []

    def print_instructions(self):
        print("\033[32m\033[2m[c]\033[22;39m Create plant")
        print("\033[32m\033[2m[d]\033[22;39m Delete plant")
        print("\033[32m\033[2m[ls]\033[22;39m List plants")
        print("\033[34m\033[2m[w]\033[22;39m Water plant")
        print("\033[34m\033[2m[u]\033[22;39m Unwater plant")
        print("\033[34m\033[2m[lw]\033[22;39m List last times watered")
        print("\033[35m\033[2m[save]\033[22;39m Save unsaved changes")
        print("\033[35m\033[2m[reset]\033[22;39m Delete unsaved changes")
        print("\033[35m\033[2m[q]\033[22;39m Quit")

    def list_plants(self):
            plant_names = self.__plant_db.get_all_plant_names()
            for p in plant_names:
                print("  · " + p)
            print()

    def __plant_avg_watering_interval(self, all_waterings:list):
            # calculate average interval between all waterings
            interval_sum = 0
            prev_date = datetime.now().date()
            for w in all_waterings:
                delta = prev_date - datetime.fromisoformat(w).date()
                interval_sum += delta.days
            avg_interval = round(interval_sum / len (all_waterings), 2)
            return avg_interval

    def list_last_times_watered(self):
            plants = self.__plant_db.get_all_plant_names()

            for p_name in plants:
                all_waterings = self.__plant_db.get_all_waterings(p_name)
                if len(all_waterings) > 0:
                    last_watering_date_str = all_waterings[0]
                    last_watering_date = datetime.fromisoformat(last_watering_date_str).date()

                    avg_interval = self.__plant_avg_watering_interval(all_waterings)

                    curr_date = datetime.now().date()
                    delta = curr_date - last_watering_date
                    delta = delta.days

                    print(f"  · {p_name}: \033[4;34m{last_watering_date.strftime('%d.%m.%y')}\033[24;2m {delta} days ago (avg every {avg_interval} days)\033[22;39m")
                else:
                    print(f"  · {p_name}: \033[4;34m None \033[24;2m None \033[22;39m")
            print()


    def list_change_buffer(self):
        if len(self.__changes_list) == 0:
            return
        print("Unsaved changes:")
        print('\n'.join(self.__changes_list))

    def run(self):
        try:
            self.__run()
        except KeyboardInterrupt:
            self.__plant_db.quit()

    def __run(self):
        while True:
            self.list_change_buffer()
            self.print_instructions()
            command = input("> ")

            if command == "c":
                print("Create plant\n")

                print("Input blank to cancel")
                p_name = input("Plant name: ").strip()
                if p_name == "":
                    print("Cancelled.")

                elif self.__plant_db.create_plant(p_name):
                    print("plant created.")
                    self.__changes_list.append(f'create "{p_name}"')

                print()

            elif command == "w":
                self.list_last_times_watered()
                print("Input blank to cancel")
                p_name = input("Plant name: ")
                if p_name == "":
                    print("Cancelled.")
                    print()
                    continue
    
                date = datetime.now().date()
                print(date)
                do_mod = input("Modify date? (y/n): ")
                if do_mod == "y":
                    print("To leave a value unchanged, input blank.")
                    year = input("Year: ").strip()
                    month = input("Month: ").strip()
                    day = input("Day: ").strip()
                    try:
                        if year == "":
                            year = date.year
                        if month == "":
                            month = date.month
                        if day == "":
                            day = date.day

                        date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")

                    except:
                        print("invalid date.")
                        continue

                if self.__plant_db.water_plant(p_name, date.isoformat()):
                    print(f'Watering {p_name}, {date}')
                    proceed = input("Proceed? (y/n): ")
                    if proceed == "y":
                        print(f'Plant watered {date}.')
                        self.__changes_list.append(f'water "{p_name}"')
                    else:
                        print("Cancelled.")
                print()


            elif command == "lw":
                self.list_last_times_watered()

            elif command == "ls":
                self.list_plants()

            elif command == "u":
                self.list_last_times_watered()
                print("Input blank to cancel")
                p_name = input("Plant name: ").strip()
                if p_name == "":
                    print("Cancelled.")
                elif self.__plant_db.undo_watering(p_name):
                    print("Watering undone.")
                    self.__changes_list.append(f'unwater "{p_name}"')
                else:
                    print("Cancelling.")

                print()

            elif command == "d":
                self.list_plants()
                print("Input blank to cancel")
                p_name = input("Plant name: ").strip()
                if p_name == "":
                    print("Cancelled.")
                elif self.__plant_db.delete_plant(p_name):
                    print("plant deleted.")
                    self.__changes_list.append(f'delete "{p_name}"')
                else:
                    print("Cancelling.")
                print()

            elif command == "q":
                if len(self.__changes_list) != 0:
                    self.list_change_buffer()
                    save = input("Discard unsaved changes? (yes/no):")
                    if save == "yes":
                        self.__plant_db.undo_changes()

                self.__plant_db.quit()
                break
            
            elif command == "reset":
                self.__plant_db.undo_changes()
                self.__changes_list.clear()
                print()

            elif command == "save":
                self.__plant_db.save_changes()
                print()


if __name__ == "__main__":
    app = PlantApp()
    app.run()
