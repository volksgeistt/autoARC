import logging
import pyautogui
import time
import random
from colorama import Fore, Back, Style, init
import pyfiglet
import cv2
import numpy as np
import os
import sys
import math

init(autoreset=True)
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

author = "volksgeistt"

class AutoARC:
    def __init__(self):
        self.terminal_width = os.get_terminal_size().columns
        try:
            self.execLoadingScreen()
            self.run()
        except Exception as e:
            logging.error(f"Initialization error: {str(e)}")
            print(Fore.RED + Style.BRIGHT + self.centerText(f"Error during initialization: {str(e)}"))
            sys.exit(1)

    def centerText(self, text):
        return text.center(self.terminal_width)

    def printAndInput(self, prompt):
        print(Fore.GREEN + Style.BRIGHT + prompt, end="")
        return input(f" :: {Fore.RESET}{Style.RESET_ALL}")

    def execLoadingScreen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        title = pyfiglet.figlet_format("Auto ARC", font="slant")
        for line in title.split('\n'):
            print(Fore.CYAN + Style.BRIGHT + self.centerText(line))
            time.sleep(0.1)
        
        print(Fore.YELLOW + Style.BRIGHT + self.centerText(f"Developed by {author}"))
        print(Fore.YELLOW + Style.BRIGHT + self.centerText(f"github.com/{author}"))
        print(Fore.GREEN + Style.BRIGHT + self.centerText("Support: unrealvolksgeist@gmail.com"))
        print(Fore.GREEN + Style.BRIGHT + self.centerText("Totally Undetected & Safe..! # Happy Gaming :)"))
        print()
        
        loading_text = "Loading"
        for _ in range(3):
            for i in range(4):
                print(Fore.MAGENTA + Style.BRIGHT + self.centerText(loading_text + "." * i), end='\r')
                time.sleep(0.5)
        
        print(Fore.GREEN + Style.BRIGHT + self.centerText("Loading complete! :)"))
        time.sleep(1)

    def run(self):
        while True:
            self.displayMenu()
            self.handleChoice()

    def displayMenu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        title = pyfiglet.figlet_format("Auto ARC", font="slant")
        midTitle = '\n'.join(self.centerText(line) for line in title.split('\n'))
        print(Fore.CYAN + Style.BRIGHT + midTitle)
        print(Fore.YELLOW + Style.BRIGHT + self.centerText(f"dev @ {author}"))
        print(Fore.YELLOW + Style.BRIGHT + self.centerText(f"github.com/{author}\n"))
        print(Fore.YELLOW + Style.BRIGHT + self.centerText("CHOOSE AN OPTION"))
        print()
        
        menuList = [
            "1. AutoTyper",
            "2. Anti-AFK Movement",
            "3. Mouse Simulation",
            "4. Screen Capture && Analysis",
            "5. Timed Execution",
            "6. CustomKey Sequence",
            "7. 360 Auto Mouse Simulation",
            "0. Exit"
        ]
        
        maxLength = max(len(item) for item in menuList)
        for i in range(0, len(menuList), 2):
            itemLeft = menuList[i].ljust(maxLength)
            itemRight = menuList[i+1].ljust(maxLength) if i+1 < len(menuList) else ""
            midLine = f"{Fore.CYAN}{itemLeft}    {Fore.CYAN}{itemRight}"
            print(self.centerText(midLine))
        
        print()

    def handleChoice(self):
        try:
            choice = int(self.printAndInput("Enter your choice (0-7)"))
            if choice == 0:
                print(Fore.MAGENTA + Style.BRIGHT + self.centerText("Thank you for using Auto ARC. Goodbye!"))
                sys.exit(0)
            elif choice == 1:
                self.MsgSpammer()
            elif choice == 2:
                self.AutoMove()
            elif choice == 3:
                self.MouseMovement()
            elif choice == 4:
                self.ScreenCapture()
            elif choice == 5:
                self.TimedExecution()
            elif choice == 6:
                self.CustomKeySequence()
            elif choice == 7:
                self.AutoMouse360()
            else:
                print(Fore.RED + Style.BRIGHT + self.centerText("Invalid option. Please choose a number between 0 and 7."))
        except ValueError:
            print(Fore.RED + Style.BRIGHT + self.centerText("Invalid input. Please enter a number."))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\nTask interrupted. Restarting..."))
        finally:
            self.restartProgram()

    def restartProgram(self):
        print(Fore.YELLOW + Style.BRIGHT + self.centerText("Restarting the program..."))
        time.sleep(2)
        self.run()

    def MsgSpammer(self):
        logging.info("Starting AutoTyper task")
        w = self.printAndInput("Msg to spam")
        s = int(self.printAndInput("Msg amount to spam"))
        a = float(self.printAndInput("Msg spam time interval"))
        logging.info(f"Spam configuration: Message='{w}', Amount={s}, Interval={a}")
        print(Fore.BLUE + Style.BRIGHT + self.centerText("Config Loaded : Now Please Switch To The Main Window."))
        time.sleep(5)
        
        try:
            for x in range(s):
                logging.info(f"Typing message ({x+1}/{s})")
                pyautogui.typewrite(w)
                pyautogui.press('enter')
                time.sleep(a)
            
            logging.info("AutoTyper task completed")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("AutoTyper task completed successfully!"))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\nAutoTyper task interrupted."))
        finally:
            self.restartProgram()

    def AutoMove(self):
        logging.info("Starting Auto ARC Random Movement task")
        print(Fore.GREEN + Style.BRIGHT + self.centerText("You Can Now Switch To The Main Window."))
        time.sleep(5)
        print(Fore.GREEN + Style.BRIGHT + self.centerText("# AutoMove Started "))
        time.sleep(0.5)

        moveCount = 0
        weaponSwitchCount = 0
        
        try:
            while True:
                Movement = random.choice(['w', 's', 'a', 'd'])
                WeaponSwitch = random.choice([True, False])
                
                logging.info(f"Performing movement: {Movement}")
                pyautogui.keyDown(Movement)
                time.sleep(0.2)
                pyautogui.keyUp(Movement)
                
                moveCount += 1
                
                if WeaponSwitch:
                    weapon = random.choice(['2', '3', 'E'])
                    logging.info(f"Switching weapon: {weapon}")
                    pyautogui.press(weapon)
                    weaponSwitchCount += 1
                
                logging.info(f"Total movements: {moveCount}, Total weapon switches: {weaponSwitchCount}")
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            logging.info("Auto ARC Random Movement task interrupted by user")
            print(Fore.RED + Style.BRIGHT + self.centerText("\n>> Task Interrupted Due To Keyboard Interruption.."))
        finally:
            self.restartProgram()

    def MouseMovement(self):
        logging.info("Starting Mouse Movement Simulation")
        duration = int(self.printAndInput("Enter duration for mouse movement (in seconds)"))
        print(Fore.BLUE + Style.BRIGHT + self.centerText("Now Please Switch To The Main Window."))
        time.sleep(4)
        endTime = time.time() + duration
        try:
            while time.time() < endTime:
                x = random.randint(0, pyautogui.size().width)
                y = random.randint(0, pyautogui.size().height)
                pyautogui.moveTo(x, y, duration=1, tween=pyautogui.easeInOutQuad)
                logging.info(f"Moved mouse to ({x}, {y})")

            logging.info("Mouse Movement Simulation completed")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("Mouse Movement Simulation completed successfully!"))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\nMouse Movement Simulation interrupted."))
        finally:
            self.restartProgram()

    def ScreenCapture(self):
        logging.info("Starting Screen Capture and Analysis")
        print(Fore.BLUE + Style.BRIGHT + self.centerText("Now Please Switch To The Main Window\nScreen Will Be Captured In Next 7 Seconds."))
        time.sleep(9)
        try:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            cv2.imwrite("screenshot.png", screenshot)
            cv2.imwrite("edges.png", edges)
            
            logging.info("Screen captured and analyzed. Files saved as 'screenshot.png' and 'edges.png'")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("Screen Capture and Analysis completed successfully!"))
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + self.centerText(f"Error during Screen Capture: {str(e)}"))
        finally:
            self.restartProgram()

    def TimedExecution(self):
        logging.info("Starting Timed Execution")
        duration = int(self.printAndInput("Enter duration for timed execution (in seconds)"))
        interval = float(self.printAndInput("Enter interval between actions (in seconds)"))
        endTime = time.time() + duration
        try:
            while time.time() < endTime:
                action = random.choice([self.AutoMove])
                action()
                time.sleep(interval)
            
            logging.info("Timed Execution completed")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("Timed Execution completed successfully!"))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\nTimed Execution interrupted."))
        finally:
            self.restartProgram()

    def CustomKeySequence(self):
        logging.info("Starting Custom Key Sequence")
        sequence = self.printAndInput("Enter key sequence (e.g., 'w,a,s,d,space')").split(',')
        repetitions = int(self.printAndInput("Enter number of repetitions"))
        print(Fore.BLUE + Style.BRIGHT + self.centerText("Now Please Switch To The Main Window."))
        time.sleep(7)
        try:    
            for _ in range(repetitions):
                for key in sequence:
                    pyautogui.press(key.strip())
                    logging.info(f"Pressed key: {key.strip()}")
                    time.sleep(0.1)
            
            logging.info("Custom Key Sequence completed")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("Custom Key Sequence completed successfully!"))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\nCustom Key Sequence interrupted."))
        finally:
            self.restartProgram()
            
    def AutoMouse360(self):
        logging.info("Starting 360 Auto Mouse Simulation")
        print(Fore.GREEN + Style.BRIGHT + self.centerText("360 Auto Mouse Simulation Started"))
        
        duration = int(self.printAndInput("Enter duration for 360 mouse movement (in seconds)"))
        radius = int(self.printAndInput("Enter radius for circular movement (in pixels)"))
        print(Fore.BLUE + Style.BRIGHT + self.centerText("Now Please Switch To The Main Window."))
        time.sleep(3)        
        center_x, center_y = pyautogui.position()
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                angle = random.uniform(0, 2 * math.pi)
                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))
                
                pyautogui.moveTo(x, y, duration=0.1, tween=pyautogui.easeInOutQuad)
                logging.info(f"Moved mouse to ({x}, {y})")
                
                time.sleep(0.07) 
            logging.info("360 Auto Mouse Simulation completed")
            print(Fore.GREEN + Style.BRIGHT + self.centerText("360 Auto Mouse Simulation completed successfully!"))
        except KeyboardInterrupt:
            print(Fore.RED + Style.BRIGHT + self.centerText("\n360 Auto Mouse Simulation interrupted."))
        finally:
            self.restartProgram()

if __name__ == "__main__":
    try:
        logging.info("Starting Auto ARC script.")
        AutoARC()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        print(Fore.RED + "Fatal error occurred. Check logs for details.")
    finally:
        logging.info("Auto ARC script completed.")
