# Weather (and time) app for Waveshare 1.3 inch LCD screen Pico W

from lcd_driver import LCD
from machine import Pin,PWM
import framebuf, utime, os
import network, ntptime, urequests
import time, math
from secrets import secrets

BL = 13  # Pins used for display screen
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

# Connect to Wi-Fi (replace with your credentials)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets["ssid"], secrets["pw"])

while not wlan.isconnected():
    pass  # Wait for connection

print("Connected to Wi-Fi")

ntptime.host = secrets["ntptimehost"]

is_dst = False

def updateTime():
    global is_dst
    try:
        # Sync time with NTP server
        ntptime.settime()
    except:
        print(f"NTP Time connnecting with {ntptime.host} is not working.")
    
    try:
        url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={secrets['timedb_key']}&format=json&by=zone&zone=Europe/London"
        response = urequests.get(url)
        timezone_data = response.json()
        response.close()

        # Extract DST status
        is_dst = timezone_data.get("dst", False)
    except:
        print("Unable to communicate with api.timezonedb.com.")
    

updateTime()
# Get current time
current_time = time.localtime()

def displayWeather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={secrets["weather_key"]}&units=metric"
    response = urequests.get(url)
    weather_data = response.json()

    temperature = weather_data.get("main", {}).get("temp", "N/A")
    wind_speed = weather_data.get("wind", {}).get("speed", "N/A")
    weather_description = weather_data.get("weather", [{}])[0].get("description", "N/A")
    
    LCD.write_text(f"City: {city}", 20, 45, 1, colour(0,255,255))
    LCD.write_text(f"Temp: {temperature} Degrees C", 20, 55, 1, colour(0,255,255))
    LCD.write_text(f"Wind speed: {wind_speed} m/s", 20, 65, 1, colour(0,255,255))
    LCD.write_text(f"Weather: {weather_description}", 20, 75, 1, colour(0,255,255))
    response.close()
    

def colour(R,G,B):
    # Get RED value
    rp = int(R*31/255) # range 0 to 31
    if rp < 0: rp = 0
    r = rp *8
    # Get Green value - more complicated!
    gp = int(G*63/255) # range 0 - 63
    if gp < 0: gp = 0
    g = 0
    if gp & 1:  g = g + 8192
    if gp & 2:  g = g + 16384
    if gp & 4:  g = g + 32768
    if gp & 8:  g = g + 1
    if gp & 16: g = g + 2
    if gp & 32: g = g + 4
    #Get BLUE value       
    bp =int(B*31/255) # range 0 - 31
    if bp < 0: bp = 0
    b = bp *256
    colour = r+g+b
    return colour
    
def ring(cx,cy,r,cc):   # Draws a circle - with centre (x,y), radius, colour 
    for angle in range(91):  # 0 to 90 degrees in 2s
        y3=int(r*math.sin(math.radians(angle)))
        x3=int(r*math.cos(math.radians(angle)))
        LCD.pixel(cx-x3,cy+y3,cc)  # 4 quadrants
        LCD.pixel(cx-x3,cy-y3,cc)
        LCD.pixel(cx+x3,cy+y3,cc)
        LCD.pixel(cx+x3,cy-y3,cc)
  
pwm = PWM(Pin(BL))
pwm.freq(1000)
pwm.duty_u16(32768)

# Background colour - dark grey
LCD.fill(colour(40,40,40))
LCD.show()

# Define pins for buttons and Joystick
keyA = Pin(15,Pin.IN,Pin.PULL_UP) # Normally 1 but 0 if pressed
keyB = Pin(17,Pin.IN,Pin.PULL_UP)
keyX = Pin(19,Pin.IN,Pin.PULL_UP)
keyY= Pin(21,Pin.IN,Pin.PULL_UP)

up = Pin(2,Pin.IN,Pin.PULL_UP)
down = Pin(18,Pin.IN,Pin.PULL_UP)
left = Pin(16,Pin.IN,Pin.PULL_UP)
right = Pin(20,Pin.IN,Pin.PULL_UP)
ctrl = Pin(3,Pin.IN,Pin.PULL_UP)

def drawBasics():
    LCD.rect(0,0,240,240,LCD.red)
    LCD.pixel(1,1,LCD.white)     # LT
    LCD.pixel(0,239,LCD.white)   # LB
    LCD.pixel(239,0,LCD.white)   # RT
    LCD.pixel(239,239,LCD.white) # RB
    LCD.write_text("Weather and Time app", 20, 10, 1, colour(0,0,255))
    LCD.write_text(f"Hold A for city {secrets["city2"]}.", 20, 180, 1, colour(255, 0, 255))
    LCD.write_text(f"Hold B for city {secrets["city3"]}.", 20, 190, 1, colour(255, 0, 255))
    LCD.write_text("Press A & Y to quit.", 20, 220, 1, colour(255,0,0))

running = True

while(running):
    displayWeather(secrets["city1"])
    drawBasics()
    
    try: updateTime()
    except: pass
    LCD.write_text(f"Time {time.localtime()[3]+(1 if is_dst else 0)} : {time.localtime()[4]} : {time.localtime()[5]}", 20, 25, 1, colour(0,255,255))
    
    if keyA.value() == 0:
        LCD.fill_rect(20,45,200,40,colour(40,40,40))
        displayWeather(secrets["city2"])
    
    elif keyB.value() == 0:
        LCD.fill_rect(20,45,200,40,colour(40,40,40))
        displayWeather(secrets["city3"])
    
    if (keyA.value() == 0) and (keyY.value() == 0): # Halt looping?
        running = False
    
    utime.sleep(.1)
    
    LCD.show()
    LCD.fill(colour(40,40,40))
    
# Finish
LCD.fill(0)
for r in range(10):
    ring(120,120,60+r,colour(255,255,0))
LCD.write_text("Closing", 65, 115, 2, colour(255,0,0))
LCD.show()
# Tidy up
utime.sleep(3)
LCD.fill(0)
LCD.show()
