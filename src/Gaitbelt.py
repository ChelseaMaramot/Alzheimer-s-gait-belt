

import time
import busio
import board
import smbus
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from math import pow
from sensor_library import Orientation_Sensor
from gpiozero import LED
from gpiozero import Button

## We can now read values from the sensor by calling the appropriate method:
## Calling each method only returns a single value. To retrieve data continuosly, call the method inside an infinite loop. #while True
sensor =  Orientation_Sensor()
sensor.euler_angles()
sensor.lin_acceleration()

#Install Library files by typing "sudo pip3 install adafruit-circuitpython-bno055" at the Terminal.
class Orientation_Sensor(object):
    def euler_angles(self): # 3-axis orientation in angular degrees 
        return self.bno055.euler
    def lin_acceleration(self): # 3-axis vector of linear acceleration in m/s^2 (acceleration - gravity)
        return self.bno055.linear_acceleration



#Raspberry pi (LED):
green_led = LED(18)
red_led = LED(7)
blue_led = LED(21)

#Raspberry pi (Button):
user_button = Button(26)

##OLED 
# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height

image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# First define some constants to allow easy resizing of shapes.
padding = 2
shape_width = 20
top = padding
bottom = height-padding

# Move left to right keeping track of the current x position for drawing shapes.
x = padding

# Load default font.
font = ImageFont.load_default()
###########################

# Function displays baseline, speed, and angle values determined in each loop on the OLED
def display(baseline, v_i, euler_y):
    draw.rectangle((0,top+10,width,height), outline=0, fill=0)
    draw.text((x, top),    'Baseline',  font=font, fill=255)
    draw.text((x, top+10),str(abs(baseline)), font=font, fill=255)
    draw.text((x+80, top),    'Speed',  font=font, fill=255)
    draw.text((x+80, top+10),str(abs(round((v_i),2))), font=font, fill=255)
    draw.rectangle((0,20,width,height), outline=0, fill=0)
    draw.text((x, top+20),    'angle Value',  font=font, fill=900)
    draw.text((x+80, top+20),str(euler_y[-1]), font=font, fill=255)
    disp.image(image)
    disp.display()




## Task 1: Status
#Finding the average of the n most recent items in the list
#It appends the n most recent into average_list, n being 5 in this case
#If the number of items in the list equals 5, the average will be calculated
#This is done by taking the sum of the list values, then dividing it by the length, which is fixed at 5
#If the average is coming in a green light will turn on
def average(data): # data is the list where we put all of our sensor values
    average_list = []
    avg_sensor_value = 0

    if len(data)>=5:
        for i in range(-5,0): ## The 5 most recent items.
            average_list.append(data[i])
           
        if len(average_list) == 5:
            avg_sensor_value = sum(average_list)/len(average_list)
            avg_sensor_value =round(avg_sensor_value,2)
            green_led.on()
            
        
    else:
        print("No data")

    
    return avg_sensor_value
    
## Task 2: Speed Notification

#assuming initial velocity is zero
#Use kinematic formula Vf = Vi + at
#A new final velocity value will be produced and overwrite the old v_i variable
##This value is called v_f and returned as such, but reassigned to v_i when the actual function is called
##v_i is used to process the need for a speed notification in the next function
#The function then loops
#When acceleration is a near-zero value, we assume that we have completely stopped (v_i = 0)
def velocity(v_i, acceleration):
    time= 0.01

    if abs(acceleration) < 0.3:
        acceleration = 0
        v_i = 0
        
    v_f = v_i + acceleration * time
    
    return v_f

##Inputs baseline from the main function and the speed calcualted in the velocity function
#Determines what is 30% of the baseline annd assigns that to "percent"
#Calculates the difference between baseline and secondary
#Normal: green LED is on and blue LED is off
#Abnormal: if the difference is greater than percent, blue LED is on
def speed_notification(baseline, v_i):
    A_status= 'good'
    if abs(v_i) <= 5 and abs(v_i) > 0: ##avg is value from average(data)
        difference = abs(abs(baseline) - abs(v_i))
        percent = 0.50* abs(baseline)

        if difference > percent:
            blue_led.on()
            A_status = "bad"
             
        else:
          print("Normal results")
          A_status = 'good'
          blue_led.off()
    elif abs(v_i)> 5:
        blue_led.off()
        print('Speed out of range')
    else:
        print ("you're not moving")
        blue_led.off()
            
        A_status='good'
          

    return A_status



#Task 4: additional notification of the euler angle value
##Detects an abnormal hip angle while walking
##As hips rock, axis on y-plane of body will slant from one side to the other, prducing negative or positive angles
# If a negative angle is read, a value -1 is appended into the list counter
## similarily, if a positive angle is read, a value +1 will be appended into the list counter
##The list sum is taken once the counter has 10 values
#Normal walk: Equal amount time spent on each hip side. Therefore sum of counter is zero (Red LED off)
#Abnormal walk: Unequal amount of time spent on each hip. Therefore, sum accumulates as negative or positive (Red LED on)
##For the sake of data speed input and potential errors in readings, theres an allowance of an absolute value of the sum of 2 before the sensor is set off
## A variable E_status is defined and given a string of 'good' or 'bad', related to normal or abnormal respectively. This is returned for the escalation portion later

def euler_angle_notification(counter, euler_y):
    E_status='good'
    if len(counter) < 10:
        if euler_y[-1] < 0:
            counter.append(-1)
        elif euler_y[-1] > 0:
            counter.append(1)

    else:
        angle_difference = sum(counter)
        if abs(angle_difference) > 2 and abs(angle_difference) <= 9:
            red_led.on()
            list.clear(counter)
            E_status = 'bad'


        elif abs(angle_difference) > 9:
            E_status = "good"
            red_led.off()
            list.clear(counter)
        else:
            red_led.off()
            list.clear(counter)
            E_status = 'good'

        
    return E_status

##Task 3 Escalation
#Requires user input to acknowledge abnormal speed and angle detected
##being called only when both A_status and E_status are assigned 'bad'
#If both speed and angle are bad (RED & BLUE light ON)
##The escalation portion causes the program to stop signal to the user that theres an issue with the gait pattern
#A button needs to be pressed which is indicated by flashing red light
#When pressed red LED turns off
def escalation():
    print ("Escalating!")
    while user_button.is_pressed == True:  ## while the button is NOT PRESSED
        blue_led.off()
        red_led.on()
        time.sleep(0.5)
        red_led.off()
        time.sleep(0.5)
            
    print("Button is pressed")  ##button becomes False -> pressed
    red_led.off()

def main():
    try:
        ##These blank/initial values allow for these prexisting value sto change over time
        data = []
        euler_y = [0]
        counter = []
        counter_2 = 0
        speeds = [0]
        A_status = 'good'
        E_status= 'good'
        v_i = 0
        baseline = 0
        acceleration = 0

        ##while true loop allows for function to run indefinitely as sensor value is looped and redefined with every loop, allowing for new calculations
        while True:
            
            #Assigns the the euler angle from the sensor into a variable called "euler_angles"
            euler_angles = sensor.euler_angles()
        
            
            #If the y-euler angle is not "None", it is added into a list called "euler_y"
            if euler_angles[1] != None:
                euler_y.append(int(euler_angles[1]))


                #If the last value euler_y is not none
                #Calls the returned value from Euler notification function and overwirtes the old E_status value
                if euler_y[-1] != None:
                    E_status = euler_angle_notification(counter, euler_y)

            #Assigns linear acceleration from the sensor to lin_acceleration
            #Adds values that are not none into a list called data
            lin_acceleration = sensor.lin_acceleration()

            if lin_acceleration[2] != None:
                data.append(lin_acceleration[2])
                
                acceleration = average(data)

            #Calculates the velocity from the raw acceleration values from the sensor
                if len(data)>1:
                    v_i = velocity (v_i, lin_acceleration[2])
                    speeds.append(round(v_i,2))
                    
            #Calculates baseline with the first 10 items on the list "speeds"
            #Overwrites A_status with returned value from speed_nofication
            if len(speeds)>10:
                baseline = sum(speeds[0:10])/10
                baseline = round(baseline,2)
            
                A_status = speed_notification(baseline, v_i)

            #Activates OLED and displays baseline,angle, and speed   
            if euler_y[-1] != None:
                display(baseline, v_i, euler_y)
                
            #Calls escalation when E_staus and A_status are both "bad".
            if E_status == 'bad' and A_status == 'bad':
                counter_2 +=1
                if counter_2 == 3:
                    escalation()
                    counter_2=0

            print('\n',"Acceleration", acceleration, '\t', 'speed',v_i, '\t', "Velocity Status", A_status)
            print ('\n','angle', euler_angles[1], '\t', "Euler Status:", E_status)
            print('\n', "counter",counter)

            time.sleep(0.01)    #allows for a pause in the program before loopingthis allows for calculation of speed in the velocity function using the same value for change in time
    except OSError:
        print("Sensor Malfunction, please restart the program")
    #Stops the code when there is OS Error 
       
main()

