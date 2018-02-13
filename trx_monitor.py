#!/usr/bin/python
'''
Created on 22 January 2018

@author: Gregory Fenton, M6LWY

@note: The program uses the FT847 class to query the transceiver and to print
	   its state.
	   Serial port name is defined by SERIAL_PORT constant.
	   Number of queries per second is defined by SAMPLES_PER_SEC constant.
'''

from ft847 import FT847
import time, atexit

# Constants
SERIAL_PORT = "COM6"
SAMPLES_PER_SEC = 4

box_TL = '/'
box_TR = '\\'
box_BL = '\\'
box_BR = '/'
box_T  = '='
box_B  = '='
box_L  = '|'
box_R  = '|'
box_LE = '¦'
box_RE = '¦'
box_TE = 'v'
box_BE = '^'
box_IH = '-'
box_IV = '|'
box_IC = '+'
box_fill = ' '

top = 1
left = 1
width = 60
height = 10

def drawbox(top, left, bottom, right):
	print ("\33[%d;%dH" % (top, left), end = '', flush = True)
	print ("%c%s%c" % (box_TL, box_T * (right - left - 1), box_TR), end = '', flush = True)
	for i in range(top + 1, bottom):
		print ("\33[%d;%dH" % (i, left), end = '', flush = True)
		print ("%c%s%c" % (box_L, box_fill * (right - left - 1), box_R), end = '', flush = True)
	print ("\33[%d;%dH" % (bottom, left), end = '', flush = True)
	print ("%c%s%c" % (box_BL, box_B * (right - left - 1), box_BR), end = '', flush = True)

def gotoxy(x, y):
	print ("\33[%d;%dH" % (y, x), end = '', flush = True)

def clrscr():
	print ("\33[2J", end = '', flush = True)

def restoreCursor():
	print("\033[?25h");

if __name__ == '__main__':
	atexit.register(restoreCursor)
	clrscr()
	print("\033[?25l")
	drawbox(1, 1, height, width)
	print ("\33[1;2H=====FT-847====Gregory Fenton====M6LWY====labby.co.uk=====", end = '', flush = True)

	ft847 = False
	while True:
		try:
			if ft847 == False:
				ft847 = FT847(SERIAL_PORT)
			delay = 1.0 / SAMPLES_PER_SEC
			#ft847.gb3ts()
			oldstr = {}
			while True:
				ft847.read_frequency()
				ft847.read_rx_status()
				if ft847.errormessage != "":
					print ("\33[2;9H", end = '', flush = True)
					print ("%-80s" % ft847.errormessage, end = '', flush = True)
					ft847.errormessage = ""
				newstr = ft847.arraystr()
				if oldstr != newstr:
					print ("\33[4;4H", end = '', flush = True)
					oldstr = newstr
					for i in range(0, len(oldstr)):
						try:
							#freq2, self._mode, sql_str, ctc_str, dsc_str, s_meter_str, self._wavelength, self._bandplan
							if i == 0: #freq2
								print("\33[%d;%dH\33[46m%11s\33[0m" % (top + 2, left + 4, oldstr[i]), end = '', flush = True)
							elif i == 1: #self._mode
								print("\33[%d;%dH%27s" % (top + 3, left + 4, oldstr[i]), end = '', flush = True)
							elif i == 2: #sql_str
								print("\33[%d;%dH%-3s" % (top + 1, width - 13 - 18, oldstr[i]), end = '', flush = True)
							elif i == 3: #ctc_str
								print("\33[%d;%dH%-9s" % (top + 1, width - 13 - 10, oldstr[i]), end = '', flush = True)
							elif i == 4: #dsc_str
								print("\33[%d;%dH%-13s" % (top + 1, width - 13, oldstr[i]), end = '', flush = True)
							elif i == 5: #s_meter_str
								print("\33[%d;%dH%-3s" % (top + 6, left + 1, oldstr[i]), end = '', flush = True)
							elif i == 6: #s_meter_str line 2
								print("\33[%d;%dH%-3s" % (top + 5, left + 1, oldstr[i]), end = '', flush = True)
							elif i == 7: #self._wavelength
								print("\33[%d;%dH%20s" % (top + 2, width - 20, oldstr[i].strip()), end = '', flush = True)
							elif i == 8:  #self._bandplan
								b = ""
								if(oldstr[i].strip().lower() == "out of band"):
									b += "\33[41m"
								b += oldstr[i].strip().center(width - 2)
								if(oldstr[i].strip().lower() == "out of band"):
									b += "\33[0m"
								print("\33[%d;%dH%58s" % (top + 8, left + 1, b), end = '', flush = True)
							elif i == 9: #Frequency information
								s = "%58s" % oldstr[i].strip().center(width - 2)
								if len(s) > 58:
									s = s[0:58]
								print("\33[%d;%dH%58s" % (top + 4, left + 1, s), end = '', flush = True)
							elif i == 10: #Bandwidth
								print("\33[%d;%dH%6sHz bandwidth" % (top + 3, width - 18, oldstr[i].strip()), end = '', flush = True)
						except e:
							pass
						finally:
							pass
				else:
					time.sleep(delay)
				#print(ft847)
				time.sleep(delay)
		except KeyboardInterrupt:
		#	# KeyboardInterrupt exception is thrown when CTRL-C or CTRL-Break is pressed. 
			break
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			tb = traceback.extract_tb(exc_tb)[-1]
			errormessage = "%s [%s] [%s]" % (exc_type, tb[2], tb[1])
			pass
		finally:
			print ("\33[8;2H", end = '', flush = True)
			print("See you later. 73 de M6LWY", end = '', flush = True)
			print ("\33[9;2H", end = '', flush = True)
			print("  -... -.-- .\n\n", end = '', flush = True)

