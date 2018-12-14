import numpy as np
import cv2
import sys
from matchers import matchers
import time

class Stitch:
	def __init__(self, args):
		self.path = args
		fp = open(self.path, 'r')
		filenames = [each.rstrip('\r\n') for each in  fp.readlines()]
		print (filenames)
		self.images = [cv2.resize(cv2.imread(each),(1280, 720)) for each in filenames]
		self.count = len(self.images)
		self.left_list, self.right_list, self.center_im = [], [],None
		self.matcher_obj = matchers()
		self.prepare_lists()

	def prepare_lists(self):
		print ("Number of images : %d"%self.count)
		self.centerIdx = self.count/2 
		print ("Center index image : %d"%self.centerIdx)
		self.center_im = self.images[int(self.centerIdx)]
		for i in range(self.count):
			if(i<=self.centerIdx):
				self.left_list.append(self.images[i])
			else:
				self.right_list.append(self.images[i])
		print ("Image lists prepared")

	def leftshift(self):
		# self.left_list = reversed(self.left_list)
		a = self.left_list[0]
		print ("a.shape",a.shape)
		for b in self.left_list[1:]:
			H = self.matcher_obj.match(a, b, 'left')
			print ("Homography is : ", H)
			xh = np.linalg.inv(H)
			print ("Inverse Homography :", xh)
			
			ds1 = np.dot(xh, np.array([a.shape[1], a.shape[0], 1]));
			#print ("final ds1=>", ds1)
			ds = ds1/ds1[-1]
			print ("final ds=>", ds)
			f1 = np.dot(xh, np.array([0,0,1]))
			f1 = f1/f1[-1]
			#print ("xh[0][-1]", xh[0][-1])
			xh[0][-1] += abs(f1[0])
			#print ("xh[0][-1]", xh[0][-1])
			#print ("xh[1][-1]", xh[1][-1])
			xh[1][-1] += abs(f1[1])
			#print ("xh[1][-1]", xh[1][-1])
			ds = np.dot(xh, np.array([a.shape[1], a.shape[0], 1]))
			print ("ds=>", ds)
			offsety = abs(int(f1[1]))
			#print ("offsety=>", offsety)
			offsetx = abs(int(f1[0]))
			#print ("offsetx=>", offsetx)
			dsize = (int(ds[0])+offsetx, int(ds[1]) + offsety)
			print ("image dsize =>", dsize)
			tmp = cv2.warpPerspective(a, xh, dsize)
			# cv2.imshow("warped", tmp)
			# cv2.waitKey()
			tmp[offsety:b.shape[0]+offsety, offsetx:b.shape[1]+offsetx] = b
			a = tmp

		self.leftImage = tmp

		
	def rightshift(self):
		for each in self.right_list:
			self.leftImage=self.change_size(self.leftImage)
			H = self.matcher_obj.match(leftImage, each, 'right')
			print ("Homography :", H)
			txyz = np.dot(H, np.array([each.shape[1], each.shape[0], 1]))
			txyz = txyz/txyz[-1]
			dsize = (int(txyz[0])+self.leftImage.shape[1], int(txyz[1])+self.leftImage.shape[0])
			tmp = cv2.warpPerspective(each, H, dsize)
			#cv2.imshow("tp", tmp)
			cv2.waitKey()
			# tmp[:self.leftImage.shape[0], :self.leftImage.shape[1]]=self.leftImage
			tmp = self.mix_and_match(self.leftImage, tmp)
			print ("tmp shape",tmp.shape)
			print ("self.leftimage shape=", self.leftImage.shape)
			self.leftImage = tmp
		# self.showImage('left')



	def change_size(self, leftImage):
		y, x = leftImage.shape[:2]
		edges_x=[]
		edges_y=[]
		for i in range(x):
			for j in range(y):
				if np.array_equal(leftImage[j,i],np.array([0,0,0])):
					# print("横坐标",i)
					# print("纵坐标",j)
					edges_x.append(i)
					edges_y.append(j)
					#print (1)
					left=min(edges_x)               #左边界
					right=max(edges_x)              #右边界
					width=right-left                #宽度
					bottom=min(edges_y)             #底部
					top=max(edges_y)                #顶部
					height=top-bottom               #高度
					pre1_picture=image[left:left+width,bottom:bottom+height]
					leftImage=pre1_picture
		return leftImage
			

		

	def mix_and_match(self, leftImage, warpedImage):
		i1y, i1x = leftImage.shape[:2]
		#print ("final ds=>", leftImage.shape[:2])
		i2y, i2x = warpedImage.shape[:2]
		#print ("final ds=>", warpedImage.shape[:2])
		print (leftImage[-1,-1])

		t = time.time()
		black_l = np.where(leftImage == np.array([0,0,0]))
		#print ("black_l",black_l)
		black_wi = np.where(warpedImage == np.array([0,0,0]))
		#print ("black_wi",black_wi)
		print (time.time() - t)
		print (black_l[-1])
		
		

		for i in range(0, i1x):
			for j in range(0, i1y):
				try:
					if(np.array_equal(leftImage[j,i],np.array([0,0,0])) and  np.array_equal(warpedImage[j,i],np.array([0,0,0]))):
						# print "BLACK"
						# instead of just putting it with black, 
						# take average of all nearby values and avg it.
						warpedImage[j,i] = [0, 0, 0]
					else:
						if(np.array_equal(warpedImage[j,i],[0,0,0])):
							# print "PIXEL"
							warpedImage[j,i] = leftImage[j,i]
						else:
							if not np.array_equal(leftImage[j,i], [0,0,0]):
								bw, gw, rw = warpedImage[j,i]
								bl,gl,rl = leftImage[j,i]
								# b = (bl+bw)/2
								# g = (gl+gw)/2
								# r = (rl+rw)/2
								warpedImage[j, i] = [bl,gl,rl]
				except:
					pass
		# cv2.imshow("waRPED mix", warpedImage)
		# cv2.waitKey()
		return warpedImage




	def trim_left(self):
		pass

	def showImage(self, string=None):
		if string == 'left':
			cv2.imshow("left image", self.leftImage)
			# cv2.imshow("left image", cv2.resize(self.leftImage, (400,400)))
		elif string == "right":
			cv2.imshow("right Image", self.rightImage)
		cv2.waitKey()


if __name__ == '__main__':
	try:
		args = sys.argv[1]
	except:
		args = "txtlists/ice+1.txt"
	finally:
		print ("Parameters : ", args)
	s = Stitch(args)
	s.leftshift()
	# s.showImage('left')
	s.rightshift()
	print ("done")
	cv2.imwrite("ice+1.jpg", s.leftImage)
	print ("image written")
	cv2.destroyAllWindows()
	
