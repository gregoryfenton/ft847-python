'''
Created on 22 January 2018

@author: Gregory Fenton M6LWY

@note: FT847 class which communicates with FT-847 using serial library,
	   queries and sets transceiver's frequency and state and generates
	   transceiver state strings for printing.
	   Base code derived from FT817.py https://github.com/4x1md
'''

import serial, sys, os, traceback, time
from bandplans_uk import bandplan

bp = bandplan()

class FT847(object):
	
	# Constants
	# Serial port settings
	SERIAL_SPEED = 57600
	SERIAL_STOPBITS = serial.STOPBITS_TWO
	SERIAL_TIMEOUT = 0.2
	
	errormessage = ""
	
	# Transceiver modes and commands
	MODES = {}
	MODES[0x00] = "Lower Sideband"
	MODES[0x01] = "Upper Sideband"
	MODES[0x02] = "Continuous Wave"
	MODES[0x03] = "Continuous Wave LSB"
	MODES[0x04] = "Amplitude Modulation"
	MODES[0x08] = "Frequency Modulation"
	MODES[0x82] = "Continuous Wave Narrow"
	MODES[0x83] = "Continuous Wave LSB Narrow"
	MODES[0x84] = "Amplitude Modulation Narrow"
	MODES[0x88] = "Frequency Modulation Narrow"
	
	CMD_CAT_ON = [0x00, 0x00, 0x00, 0x00, 0x00]
	CMD_READ_FREQ = [0x00, 0x00, 0x00, 0x00, 0x03]
	CMD_READ_RX_STATUS = [0x00, 0x00, 0x00, 0x00, 0xE7]
	CMD_GB3TS = [0x43, 0x31, 0x75, 0x00, 0x01]
	CMD_GB3NT = [0x43, 0x30, 0x00, 0x00, 0x01]
	CMD_SET_FMN = [0x88, 0x00, 0x00, 0x00, 0x07]
	CMD_SET_CTCSS = [0x2A, 0x00, 0x00, 0x00, 0x0A]
	CMD_SET_TONE = [0x1A, 0x00, 0x00, 0x00, 0x0B]
	CMD_SET_RPT_SHIFT = [0x49, 0x00, 0x00, 0x00, 0x09]
	
	def __init__(self, serial_port, serial_speed=SERIAL_SPEED, serial_stopbits=SERIAL_STOPBITS):
		self._serial = serial.Serial(serial_port, serial_speed, stopbits=serial_stopbits, timeout=FT847.SERIAL_TIMEOUT)
		self._frequency = ""
		self._frequencyint = 0
		self._mode = ""
		self._squelch = True
		self._s_meter = ""
		self._discriminator = False
		self._ctcssdcs = False
		self._bandplan = 'O'
		self._wavelength = "0 metres"
	
	#cmd = FT847.CMD_CAT_ON
	#self._serial.write(cmd)
		
	def read_frequency(self):
		'''Queries transceiver RX frequency and mode.
		The response is 5 bytes: first four store frequency and
		the fifth stores mode (AM, FM, SSB etc.)
		'''
		self._serial.reset_input_buffer()
		self._serial.reset_output_buffer()
		cmd = FT847.CMD_READ_FREQ
		self._serial.write(cmd)
		resp_bytes = [0x99, 0x99, 0x99, 0x99, 0x0]
		timeout = time.time() + 1
		while self._serial.inWaiting() == 0:
			if time.time() >= timeout:
				errormessage = "Timeout reached waiting for serial data"
				break
			time.sleep(0.05)
		resp = self._serial.read(5)
		try:
			carry = True
			#f = "F: %02x%02x" % (resp[0], resp[1])#, resp[2], resp[3], resp[4])
			#print(f)
			resp_bytes = (resp[0], resp[1], resp[2], resp[3])
			f = "%02x%02x%02x%02x" % resp_bytes
			carry = True
			g = ""
			h = 0
			for i in range(0,8):
				if f[i] == '0' and carry == True:
					g += ' '
				else:
					g += f[i]
					h *= 10
					h += int(f[i], 16)
					carry = False
			self._frequency = "%s0" % g
			self._frequencyint = h
			self._bandplan = bp.checkfrequency(h)
			self._wavelength = bp.whatband(h)
			self._mode = FT847.MODES[resp[4]]
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			tb = traceback.extract_tb(exc_tb)[-1]
			errormessage = "%s [%s] [%s]" % (exc_type, tb[2], tb[1])
			pass
		finally:
			pass
		
	def read_rx_status(self):
		'''Queries transceiver RX status.
		The response is 1 byte:
		bit 7: Squelch status: 0 - off (signal present), 1 - on (no signal)
		bit 6: CTCSS/DCS Code: 0 - code is matched, 1 - code is unmatched
		bit 5: Discriminator centering: 0 - discriminator centered, 1 - uncentered
		bit 4: Dummy data
		bit 3-0: S Meter data
		'''
		cmd = FT847.CMD_READ_RX_STATUS
		self._serial.write(cmd)
		resp_byte = 0b00010110
		resp = self._serial.read(1)
		try:
			resp_byte = ord(resp[0])
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			tb = traceback.extract_tb(exc_tb)[-1]
			errormessage = "%s [%s] [%s]" % (exc_type, tb[2], tb[1])
			try:
				resp_byte = resp[0]
			except:
				resp_byte = 0x00
				pass
			pass
		finally:
			pass
		self._squelch	   = True  if (resp_byte & 0B10000000) else False
		self._ctcssdcs	  = True if (resp_byte & 0B01000000) else False
		self._discriminator = False if (resp_byte & 0B00100000) else True
		self._s_meter = resp_byte & 0b00011111
		
	def get_s_meter_string(self, s_meter_str):
		'''Generates S-Meter string for printing. The string includes
		S value with decibels over 9 is printed and a simple 15 symbols scale.
		Examples:
		S0:	  S0+00 ...............
		S3:	  S3+00 |||............
		S9:	  S9+00 |||||||||......
		S9+20dB: S9+00 |||||||||||....
		'''
		res = ""
		try:
			s_meter = int(s_meter_str)
			#print "s_meter: %d" % s_meter
			if s_meter < 19:
				s_half = int(s_meter) - 1 if s_meter > 0 else 0
				s_half /= 2
				res = "S%02.1f   " % s_half
				res += " %s" % ("|" * s_meter)
			else:
				 res = "S9  "
				 above_nine = s_meter - 19
				 #if above_nine > 0:
				 res += "+%02d " % (5 * above_nine)
				 #else:
				 #	res += "+00"
				 res += "%s" % ("|" * 19)
				 res += "%s" % ("I" * above_nine)
			res += "%s" % ("." * (31 - s_meter))
			
			#if s_meter == 31:
			#	res += (chr(3) * 10) + chr(6)
			#elif s_meter == 0:
			#	res += (chr(4) * 10) + chr(5)
			#else:
			#	lines = s_meter
			#	dots = 31 - s_meter
			#	fullblocks = int(lines / 3)
			#	partblocks = lines % 3
			#	res += chr(3) * fullblocks
			#	if partblocks > 0:
			#		res += chr(partblocks)
			#		dots -= 2 - partblocks
			#	if dots > 0:
			#	   res += chr(4) * int(dots / 3)
			#	res += chr(5)
			return res
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			tb = traceback.extract_tb(exc_tb)[-1]
			errormessage = "%s [%s] [%s]" % (exc_type, tb[2], tb[1])
			pass
		return res

	def get_trx_state_string(self):
		'''Returns transceiver state data for printing.
		'''
		s_meter_str = self.get_s_meter_string(self._s_meter)
		sql_str = "\33[0;46mSquelch\33[0;30m" if self._squelch else "\33[0;30mSquelch\33[0m"
		dsc_str = "\33[0;46mDiscriminator\33[0m" if self._discriminator else "\33[0;30mDiscriminator\33[0m"
		ctc_str = "\33[0;46mCTCSS/DCS\33[0m" if self._ctcssdcs else "\33[0;30mCTCSS/DCS\33[0m"
		try:
			freq1 = "%09d" % int(self._frequency)
		except:
			freq1 = "999999999"
			pass
		finally:
			pass
		freq2 = "%03d.%03d.%03d" % (int(freq1[0:3]), int(freq1[3:6]), int(freq1[6:9]))
		res = "%11s\n%-27s\n%7s\n%9s\n%13s\n%14s\n          1 2 3 4 5 6 7 8 9   +20 +40 +60dB\n%20s\n%48s\n%s" % (freq2, self._mode, sql_str, ctc_str, dsc_str, s_meter_str, self._wavelength, self._bandplan, bp.signalonfrequency(freq1))
		lines = res.split('\n')
		return lines
	
	def arraystr(self):
		'''Overrides __str__() method for using FT847 class with print command.
		'''
		return self.get_trx_state_string()
	
	def gb3ts(self):
		cmd = FT847.CMD_GB3TS
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_FMN
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_CTCSS
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_RPT_SHIFT
		self._serial.write(cmd)
	
	def gb3nt(self):
		cmd = FT847.CMD_GB3NT
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_FMN
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_CTCSS
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_TONE
		self._serial.write(cmd)
		time.sleep(0.5)
		cmd = FT847.CMD_SET_RPT_SHIFT
		self._serial.write(cmd)
	
#	 def loop(self, samples_per_sec):
#		 '''Infinite loop which queries the transceiver and prints the data.
#		 Number of queries per second is passed in samples_per_sec variable.
#		 '''
#		 delay = 1.0 / samples_per_sec
#		 while True:
#			 self.read_frequency()
#			 self.read_rx_status()
#			 self.print_data()
#			 time.sleep(delay)
# 
# if __name__ == '__main__':
#	 ft847 = FT847()
#	 ft847.loop(SAMPLES_PER_SEC)

