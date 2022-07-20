import netCDF4
import pcraster
import os
import csv

clone_map_path = "/home/bram/Data/PCR-GLOBWB/30sec/global/cloneMaps/global_30sec_clone.map"
ldd_map_path = "/home/bram/Data/PCR-GLOBWB/30sec/global/routing/surface_water_bodies/version_2020-05-XX/lddsound_30sec_version_202005XX_correct_lat.nc"
ldd_variable_name = "Band1"
point = [6.920416, 51.051668]
tmp_dir_path = "/home/bram/Data/PCR-GLOBWB/30sec/tmp/rhine"
out_dir_path = "/home/bram/Data/PCR-GLOBWB/30sec/out/rhine"

# Create directories
if not os.path.exists(tmp_dir_path): os.mkdir(tmp_dir_path)
if not os.path.exists(out_dir_path): os.mkdir(out_dir_path)

# Set pcraster clone
pcraster.setclone(clone_map_path)

# Get LDD from netCDF and convert to pcraster map
ldd_dataset = netCDF4.Dataset(ldd_map_path, "r")
ldd_variable = ldd_dataset.variables[ldd_variable_name]
ldd = ldd_variable[:]
ldd_map = pcraster.numpy2pcr(pcraster.Scalar, ldd, ldd_variable.missing_value)
ldd_dataset.close()
ldd_map = pcraster.ldd(ldd_map)

# Get points from csv and covert to pcraster map
point_csv_path = tmp_dir_path + "/point.csv"
point_map_path = tmp_dir_path + "/point.map"
point_csv_file = open(point_csv_path, "w")
point_csv_writer = csv.writer(point_csv_file)
point_csv_writer.writerow([1, point[0], point[1]])
point_csv_file.close()
os.system("col2map -B -s, -v 1 -x 2 -y 3 " + point_csv_path + " " + point_map_path + " --clone " + clone_map_path)
point_map = pcraster.readmap(point_map_path)

# Get catchment for point and its extent
catchment_map_path = tmp_dir_path + "/catchment.map"
catchment_map = pcraster.catchment(ldd_map, point_map)
pcraster.report(catchment_map, catchment_map_path)
xcoord_map = pcraster.ifthen(catchment_map, pcraster.xcoordinate(True))
ycoord_map = pcraster.ifthen(catchment_map, pcraster.ycoordinate(True))
xcoord_max_map = pcraster.mapmaximum(xcoord_map)
ycoord_max_map = pcraster.mapmaximum(ycoord_map)
xcoord_min_map = pcraster.mapminimum(xcoord_map)
ycoord_min_map = pcraster.mapminimum(ycoord_map)
xcoord_max = pcraster.pcr2numpy(xcoord_max_map, -999999)[0,0]
ycoord_max = pcraster.pcr2numpy(ycoord_max_map, -999999)[0,0]
xcoord_min = pcraster.pcr2numpy(xcoord_min_map, -999999)[0,0]
ycoord_min = pcraster.pcr2numpy(ycoord_min_map, -999999)[0,0]

# Crop catchment to its active extent
catchment_tif_path = tmp_dir_path + "/catchment.tif"
landmask_tif_path = tmp_dir_path + "/landmask.tif"
landmask_map_out = out_dir_path + "/landmask.map"
os.system("gdal_translate " + catchment_map_path + " " + catchment_tif_path)
os.system("gdalwarp -te " + str(xcoord_min) + " " + str(ycoord_min) + " " + str(xcoord_max) + " " + str(ycoord_max) + " " + catchment_tif_path + " " + landmask_tif_path)
os.system("gdal_translate " + landmask_tif_path + " " + landmask_map_out)

# Crop clonemap to the catchment's active extent
clone_map_out = out_dir_path + "/clone.map"
pcraster.setclone(landmask_map_out)
landmask_map = pcraster.readmap(landmask_map_out)
clone_map = landmask_map | ~landmask_map
pcraster.report(clone_map, clone_map_out)

# Plot
pcraster.aguila(landmask_map)
pcraster.aguila(clone_map)
