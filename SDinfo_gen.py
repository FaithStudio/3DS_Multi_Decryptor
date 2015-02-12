import sys
import os
import struct
import hashlib
from binascii import hexlify


def roundUp(numToRound, multiple):  #From http://stackoverflow.com/a/3407254
	if (multiple == 0):
		return numToRound

	remainder = abs(numToRound) % multiple
	if (remainder == 0):
		return numToRound
	if (numToRound < 0):
		return -(abs(numToRound) - remainder)
	return numToRound + multiple - remainder


####Part of this code from https://stackoverflow.com/questions/120656/directory-listing-in-python
def parsedir(foldername, ctrlist):
	savedpath = os.getcwd()
	try:
		os.chdir('./' + foldername)
	except Exception as ex:
		return

	hastitlelist = False
	if len(sys.argv) > 2:
		titles = sys.argv[2:]
		hastitlelist = True

	for dirname, dirnames, filenames in os.walk('.'):
		for filename in filenames:
			if 'quota.dat' in filename.lower():
				continue

			#Only Generate titles requested
			if hastitlelist:
				shouldexit = True
				for title in titles:
					upper = title.lower()[:8]
					lower = title.lower()[8:]
					if dirname.startswith("./" + upper + "/" + lower):
						shouldexit = False
				if shouldexit:
					continue

			fsizeMB = roundUp(os.stat(os.path.join(dirname, filename)).st_size, 1024*1024) / (1024*1024)

			fname = '/' + foldername + os.path.join(dirname, filename)[1:].replace('\\','/')
			wfname = fname.encode('utf-16le') + '\x00\x00'

			digest = hashlib.sha256(wfname).digest()
			x = struct.unpack("<LLLLLLLL", digest)
			ctr = struct.pack("<LLLL", x[0] ^ x[4], x[1] ^ x[5], x[2] ^ x[6], x[3] ^ x[7])

			wfname = 'sdmc:/'.encode('utf-16le') + wfname[2:-2].replace('/','.') + '.xorpad'.encode('utf-16le') + '\x00\x00'
			if len(wfname) > 180:
				print "Filename too long. This shouldn't happen."
				print '%s' % fname
				raise SystemExit(0)
			ctrlist.append([ctr, wfname, fsizeMB, fname])
	os.chdir(savedpath)



if len(sys.argv) < 2:
	print 'usage: SDinfo_gen.py folderpath'
	print 'folderpath: folder on your SD that contains "dbs", "title", etc.'
	print 'For example, SDinfo_gen.py "X:/Nintendo 3DS/xxxxxxxxx/xxxxxxxx/"'
	raise SystemExit(0)

savedpath = os.getcwd()
try:
	os.chdir(sys.argv[1])
except Exception as ex:
	print str(ex)
	raise SystemExit(0)

ctrlist = []

parsedir('dbs', ctrlist)
parsedir('extdata', ctrlist)
parsedir('title', ctrlist)
#parsedir('backups', ctrlist) #I don't have anything to test this with

os.chdir(savedpath)

if not ctrlist == []:
	fh = open('SDinfo.bin','wb')
	listlen = len(ctrlist)
	fh.write(struct.pack('<L', listlen)) #Number of entries
	for x in ctrlist:
		fh.write(x[0]) #Counter
		fh.write(struct.pack('<L', x[2])) #File size in Megabytes(rounded up)
		fh.write(x[1]) #Output filename in utf16
		if len(x[1]) < 180:
			fh.write('\x00'*(180-len(x[1]))) #Pad filename out to 180 bytes
	print 'SDinfo.bin generated.'
else:
	print "Couldn't find any content. Wrong folder?"
