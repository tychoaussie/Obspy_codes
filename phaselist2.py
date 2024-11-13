__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20230418"
__license__ = "MIT"


import os,csv
import sys
from obspy.geodetics.base import gps2dist_azimuth as gps2dist
from obspy.clients.iris import Client
import numpy as np
from obspy import UTCDateTime
from obspy.taup import TauPyModel

#20230419 Add depth reporting to include not only depth in kilometers but also R (radius of planet)
#         Clean up formatting of the arrival text output
#20181205 edition adds station awareness to the code for our local stations. Just add the station name
# in upper case and omit the station lattitude and longitude. 

class phaselist(object):
    '''Phaselist is a program for listing out the phases and predicted arrival times between a 
       published event origin time, hypocenter and station location.
       Right now, we have to explicitly type in the station location coordinates but
       in future versions, I want to pull them from a station location file like what is found
       within the c:/EVENTCAT/locations directory.


       Syntax: phaselist ORIGIN_TIME STLAT STLON EVLAT EVLON EVDEPTH 
       where,
            ORIGINTIME is of the format: yyyy-mm-ddTHH:MM:SS (note the letter T)
            STLAT,EVLAT is of format dd.00000 where dd is positive for positive latittudes 
            STLON,EVLON is of format ddd.0000 where ddd is positive for longitudes to the east
            of zero degrees longitude
            EVDEPTH is listed in kilometers. Positive values point down into the earth.

       

       Typical useage:
       C:\Anaconca\sigscript> phaselist 2015-11-30T09:49:13 42.74695 -84.39015 36.737 -98.006 5.00
 

    '''

                 # Function getoptions:
                 # Retrieve any command line options and populate the initial conditions. 
                 # If initial conditions are not met, or fail in any way, prompt the user
                 # to fill in the initial conditions.
                 # Return the option list to the program, consisting of the origin time,
                 # station coordinates, event coordinates, and event depth. 

  
def getparams():         # Enter the parameters
    print ("Either no command line options were entered, or one of them was incorrect.")
    OT = raw_input('Enter origin time in format yyyy-mm-ddTHH:MM:SS > ') 
    stlat = float(raw_input('Enter the station latitude. > '))
    stlon = float(raw_input('Enter the station longitude. > '))
    evlat = float(raw_input('Enter the event latitude. > '))
    evlon = float(raw_input('Enter the event longitude. > '))
    depth = float(raw_input('Enter the event depth. > '))                 
    return (OT,stlat,stlon,evlat,evlon,depth)


def getoptions():
    stlat = False
    station = [["NHBP",42.097477,-85.266003], \
               ["LNSM" ,42.731480,-84.47680], \
               ["NE8K" ,42.807600,-84.42195], \
               ["MOOU" ,42.577000,-84.43860], \
               ["WKZ13",44.9972,55.4495]]
    if len(sys.argv) ==7:
        try:
            OT = sys.argv[1]
            stlat = float(sys.argv[2])
            stlon = float(sys.argv[3])
            evlat = float(sys.argv[4])
            evlon = float(sys.argv[5])
            depth = float(sys.argv[6])
        except:
            OT,stlat,stlon,evlat,evlon,depth = getparams()
    elif len(sys.argv) == 6:
        OT = sys.argv[1]
        try:
            for st in station:
                if st[0] in sys.argv[2]:
                    stlat = st[1]
                    stlon = st[2]
            if stlat:
                evlat = float(sys.argv[3])
                evlon = float(sys.argv[4])
                depth = float(sys.argv[5])
            else:
                OT,stlat,stlon,evlat,evlon,depth = getparams()
        except:
            OT,stlat,stlon,evlat,evlon,depth = getparams()

    return(OT,stlat,stlon,evlat,evlon,depth)

def getdistance(stlat,stlon,evlat,evlon):
    result = []
    x = gps2dist(stlat,stlon,evlat,evlon)
    result.append(x[0]/111250.0) # distance in arc degrees
    result.append(x[1]) # azimuth
    result.append(x[2]) # backazimuth
    return result
    
def getradialdepth(Kmdepth):
    # average radius of planet = 6371
    radialdepth = Kmdepth/6371.
    return(radialdepth)
#                                                    Function Load:
#                                 General purpose loading function that brings in the first line as
#                                 a header list, and the remaining dataset as a secondary list
#
def load(infile):                                    
    with open(infile,'r') as fin:
        list = csv.reader(fin)
        rowcnt=0
        stack = []
        header = []
        data = []
        for row in list:           # Bring in the data and create a list of lists, each of which                                  
            stack.append(row)
        h1 = []
        h2 = []
        for i in range(0,len(stack)):
            if i < 3:
                header.append(stack[i])
            else:
                #print stack[i]
                if (len(stack[i][1])):
                    h1.append(float(stack[i][1]))
                if (len(stack[i][2])):              
                    h2.append(float(stack[i][2]))
    return (header,h1,h2)

def main():
                                      #           MAIN PROGRAM BODY

    OT,stlat,stlon,evlat,evlon,depth = getoptions()
    print(f'Station coordinates (A): {stlat},{stlon}')
    print(f'Event coordinates (B): {evlat},{evlon}')
    print(f'Event depth = {depth} Km ({getradialdepth(depth):4.2f} r)')
    origin_time = UTCDateTime(str(OT))
#    result = client.distaz(stalat=stlat, stalon=stlon, evtlat=evlat,evtlon=evlon)
    result = getdistance(stlat,stlon,evlat,evlon)
    model_used = 'ak135' #(model choices: "iasp91","ak135","ak135f", "prem", "jb","herrin","sp6" see: https://docs.obspy.org/packages/obspy.taup.html)

    model = TauPyModel(model=model_used) 
    arrivals = model.get_travel_times(source_depth_in_km=depth,distance_in_degree=float(result[0]) ,\
                                     phase_list = ['P','Pdiff','pPdiff','S','PP','PS','SS','SP','PPP','PPS','PSS','SSS','SSP','SPP','PcP','ScS','ScP', \
                                                    'PKP','PKS','SKS','SKP','PKKP','PKKS','SKKS','SKKP','SKKKS','PcPPKP','PcSPKP','ScSP','ScsPKP','ScPPKP', \
                                                    'PKPPcP','PKPPcS','PKPScS','PKPPKP','PKPPKS','PKPSKP', 'PKSPKP','SKPPKP','SKSP','PKPPKPPKP', \
                                                    'PKiKP','pP','Pn','Pg','Sn','Sg'])
    print ("Distance = {0:.1f} arc degrees.".format(result[0]))
    print ("{0:.0f} Km distance.".format(result[0]*111.25))
    print ("{0:.0f} deg Azimuth to event.".format(result[1])) # coordinates A to B (azimuth)
    print ("{0:.0f} degrees back Azimuth from event towards station.".format(result[2])) # coordinates B to A (backazimuth)
#    table = Client.traveltime(evloc=(evlat,evlon),staloc=[(stlat,stlon)],evdepth=depth)
#    print ("Selected phase list:\n")
#    print (table.decode())

                   #   Print the phases, travel time and forecasted arrival time.
    phasename = []
    phasetime = []
    arrivaltime = []
    print ("For origin time {}, ".format(origin_time))
    print(f'Phase arrival times are based on the {model_used} earth model.')
    print ("TauP big list of phases and arrival times:")
    for i in range(0,len(arrivals)):
        phasename.append(arrivals[i].name)
        phasetime.append(arrivals[i].time)
        at = origin_time+(arrivals[i].time)
        arrivaltime.append(at)
        arrtimemins = int(arrivals[i].time/60)
        arrtimesecs = arrivals[i].time - arrtimemins*60
        print ('Phase: {0:10} arrives in {1:7.2f} sec. ({2:2} min,{3:4.1f} sec) at time {4:02.0f}:{5:02.0f}:{6:02.0f}.{7:02.0f}' \
              .format(arrivals[i].name,arrivals[i].time,arrtimemins,arrtimesecs,at.hour,at.minute,at.second,at.microsecond/10000))
    arrivalpaths = model.get_ray_paths(source_depth_in_km=depth,distance_in_degree=result[0], \
                                        phase_list = ['P','Pdiff','Pn','Pg','PmP','PcP','PP','PKiKP','S','Sn','Sg','SmS','SS','ScS'])
#    arrivalpaths.plot_rays()

 

#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
 