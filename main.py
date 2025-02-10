#-------------------------------------------------------------------
# UK MSF Radio Time Signal Decoder for RPi PICO
#
# Display decoded Date & Time on HD44780 16x2 LCD 
#
# https://en.wikipedia.org/wiki/Time_from_NPL_(MSF)
#
# Data Format: http://www.npl.co.uk/upload/pdf/MSF_Time_Date_Code.pdf
#
# The MSF radio signal operates on a frequency of 60 kHz and carries the current
# UK time and date that can be received and decoded in UK.
#
# Each second contains an  'A' & 'B' bit that date & time can be decoded from every minute.
# Parity bits are included in the data
#
# For HD44780 LCD I2C driver use lcd_api.py & pico_i2c_lcd.py
# from https://github.com/T-622/RPI-PICO-I2C-LCD
#
# MSF Receiver module input GPIO15
# LCD I2C GPIO0 (SDA) & GPIO1 (SCK)
#-------------------------------------------------------------------

from machine import Pin
from machine import Timer, Pin
from time import sleep
from machine import I2C
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

import time
import array

DEBUG = 0

LCD_I2C_SDA_PIN = 0
LCD_I2C_SCK_PIN = 1
LCD_I2C_ADDR    = 0x27

LCD_NUM_ROWS = 2
LCD_NUM_COLS = 16

MSF_RX_PIN = 15

MINUTE_SECONDS = 60

SYNC_STATE_WAIT = 0
SYNC_STATE_START = 1
SYNC_STATE_OK = 2

previous_time = 0
previous_signal = 0

year = 0
month = 0
dayofmonth = 0
dayofweek = 0
hour = 0
minute = 0
seconds_count = 0
last_seconds_count = 0
minute_marker = False
wait_count = 0
last_wait_count = 0

dst = 0

seq_start = False
sync_state = SYNC_STATE_WAIT

a = array.array('i', (0 for _ in range(MINUTE_SECONDS))) # a codes
b = array.array('i', (0 for _ in range(MINUTE_SECONDS))) # b codes

bcdlist = [80, 40, 20, 10, 8, 4, 2, 1]

daysofweek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
months = [ '-', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ]
timezone = [ 'GMT', 'BST' ]

gpio_msf = Pin( MSF_RX_PIN, mode=Pin.IN )


######################################################
# check 'a' Bits 52-29 signature 01111110
######################################################
def check_signature():
    global a
    result = 0
    if DEBUG == 1:
        print( a[52], a[53], a[54], a[55], a[56], a[57], a[58], a[59])

    if a[52] == 0 and a[53] == 1 and a[54] == 1 and a[55] == 1 and a[56] == 1 and a[57] == 1 and a[58] == 1 and a[59] == 0:
        result = 1
    else:
        print( a[52], a[53], a[54], a[55], a[56], a[57], a[58], a[59])
        
    return result

######################################################
# check data parity
# Parity provides odd number of bits set to '1'
######################################################
def check_parity( start, length, parity ):
    global a
    global b
    
    sum = 0

    for x in range(start, start+length):
        sum += a[x]

    sum += b[parity]

    result = (sum % 2)
    return result


######################################################
# convert MSF data to BCD values
######################################################
def convert_bcd_value( start, len ):
    val = 0;

    digit = 8 - len;

    for x in range(start, start+len):
        val += (a[x] * bcdlist[digit])
        digit += 1

    return val


######################################################
# decode date & time using 'a' codes
######################################################
def decode_time():
    global year
    global month
    global dayofmonth
    global dayofweek
    global hour
    global minute
 
    if DEBUG == 1:
        print("decode time data")
    result = 1
    if check_signature() == 0:
        print("ERROR: check signature failed")
        result = 0
    else:
        year = 0
        if check_parity(17, 8, 54)  == 1:
            year = convert_bcd_value( 17, 8 )
            if DEBUG == 1:
                print("year=", year)
        else:
            print("ERROR: year parity failed")
            result = 0
                
        month = 0
        dayofmonth = 0
        if check_parity(25, 11, 55) == 1:
            month = convert_bcd_value( 25, 5 )
            if DEBUG == 1:
                print("month=", month)            

            dayofmonth = convert_bcd_value( 30, 6 )
            if DEBUG == 1:
                print("dayofmonth=", dayofmonth)
        else:
            print("ERROR: month parity failed")
            result = 0

        dayofweek = 0
        if check_parity(36, 3, 56) == 1:
            dayofweek = convert_bcd_value( 36, 3 )
            if DEBUG == 1:
                print("dayofweek=", dayofweek)
        else:
            print("day parity failed")
            result = 0

        hour = 0
        minute = 0
        if check_parity(39, 13, 57) == 1:
            hour = convert_bcd_value( 39, 6 )
            if DEBUG == 1:
                print("hour=", hour)
            
            minute = convert_bcd_value( 45, 7 )
            if DEBUG == 1:
                print("minute=", minute)
        else:
            print("ERROR: time parity failed")
            result = 0
    
        dst = b[58]
        if DEBUG == 1:
            print("dst bit:", dst)
        
        return result


######################################################
# process input signal sequence and covert to
# 'a' and 'b' codes 
######################################################
def process_input_change( signal, interval ):
    global seq_start
    global sync_state
    global seconds_count
    global minute_marker
    global wait_count
    global a
    global b
    
    if seq_start == True:
        #print(signal, interval)
        if signal == 0:
            # signal low
            if interval > 450 and interval < 550:
                # minute marker
                if DEBUG == True:
                    print("minute marker")
                a[0] = 0
                b[0] = 0
                seconds_count = 0
                minute_marker = True
                
            elif interval > 250 and interval < 350:
                # 300ms => a=1 b=1
                #print("11")
                a[seconds_count] = 1
                b[seconds_count] = 1
                
            elif interval > 150 and interval < 250:
                # 200ms => a=1 b=0
                #print("10")
                a[seconds_count] = 1
                b[seconds_count] = 0
                
            elif interval > 50 and interval < 150:
                # 100ms => a=0 b=0 or a=0 b=1
                #print("00")
                a[seconds_count] = 0
                b[seconds_count] = 0
 
        else:
            # signal high
            if interval > 50 and interval < 150:
                # 100ms => a=0 b=1
                #print("01")
                a[seconds_count] = 0
                a[seconds_count] = 1
            elif interval > 450:
                seconds_count += 1
                if seconds_count == MINUTE_SECONDS:
                    seconds_count = 0
                if DEBUG == 1:
                    print("T=", seconds_count)
            
    else:
        if signal == 0:
            if interval > 450:
                if DEBUG == 1:
                    print("seq start")
                seq_start = True
                a[0] = 0
                b[0] = 0
                seconds_count = 0
                if sync_state == SYNC_STATE_WAIT:
                    sync_state = SYNC_STATE_START
        else:
            if interval > 450:
                wait_count += 1
                if DEBUG == 1:
                    print("wait %d", wait_count) 


######################################################
# check MSF signal and process state change
######################################################
def check_msf_signal():
    global previous_signal
    global previous_time
    
    current_time = time.ticks_ms()
    current_signal = gpio_msf.value()

    # signal state has changed
    if current_signal == previous_signal:
        time.sleep_ms(10)
    else:
        process_input_change( current_signal, current_time - previous_time )
        previous_time = current_time
        previous_signal = current_signal


######################################################
# program loop tasks
######################################################
def main_loop():
    global seconds_count, last_seconds_count
    global year
    global month
    global dayofmonth
    global hour
    global minute
    global sync_state
    global minute_marker
    global wait_count, last_wait_count
          
    check_msf_signal()
    
    if minute_marker == True:
        if decode_time() == 1:
            if DEBUG == 1:
                print( year, months[month], dayofmonth, daysofweek[dayofweek], hour, minute, timezone[dst])
        else:
            minute += 1
            if minute == 60:
                hour += 1
                minute = 0

        # update display time
        lcd.move_to( 0, 0 )
        lcd.putstr( daysofweek[dayofweek] )
        lcd.putstr( " {:>02d} ".format(dayofmonth) )
        lcd.putstr( months[month] )
        lcd.putstr( " {:>04d} ".format( (year+2000) ) )

        lcd.move_to( 0, 1 )
        lcd.putstr( " {:>02d}:{:>02d}:00  ".format(hour, minute) )
        lcd.putstr( timezone[dst] )

        minute_marker = False
    else:
        if sync_state == SYNC_STATE_WAIT:
            if wait_count != last_wait_count:
                lcd.move_to( 0, 1 )
                lcd.putstr( "{:>8d}".format(wait_count) )
                last_wait_count = wait_count
                
        elif sync_state == SYNC_STATE_START:
            if seconds_count != last_seconds_count:     
                if DEBUG == 1:
                       print("sync started")
                lcd.clear()
                lcd.move_to( 0, 0 )
                lcd.putstr( "Receiving..." )
                lcd.move_to( 0, 1 )
                lcd.putstr( " {:>02d}:{:>02d}:{:>02d} ".format(hour, minute, seconds_count) )
                sync_state = SYNC_STATE_OK
                last_seconds_count = seconds_count
                
        elif sync_state == SYNC_STATE_OK:
            if seconds_count != last_seconds_count:
                # update seconds every second
                lcd.move_to( 7, 1 )
                lcd.putstr( "{:>02d} ".format(seconds_count) )
                last_seconds_count = seconds_count

######################################################
# main program body
######################################################
if __name__ == "__main__":
    # Initialise I2C to LCD
    i2c = I2C( 0, sda=machine.Pin(LCD_I2C_SDA_PIN), scl=machine.Pin(LCD_I2C_SCK_PIN), freq=400000 )
    lcd = I2cLcd( i2c, LCD_I2C_ADDR, LCD_NUM_ROWS, LCD_NUM_COLS )

    lcd.hide_cursor()
    lcd.backlight_on()
    lcd.putstr("===MSF Clock===")
    time.sleep(2)
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr("Wait for sync...")
    
    if DEBUG == 1:
        print("Wait for sync...")

    sync_state = SYNC_STATE_WAIT
    while True:
        main_loop()

