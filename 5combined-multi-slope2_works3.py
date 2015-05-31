
import arcpy
import itertools
import csv
import numpy as np
from numpy import unravel_index
from itertools import izip
from arcpy import env

env.workspace =r'S:\Synergy\Projects\2014\20140406 Office Local Government - Functional Analysis of Greater Metropolitan Sydney area\GIS\shp'
path='S:/Synergy/Projects/2014/20140406 Office Local Government - Functional Analysis of Greater Metropolitan Sydney area/GIS/shp/'
# execfile('S:/Synergy/Projects/2014/20140406 Office Local Government - Functional Analysis of Greater Metropolitan Sydney area/GIS/ArcPy/5combined-multi-slope2_works3.py')
## this is the master working file
# metro_working_file=path+"Metro_CC_LH_data.shp"

#define working files
JTW_file_working = path+"JTW.shp"
HSE_file_working = path+"House.shp"
SCO_file_working = path+"Social.shp"
SHP_file_working = path+"Shopping.shp"
CAR_file_working = path+"Car.shp"

csv_file = open(path+'Metro_CC_LH.csv', 'wb')
csv_file2 = open(path+'Metro_CC_LH_travel.csv', 'wb')
writer = csv.writer(csv_file)
writer2 = csv.writer(csv_file2)
intra_zone_list=[]
slope_list=[]

#convert car matrix first
car_header_pylist=arcpy.ListFields(CAR_file_working,"","DOUBLE")
car_header=[]
for ch in car_header_pylist:
	car_header.append(ch.name)
car_tuple = arcpy.da.FeatureClassToNumPyArray(CAR_file_working, car_header)
car_matrix=[]
for tup in car_tuple:
	car_matrix.append(list(tup))
car_matrix=np.matrix(car_matrix)

#replace all 0 values
# np.place(car_matrix, car_matrix==0, [1])################################keep the 0s, delete the 0s,

############ WHILE TRUE############## ( we use JTW as while metro working fisle has more than 1 objects)
while int(arcpy.GetCount_management(JTW_file_working).getOutput(0))>1:
	count=int(arcpy.GetCount_management(JTW_file_working).getOutput(0))
	print("count",int(arcpy.GetCount_management(JTW_file_working).getOutput(0))) # ('count', 5)

	FL={JTW_file_working:'jtw', HSE_file_working:'house', SCO_file_working:'social', SHP_file_working:'shopping'}
	# FL={JTW_file_working:'jtw', SCO_file_working:'social', SHP_file_working:'shopping'}
	# FL={JTW_file_working:'jtw'}
	intramaxes_100=[]
	K_intramaxes_100=[]

### for everything in FL
	for f in FL:
################STEP1 - create numpyArray from master working file#########################
		#step 1 get the headers
		header_object_pylist=arcpy.ListFields(f,"","DOUBLE")
		numpy_header=[]
		for h in header_object_pylist:
			numpy_header.append(h.name)
			##check print(numpy_header)

		#step2 access arcpyNumpy
		feature_to_matrix = arcpy.da.FeatureClassToNumPyArray(f, numpy_header)

################STEP2 - calculate composite score matrix by creating Ti/Oi*Dj + Tj/Oj*Di elements
		## step 3 create sum of each row --- this specifies Oi, Oj elements
		sumEach_row=[]
		for row in feature_to_matrix:
			eachrow=[]
			sumrow = sum(row)
			if sumrow == 0:
				sumrow = 1
				# return sumrow
			eachrow.append(sumrow)
			sumEach_row.append(eachrow)
		# print(sumEach_row)

		#step 4 create sum of each column --- this specifies Di, Dj elements
		sumEach_col=[]
		sumEach_col_inner=[]
		for i in range(0,len(feature_to_matrix)):
			summer=[]
			for row in feature_to_matrix:
				summer.append(row[i])
			eachCol_sum=sum(summer)
			if eachCol_sum == 0:
				eachCol_sum = 1
			sumEach_col_inner.append(eachCol_sum)
		sumEach_col.append(sumEach_col_inner)
		print("sumeach_col ",sumEach_col)

		#-- begin Kmatrix=Ti/(Oi)*(Dj) ## Lmatrix=Tj/(Oj)*(Di) --#

		#step 5 calcualte Ti/(Oi)*(Dj)  --- AY calls this the Kmatrix
		Kmatrix=[]
		for row in range(0,len(feature_to_matrix)):
			Krow=[]
			for col in range(0,len(feature_to_matrix)):
				Ti=feature_to_matrix[row][col]
				Oi=sumEach_row[row][0]
				Dj=sumEach_col[0][col]
				Krow.append(Ti/(Oi*Dj))
			Kmatrix.append(Krow)
		# print(Kmatrix)

		#step 6 calcualte Tj/(Oj)*(Di)  --- AY calls this the Lmatrix
		Lmatrix=[]
		for col in range(0,len(feature_to_matrix)):
			Lrow=[]
			for row in range(0,len(feature_to_matrix)):
				Tj=feature_to_matrix[row][col]
				Oj=sumEach_row[row][0]
				Di=sumEach_col[0][col]
				Lrow.append(Tj/(Oj*Di))
			Lmatrix.append(Lrow)
		# print(Kmatrix)

		#Final step 6 sum K matrix and L matrix
		K_intramax=np.matrix(Kmatrix)
		L_intramax=np.matrix(Lmatrix)
		intramax=K_intramax+L_intramax
		intramax_100=100*intramax/np.max(intramax) ### this is the matrix to sum
		intramaxes_100.append(intramax_100)

		##introduce K matrix
		K_intramax_100=100*K_intramax/np.max(K_intramax) ### this is the matrix to sum
		K_intramaxes_100.append(K_intramax_100)

	composite_intramax=sum(intramaxes_100)
	composite_K_intramax=sum(K_intramaxes_100)

	##deal with car-create car matrix
	# np.place(composite_K_intramax, composite_K_intramax==0, [1])################################keep the 0s, delete the 0s,

	##flatten car and k matrix	
	car_flat=car_matrix.flatten()
	K_flat=composite_K_intramax.flatten()
	K_flat_1D=np.squeeze(np.array(K_flat))
	car_flat_1D=np.squeeze(np.array(car_flat))
	##find zero values
	delete_car = [i for i, x in enumerate(car_flat_1D) if x == 0]
	delete_K = [i for i, x in enumerate(K_flat_1D) if x == 0]
	deletes=list(set(delete_car)|set(delete_K))##combine both lists without duplicates

	##delete 
	car_flat_1D=np.delete(car_flat_1D,deletes)
	K_flat_1D=np.delete(K_flat_1D,deletes)

################STEP3- while those working files and composite intramax has the same number of rows - reduce it
	while count==len(composite_intramax): 

################STEP3 - find the 2 LGAs with largest score#############################
		# (X,Y)positions of largest score are LGA X and LGA Y
		print("nap.nanmax(intramax) ", np.nanmax(intramax))
		print("composite_intramax ", np.nanmax(composite_intramax))
		position=np.unravel_index(composite_intramax.argmax(),composite_intramax.shape)
		print(position) #(0, 3)

################STEP4 - check if LGA(X) and LGA(Y) are contiguous #############################
		expression='"FID" = '+ str(position[0])+' OR '+'"FID" = '+ str(position[1])
		# pic any one of the FLs to determine contiguity
		arcpy.MakeFeatureLayer_management(FL.keys()[0],"one_layer",expression)
		# print("one layer created")
		arcpy.PolygonNeighbors_analysis("one_layer",r'C:\Users\ayam.SGSPL\Documents\ArcGIS\Default.gdb\one_table',"F2","NO_AREA_OVERLAP","NO_BOTH_SIDES") ###use this for LGA
		# arcpy.PolygonNeighbors_analysis("one_layer",r'C:\Users\ayam.SGSPL\Documents\ArcGIS\Default.gdb\one_table',"SA2_5DIG11","NO_AREA_OVERLAP","NO_BOTH_SIDES") ### use this for SA2
		is_contiguous = int(arcpy.GetCount_management(r'C:\Users\ayam.SGSPL\Documents\ArcGIS\Default.gdb\one_table').getOutput(0))
		if(is_contiguous)==1:
			print(position, "is contiguous") #((0, 3), 'is_contiguous')
		else:
			print(position, "is not contiguous")
################STEP5 - if contigous do the below #####################
		if is_contiguous==1:

			arcpy.Delete_management(r'C:\Users\ayam.SGSPL\Documents\ArcGIS\Default.gdb\one_table')
			
			#log propensity to travel based on previous successful iteration##log the last determined slope number
			lgX=np.log(car_flat_1D)
			lgY=np.log(K_flat_1D)
			slope, intercept = np.polyfit(lgX, lgY, 1)
			each_slope=[]
			each_slope.append(count)
			each_slope.append(header_object_pylist[position[0]].name)
			each_slope.append(header_object_pylist[position[1]].name)
			each_slope.append("car")
			each_slope.append(slope)
			slope_list.append(each_slope)

############## prepare car matrix for next iteration 
			
			##sum row and delete
			sum_row_car_matrix=(car_matrix[position[0]]+car_matrix[position[1]])/2
			car_matrix=np.append(car_matrix,sum_row_car_matrix,0)
			car_matrix=np.delete(car_matrix,[position[0],position[1]],0)
			##sum col and delete
			col_car_matrix=car_matrix[:,[position[0],position[1]]]
			sum_col_car_matrix=np.sum(col_car_matrix,1)/2
			car_matrix=np.append(car_matrix,sum_col_car_matrix,1)
			car_matrix=np.delete(car_matrix,[position[0],position[1]],1)
			# print(car_matrix)

############################
	
			for f in FL:
		#log number of trips that you are about to internalize
				intra_zone_values=[]
				intra_zone_values.append(count)
				intra_zone_values.append(header_object_pylist[position[0]].name)
				intra_zone_values.append(header_object_pylist[position[1]].name)
				header_object_pylist=arcpy.ListFields(f,"","DOUBLE")
				numpy_header=[]
				for h in header_object_pylist:
					numpy_header.append(h.name)
		##check print(numpy_header)

		#step2 access arcpyNumpy
				feature_to_matrix = arcpy.da.FeatureClassToNumPyArray(f, numpy_header)
				intra_zone_values.append(FL[f])
				intra_zone_values.append(feature_to_matrix[position[0]][position[1]])
				intra_zone_values.append(feature_to_matrix[position[1]][position[0]])
				intra_zone_list.append(intra_zone_values)

				print(FL[f],feature_to_matrix[position[0]][position[1]],feature_to_matrix[position[1]][position[0]])
		
		#for f in FL, dissolve append, delete rows etc
				arcpy.MakeFeatureLayer_management(f,FL[f]+"one_layer",expression)
				arcpy.CopyFeatures_management(FL[f]+"one_layer",path+FL[f]+"layer"+str(count-1)+".shp")
				one_layer_header=arcpy.ListFields(FL[f]+"one_layer")
				#create list to populate dissove statistics field
				dissolve_statistics_list=[]
				oneLayerHeader_length=len(one_layer_header)
				## statistics field for first 2 fields
				for i in range(2,4):
					dissolve_statistics_each=[]
					each_header=one_layer_header[i].name
					dissolve_statistics_each.append(each_header)
					dissolve_statistics_each.append("FIRST")
					dissolve_statistics_list.append(dissolve_statistics_each)
			    ## statistics field for the rest
				for i in range(4,oneLayerHeader_length):
					dissolve_statistics_each=[]
					each_header=one_layer_header[i].name
					dissolve_statistics_each.append(each_header)
					dissolve_statistics_each.append("SUM")
					dissolve_statistics_list.append(dissolve_statistics_each)

				
	##dissolve temporary layer
				arcpy.Dissolve_management(FL[f]+"one_layer",path+FL[f]+"feature_"+str(count-1)+".shp","",dissolve_statistics_list,"MULTI_PART")
					# print(arcpy.GetMessage(0))
					#backup the base case

					##create field at the end of table
				arcpy.AddField_management(f,"a"+str(count),"DOUBLE")
					##identify field headers to sum - use the max matrix plus 4
				sum_field1=one_layer_header[position[0]+4].name
				sum_field2=one_layer_header[position[1]+4].name
				
					#calculate field
				arcpy.CalculateField_management(f,"a"+str(count), "["+sum_field1+"]+["+sum_field2+"]")
	#-----------------append and update-------------------------#
					#append the dissolved field to master working file
				arcpy.Append_management(path+FL[f]+"feature_"+str(count-1)+".shp",f,"NO_TEST")

					## extract the last row as individual file: appended, update empty row with data from one_feature
				GetLastRow = int(arcpy.GetCount_management(f).getOutput(0))-1
				    
				arcpy.MakeFeatureLayer_management(f,"appended", '"FID"='+str(GetLastRow))
					# print(arcpy.GetMessage(0))
				    
				    #create header object for both files
				append_header=arcpy.ListFields("appended","","DOUBLE")
				oneFeature_header=arcpy.ListFields(path+FL[f]+"feature_"+str(count-1)+".shp","","DOUBLE")
				    
				    # make sure -1 from append (cos of the a1)
				append_iterator=len(append_header)-1
				oneFeature_iterator=len(oneFeature_header)
				        #create name list of both header objects
				append_name_list=[]
				oneFeat_name_list=[]

				        ##populate append list
				for a in range(0, append_iterator):
					append_name_list.append(append_header[a].name)
				        #check append_name_list    

				        ##populate onefeat list
				for q in oneFeature_header:
					oneFeat_name_list.append(q.name)
				        #check append_name_list    
				   
				cursor_append=arcpy.da.UpdateCursor("appended",append_name_list)
				cursor_feat=arcpy.da.SearchCursor(path+FL[f]+"feature_"+str(count-1)+".shp",oneFeat_name_list)
				    
				    ##simultaneously update the appended row with dissolved "one feature" data
				for i in range(0,oneFeature_iterator):
					cursor_append=arcpy.da.UpdateCursor("appended",append_name_list[i])
					cursor_feat=arcpy.da.SearchCursor(path+FL[f]+"feature_"+str(count-1)+".shp",oneFeat_name_list[i])
					for row_get,row_update in izip(cursor_feat,cursor_append):
						val=row_get[0]
						row_update[0]=val
						cursor_append.updateRow(row_update) 
						
	#---------------- append and update finish - so not worth it------#
				del cursor_append, cursor_feat, row_get, row_update

				arcpy.DeleteFeatures_management(FL[f]+"one_layer")
				arcpy.Delete_management(FL[f]+"one_layer")
				arcpy.Delete_management("appended")

				 ##delete fields from LGA(X) LGA(Y)
				arcpy.DeleteField_management(f,[sum_field1,sum_field2])
				
	#redefine the metro working file
				arcpy.CopyFeatures_management(f,path+FL[f]+str(count-2)+".shp")
				FL[f]=path+FL[f]+str(count-2)+".shp"
			
			# return something at this indentation
			#get the number of rows in any of these fs in FL
			arcpy.Delete_management("one_layer")
			count=int(arcpy.GetCount_management(FL.keys()[0]).getOutput(0))
			print("saved",count, "matrix", len(composite_intramax))

		else:
			print("else position before",composite_intramax[position])
			composite_intramax[position]=0
			print("else position after",composite_intramax[position])
			arcpy.Delete_management("one_layer")
			arcpy.Delete_management(r'C:\Users\ayam.SGSPL\Documents\ArcGIS\Default.gdb\one_table')
	
		


writer.writerows(intra_zone_list)
writer2.writerows(slope_list)
csv_file.close()
csv_file2.close()


