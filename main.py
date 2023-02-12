#!/bin/env python3

from datetime import *
from plantdb import PlantDatabase

class PlantApp():
    def __init__(self):
        self.__db_filename = "plant.db"
        self.__plant_db = PlantDatabase(self.__db_filename)
        self.__changes_list = []

    def print_instructions(self):
        print("\033[32m" + "[c] " + "\033[22;39m" + "Create plant")
        print("\033[32m" + "[d] " + "\033[22;39m" + "Delete plant")
        print("\033[32m" + "[ls] " + "\033[22;39m" + "List plants")
        print("\033[34m" + "[w] " + "\033[22;39m" + "Water plant")
        print("\033[34m" + "[u] " + "\033[22;39m" + "Unwater plant")
        print("\033[34m" + "[lw] " + "\033[22;39m" + "List last times watered")
        print("\033[35m" + "[save] " + "\033[22;39m" + "Save unsaved changes")
        print("\033[35m" + "[reset] " + "\033[22;39m" + "Delete unsaved changes")
        print("\033[35m" + "[q] " + "\033[22;39m" + "Quit")

    def list_plants(self):
            plant_names = self.__plant_db.get_all_plant_names()
            for p in plant_names:
                print("  · " + p)
            print()

    def __plant_avg_watering_interval(self, all_waterings:list):
            # calculate average interval between all waterings
            waterings = all_waterings.copy()
            interval_sum = 0
            prev_date = datetime.fromisoformat(waterings.pop(0)).date()
            for w in waterings:
                delta = prev_date - datetime.fromisoformat(w).date()
                interval_sum += delta.days
            try:
                avg_interval = round(interval_sum / len (waterings), 2)
            except ZeroDivisionError:
                avg_interval = None

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

                    print(f"  · {p_name}: \033[4;34m{last_watering_date.strftime('%d.%m.%y')}\033[24;2m, {delta} days ago ", end="")
                    print(f"(times watered: {len(all_waterings)}", end="")

                    if avg_interval != None:
                        print(f", avg every {avg_interval} days)",end="")
                    else:
                        print(")", end="")

                    print("\033[22;39m")
                else:
                    print(f"  · {p_name}: \033[4;34m None \033[24;39m")
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
