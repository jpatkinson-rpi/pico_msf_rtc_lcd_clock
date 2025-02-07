
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
#-------------------------------------------------------------------

Download HD44780 LCD I2C driver lcd_api.py & pico_i2c_lcd.py from
https://github.com/T-622/RPI-PICO-I2C-LCD

Upload lcd_api.py & pico_i2c_lcd.py & main.py to RPi PICO

Connect MSF receiver module signal output to PICO GPIO15

LCD I2C connects to PICO GPIO0 (SDA) and GPIO1 (SCK)

# BOOT SEQUENCE
1: wait for initial Minute Marker
![Alt text](https://github.com/jpatkinson-rpi/pico_msf_rtc_lcd_clock/images/prototype-wait.jpg "Wait for sync")

2: receive MSF data and decode for minute period
![Alt text](https://github.com/jpatkinson-rpi/pico_msf_rtc_lcd_clock/images/prototype-receive.jpg "Receiving MSF data")

3: Decoded MSF data and displaying Date/Time
![Alt text](https://github.com/jpatkinson-rpi/pico_msf_rtc_lcd_clock/images/prototype-time.jpg "Date/Time decoded")

